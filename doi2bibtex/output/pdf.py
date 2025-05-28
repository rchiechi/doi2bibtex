import re
import httpx
from pathlib import Path
import doi2bibtex.util as util
from typing import List, Optional, Union, Tuple, Dict
import asyncio
import random
import logging
from tqdm.asyncio import tqdm
from contextlib import contextmanager

PDFURL = re.compile(r'//(.*\.pdf\?download=true)')

logger = util.getlogger(__name__)

@contextmanager
def _buffer_logs():
    """Temporarily buffer all 'doi2bib' logger output and flush after context."""
    root_logger = logging.getLogger('doi2bib')
    orig_handlers = root_logger.handlers[:]
    buf_records = []
    class BufferHandler(logging.Handler):
        def emit(self, record):
            buf_records.append(record)
    buf_handler = BufferHandler()
    # Replace handlers with buffer
    root_logger.handlers = [buf_handler]
    try:
        yield
    finally:
        # Flush buffered records
        for rec in buf_records:
            for h in orig_handlers:
                h.handle(rec)
        # Restore original handlers
        root_logger.handlers = orig_handlers

async def do_pdfs(library, args):
    proxy = args.proxy
    if proxy:
        if not proxy.startswith("http://") or proxy.startswith("https://"):
            # If proxy explicitly mentions scheme, use it for both http and https for simplicity,
            # or httpx will choose based on URL. For more control, use dict.
            logger.warning(f"Assuming {proxy} is an http:// proxy.")
            proxy = f"http://{proxy}"
    
    # Determine the total number of entries for tqdm, if possible
    total_entries = len(library.entries)   
    baseurl = args.mirror.strip('/')
    urls = {}
    errs = []
    with _buffer_logs():
        for entry in tqdm(library.entries, desc="Resolving pdf links", total=total_entries, unit="doi"):
        # for entry in library.entries:
            doi = _finddoi(entry)
            if not doi:
                errs.append(entry)
                continue
            url = await async_get_pdf_links_from_urls(f"{baseurl}/{doi}", args.proxy)
            if url:
                urls[doi] = f"https://{url}"
            else:
                errs.append(doi)
            await asyncio.sleep(10 + (random.random() * 0.5))
    logger.debug(f"Processing {urls}")
    if errs:
        logger.warning(f"Could not get pdf links from {errs}.")

    
    pdfurls = {}
    for doi, url in urls.items():
        if args.filename:
            pdfpath = Path(Path(args.filename).with_suffix('.pdf'))
        else:
            pdfpath = Path(doi.replace('/', '_')+'.pdf')
        i = 0
        while any([pdfpath.exists(), pdfpath in pdfurls.values()]):
            pdfpath = Path(f"{pdfpath.name}_{i:02d}"+'.pdf')
        pdfurls[url] = pdfpath
   
    downloaded_pdfs = await util.downloadPDFs(list(pdfurls.keys()), proxy)
    failed = []
    successful_downloads = 0
    for url, pdf_data in downloaded_pdfs.items():
        if pdf_data:
            successful_downloads += 1
            logger.debug(f"Successfully downloaded {len(pdf_data)} bytes from {url}")
            pdfpath = pdfurls[url]
            try:
                with pdfpath.open("wb") as f:
                    f.write(pdf_data)
                logger.info(f"Saved PDF to {pdfpath}")
            except IOError as e:
                logger.error(f"Failed to save PDF from {url}: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while saving PDF from {url}: {e}")
        else:
            # Failure details are already logged by the download functions
            # and available via get_download_failures()
            failed.append(ur)
            pass # logger.warning(f"Failed to download PDF from {url}. See failure list for details.")    
    if errs:
        logger.warning(f"Successful downloads: {successful_downloads} / {total_entries - len(errs)} Failed to resolve {len(errs)} dois.")
        logger.warning(f"Failed urls: {failed}")

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
        # logger.warning(f"No pdf link found in {url}")
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