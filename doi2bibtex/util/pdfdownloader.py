import httpx
import asyncio
import logging
import random
from typing import List, Optional, Union, Tuple, Dict
from .getlogger import return_logger as getlogger

logger = getlogger(__name__)

# Global list to store information about failed downloads
download_failures: List[Tuple[str, str]] = []

def get_download_failures() -> List[Tuple[str, str]]:
    """
    Returns a list of (url, error_message) tuples for downloads that failed.
    """
    return download_failures

async def download_pdf_from_url(
    client: httpx.AsyncClient,
    url: str,
    retries: int = 3,
    timeout: float = 45.0 # Increased timeout for potentially large PDF downloads or slow servers
) -> Union[bytes, None]:
    """
    Asynchronously downloads a PDF from a given URL.

    It follows redirects, verifies the Content-Type is 'application/pdf',
    and checks if the content starts with '%PDF-' to ensure it's a binary PDF.
    Includes retry logic with exponential backoff for transient errors.

    Args:
        client: An initialized httpx.AsyncClient instance.
        url: The URL from which to download the PDF.
        retries: The maximum number of download attempts.
        timeout: The timeout in seconds for each request.

    Returns:
        The PDF content as bytes if successful, otherwise None.
        Failures are recorded in the global `download_failures` list.
    """
    logger.debug(f"Attempting to download PDF from: {url}")
    current_backoff_delay = 5.0  # Initial backoff delay in seconds

    for attempt in range(1, retries + 1):
        try:
            response = await client.get(url, follow_redirects=True, timeout=timeout)
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses

            content_type = response.headers.get("Content-Type", "").lower()
            logger.debug(f"URL: {url}, Attempt: {attempt}, Status: {response.status_code}, Content-Type: {content_type}")

            # Check if the Content-Type indicates a PDF
            if not content_type.startswith("application/pdf"):
                msg = f"Content-Type is not application/pdf (was: {content_type})"
                logger.debug(f"Download attempt {attempt} for {url} failed: {msg}")
                # This is likely a permanent issue with the URL/server, so don't retry for this specific error.
                # If it's the last attempt, record the failure.
                if attempt == retries:
                    download_failures.append((url, msg))
                return None # Stop processing this URL

            # Basic verification: PDF files should start with '%PDF-'
            if not response.content.startswith(b"%PDF-"):
                msg = "Content does not appear to be a valid PDF (magic number '%PDF-' missing)."
                logger.debug(f"Download attempt {attempt} for {url} failed: {msg}")
                # This could be an HTML error page served with a 200 OK and a misleading PDF Content-Type.
                # Retry, as it *could* be a transient issue, though less likely.
                if attempt < retries:
                    sleep_time = min(current_backoff_delay, 15.0) + (random.random() * 0.5) # Add jitter
                    logger.debug(f"Content validation failed for {url}, attempt {attempt}/{retries}. Retrying in {sleep_time:.2f}s...")
                    await asyncio.sleep(sleep_time)
                    current_backoff_delay *= 2  # Exponential backoff
                    continue # Go to next attempt
                else:
                    download_failures.append((url, msg + f" after {retries} attempts."))
                    return None

            logger.debug(f"Successfully downloaded PDF from: {url} ({len(response.content)} bytes)")
            return response.content

        except httpx.HTTPStatusError as err:
            status_code = err.response.status_code
            error_message = f"HTTP {status_code} error: {err.response.text[:200]}" # Include some response text
            # Retry on server errors (5xx) or rate limiting (429)
            if status_code == 429 or 500 <= status_code < 600:
                if attempt < retries:
                    sleep_time = min(current_backoff_delay, 15.0) + (random.random() * 0.5)
                    logger.debug(
                        f"HTTP {status_code} for {url}, attempt {attempt}/{retries}. Retrying in {sleep_time:.2f}s. Error: {error_message}"
                    )
                    await asyncio.sleep(sleep_time)
                    current_backoff_delay *= 2
                    continue
                else:
                    full_msg = f"HTTP {status_code} fetching {url} after {retries} attempts. Final error: {error_message}"
                    logger.error(full_msg)
                    download_failures.append((url, full_msg))
                    return None
            elif status_code == 404:
                full_msg = f"PDF not found (404) at {url}. Error: {error_message}"
                logger.error(full_msg)
                download_failures.append((url, full_msg))
                return None  # No point retrying a 404
            else:  # Other client-side errors (4xx not covered above)
                full_msg = f"HTTP {status_code} error while fetching {url}. Error: {error_message}"
                logger.error(full_msg)
                download_failures.append((url, full_msg))
                return None

        except (httpx.RequestError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.PoolTimeout) as err:
            # Includes network errors, DNS issues, timeouts, etc.
            error_message = f"{err.__class__.__name__}: {str(err)}"
            if attempt < retries:
                sleep_time = min(current_backoff_delay, 15.0) + (random.random() * 0.5)
                logger.debug(
                    f"{error_message} fetching {url}, attempt {attempt}/{retries}. Retrying in {sleep_time:.2f}s"
                )
                await asyncio.sleep(sleep_time)
                current_backoff_delay *= 2
                continue
            else:
                full_msg = f"{error_message} fetching {url} after {retries} attempts."
                logger.error(full_msg)
                download_failures.append((url, full_msg))
                return None
        except Exception as e:  # Catch any other unexpected errors during the process
            error_message = f"Unexpected error downloading {url}: {e.__class__.__name__} - {str(e)}"
            logger.exception(error_message) # Log with stack trace for unexpected errors
            if attempt == retries: # Record failure only on last attempt for unexpected errors
                 download_failures.append((url, error_message + f" on attempt {attempt}."))
            # Depending on the error, might not want to retry, but for a general catch-all,
            # if it's not the last attempt, the loop will handle retry.
            if attempt < retries:
                sleep_time = min(current_backoff_delay, 15.0) + (random.random() * 0.5)
                await asyncio.sleep(sleep_time)
                current_backoff_delay *= 2
                continue
            else:
                return None


    logger.error(f"Failed to download PDF from {url} after {retries} attempts (exhausted retries).")
    # Ensure failure is recorded if all retries exhausted without specific recording above
    if not any(f[0] == url for f in download_failures):
        download_failures.append((url, f"Failed after {retries} attempts (exhausted retries)."))
    return None


