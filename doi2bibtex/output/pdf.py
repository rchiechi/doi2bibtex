import re
import httpx
from pathlib import Path
import doi2bibtex.util as util
from typing import List, Optional, Union, Tuple, Dict


PDFURL = re.compile(r'//(.*\.pdf\?download=true)')

logger = util.getlogger(__name__)

async def do_pdfs(library, args):
    proxy = args.proxy
    if proxy:
        if not proxy.startswith("http://") or proxy.startswith("https://"):
            # If proxy explicitly mentions scheme, use it for both http and https for simplicity,
            # or httpx will choose based on URL. For more control, use dict.
            logger.warning(f"Assuming {proxy} is an http:// proxy.")
            proxy = f"http://{proxy}"
    baseurl = args.mirror.strip('/')
    urls = {}
    for entry in library.entries:
        doi = _finddoi(entry)
        if not doi:
            logger.warning(f"Could not resolve a doi from {entry}.")
            continue
        url = await async_get_pdf_links_from_urls(f"{baseurl}/{doi}", args.proxy)
        if url:
            urls[doi] = f"https://{url}"
    logger.debug(f"Processing {urls}")
    
    pdfurls = {}
    for doi, url in urls.items():
        if args.filename:
            pdfpath = Path(Path(args.filename).with_suffix('.pdf'))
        else:
            pdfpath = Path(Path(doi.replace('/', '_')).with_suffix('.pdf'))
        i = 0
        while pdfpath.exists():
            pdfpath = Path(Path(f"{pdfpath.name}_{i:02d}").with_suffix('.pdf'))
        pdfurls[url] = pdfpath
    downloaded_pdfs = await util.downloadPDFs(list(pdfurls.keys()), proxy)
    successful_downloads = 0
    for url, pdf_data in downloaded_pdfs.items():
        if pdf_data:
            successful_downloads += 1
            logger.info(f"Successfully downloaded {len(pdf_data)} bytes from {url}")
            pdfpath = pdfurls[url]
            try:
                with pdfpath.open("wb") as f:
                    f.write(pdf_data)
                logger.info(f"Saved PDF from {url} to {pdfpath}")
            except IOError as e:
                logger.error(f"Failed to save PDF from {url}: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while saving PDF from {url}: {e}")
        else:
            # Failure details are already logged by the download functions
            # and available via get_download_failures()
            pass # logger.warning(f"Failed to download PDF from {url}. See failure list for details.")    


async def async_get_pdf_links_from_urls(url: Union[str, bytes, None], proxy) -> str:
    if url is None:
        return ''
    if isinstance(url, bytes):
        url = str(url, encoding='utf-8')

    # Custom headers to mimic a browser; can sometimes help bypass simple bot detection
    # and ensure servers provide appropriate content.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        # "Accept": "application/pdf,application/octet-stream,*/*;q=0.8", # Prioritize PDF
        # "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    html = None
    async with httpx.AsyncClient(proxy=proxy, headers=headers, follow_redirects=True, timeout=10) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 404:
                logger.error(f"Could not resolve {url}")
            elif err.response.status_code == 429:
                logger.error(f"Rate-limit exteeded for {url}")
            else:
                logger.error(f"Error {err.response.status_code} while fetching {url}")
        except httpx.InvalidURL:
            logger.error(f"'{url}' is not a valid url")
        except httpx.ReadTimeout:
            logger.error(f"Timeout fetching {url}")
        except httpx.ConnectError as err:
            logger.error(f"Connection error fetching {url}: {err}")

    if not html:
        return ''
    
    m = re.search(PDFURL, html)
    try:
        pdfurl = m.group(1)
    except (AttributeError, IndexError):
        logger.warningg(f"No pdf link found in {url}")
        pdfurl = ''

    return pdfurl


def _finddoi(entry):
    doi = None
    for key in ('doi', 'DOI'):
        if key in entry.fields_dict:
            doi = entry.fields_dict[key].value
    if doi is None:
        _keys = list(entry.fields_dict)
        for _key in ('eprint', 'url'):
            if _key in entry.fields_dict:
                _keys = [_key] + _keys
        for _key in _keys:
            _uri = str(entry.fields_dict[_key].value)
            m = re.search(REDOIURI, _uri)
            if m is not None:
                doi = _uri[m.span(0)[1]:]
            if doi:
                break
    return doi.strip() or None