async def download_pdfs(
    urls: List[str],
    proxy: Optional[str] = None,
    concurrent_downloads: int = 5,
    request_timeout: float = 45.0,
    num_retries: int = 6
) -> Dict[str, Union[bytes, None]]:
    """
    Asynchronously downloads multiple PDFs from a list of URLs.

    Uses an HTTP/S proxy if provided and limits the number of concurrent downloads.

    Args:
        urls: A list of URLs from which to download PDFs.
        proxy: Optional. The proxy string (e.g., "http://user:pass@host:port").
        concurrent_downloads: The maximum number of PDFs to download simultaneously.
        request_timeout: Timeout in seconds for each individual request.
        num_retries: Number of retries for each URL.

    Returns:
        A dictionary mapping each URL to its downloaded PDF content (as bytes)
        or None if the download failed for that URL.
    """
    download_failures.clear()  # Clear failures from any previous run
    results: Dict[str, Union[bytes, None]] = {}
    
    # Configure proxies for httpx.AsyncClient
    # Proxies can be a single string or a dictionary mapping schemes.
    # Example: proxies = "http://localhost:8888"
    # Or: proxies = {"http://": "http://localhost:8080", "https://": "http://localhost:8080"}
    # proxies_config: Union[str, Dict[str, str], None] = None
    if proxy:
        if not proxy.startswith("http://") or proxy.startswith("https://"):
             # If proxy explicitly mentions scheme, use it for both http and https for simplicity,
             # or httpx will choose based on URL. For more control, use dict.
            logger.warning(f"Assuming {proxy} is an http:// proxy.")
            proxy = f"http://{proxy}"
        # else:
        #     # Assuming a simple host:port proxy, prefix with http://
        #     # This is a basic assumption; robust proxy parsing might be needed for complex cases.
        #     logger.warning(f"Proxy string '{proxy}' does not specify a scheme, assuming 'http://{proxy}' for all protocols.")
        #     proxies_config = {"all://": f"http://{proxy}"}


    # Use an asyncio.Semaphore to limit the number of concurrent downloads
    semaphore = asyncio.Semaphore(concurrent_downloads)

    # Custom headers to mimic a browser; can sometimes help bypass simple bot detection
    # and ensure servers provide appropriate content.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        "Accept": "application/pdf,application/octet-stream,*/*;q=0.8", # Prioritize PDF
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    
    async def download_task_with_semaphore(client: httpx.AsyncClient, url_to_download: str):
        async with semaphore:
            logger.debug(f"Semaphore acquired for {url_to_download}")
            content = await download_pdf_from_url(
                client,
                url_to_download,
                retries=num_retries,
                timeout=request_timeout
            )
            logger.debug(f"Semaphore released for {url_to_download}")
            return content

    # Create a single AsyncClient session to be reused for all requests
    # This allows connection pooling and better performance.
    async with httpx.AsyncClient(proxy=proxy, headers=headers, timeout=request_timeout, follow_redirects=True) as client:
        tasks = []
        for url in urls:
            # Create a download task for each URL
            task = asyncio.create_task(download_task_with_semaphore(client, url))
            tasks.append(task)

        # Wait for all download tasks to complete
        # return_exceptions=True would return exceptions as results instead of raising them.
        # Here, exceptions are handled within download_pdf_from_url.
        downloaded_contents = await asyncio.gather(*tasks, return_exceptions=False)

        for url, content in zip(urls, downloaded_contents):
            results[url] = content
            # Ensure a failure is logged if content is None and not already in download_failures
            # This is a fallback, as download_pdf_from_url should ideally record all its failures.
            if content is None and not any(failure_url == url for failure_url, _ in download_failures):
                logger.debug(f"No specific failure recorded for {url} which returned None. Adding generic failure.")
                download_failures.append((url, "Download returned None, specific error not captured or occurred outside download_pdf_from_url."))
    
    return results

# --- Example Usage ---
async def main_example():
    """
    Example function to demonstrate the PDF downloader.
    """
    # A list of URLs to test the downloader.
    # Replace these with actual URLs for testing.
    test_urls = [

        "http://dacemirror.sci-hub.se/journal-article/d9a0327f0b4962ac4f638ad280c92a30/sumimoto2004.pdf?download=true", # Another sample PDF
        "https://arxiv.org/pdf/2303.08774",  # PDF from arXiv (usually reliable)
        "https://www.google.com",  # HTML page, not a PDF
    ]

    # Optional: Set a proxy server if you need to use one.
    # proxy_server = "http://your_proxy_host:your_proxy_port"
    # proxy_server = "http://user:password@your_proxy_host:your_proxy_port" # With auth
    proxy_server = "http://localhost:3128"

    logger.info(f"--- Starting PDF download process for {len(test_urls)} URLs ---")
    
    # Call the main download function
    downloaded_pdfs = await download_pdfs(
        urls=test_urls,
        proxy=proxy_server,
        concurrent_downloads=1, # Limit to 3 concurrent downloads for this example
        request_timeout=30.0,   # 30 seconds timeout for each request
        num_retries=3           # 2 retries per URL (total 3 attempts)
    )

    logger.info("--- PDF Download Process Complete ---")

    successful_downloads = 0
    for url, pdf_data in downloaded_pdfs.items():
        if pdf_data:
            successful_downloads += 1
            logger.info(f"Successfully downloaded {len(pdf_data)} bytes from {url}")
            # In a real application, you would save the pdf_data to a file:
            # try:
            #     file_name = url.split('/')[-1]
            #     if not file_name.lower().endswith(".pdf"):
            #         file_name = f"{file_name.split('.')[0] if '.' in file_name else file_name}.pdf"
            #     if not file_name: # Handle case of trailing slash
            #         file_name = f"downloaded_{random.randint(1000,9999)}.pdf"
            #
            #     with open(file_name, "wb") as f:
            #         f.write(pdf_data)
            #     logger.info(f"Saved PDF from {url} to {file_name}")
            # except IOError as e:
            #     logger.error(f"Failed to save PDF from {url}: {e}")
            # except Exception as e:
            #     logger.error(f"An unexpected error occurred while saving PDF from {url}: {e}")
        else:
            # Failure details are already logged by the download functions
            # and available via get_download_failures()
            pass # logger.warning(f"Failed to download PDF from {url}. See failure list for details.")


    logger.info(f"--- Download Summary ---")
    logger.info(f"Total URLs processed: {len(test_urls)}")
    logger.info(f"Successful downloads: {successful_downloads}")
    logger.info(f"Failed downloads: {len(get_download_failures())}")

    if get_download_failures():
        logger.warning("--- Detailed Failures ---")
        for i, (failed_url, error_msg) in enumerate(get_download_failures()):
            logger.warning(f"Failure {i+1}: URL: {failed_url}, Error: {error_msg}")

if __name__ == "__main__":
    # Configure a logger
    # Use a more descriptive format for logging
    # logging.basicConfig(
    #     level=logging.INFO,
    #     format="%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
    # )
    # To run this example, you can uncomment the following line:
    asyncio.run(main_example())
    # For production use, integrate into your existing asyncio event loop.
