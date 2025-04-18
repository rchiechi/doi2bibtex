import urllib.request
from urllib.error import HTTPError
import http
import asyncio
import json
from typing import List
from urllib.parse import urlencode
import httpx
import random
from asyncio_throttle import Throttler
from doi2bibtex.util.getlogger import return_logger
from colorama import Fore, Style

BASE_URL = 'https://api.openalex.org/works'

logger = return_logger(__name__)

throttler = Throttler(rate_limit=10, period=1)  # 10 requests per second (OpenAlex limit)

failures = []

def get_failures():
    """Return list of failed OpenAlex fetches as (url, error_message) tuples."""
    return failures

async def async_get_work_by(id, **kwargs):
    if isinstance(id, bytes):
        id = str(id, encoding='utf-8')
    if kwargs.get('doi', False):
        id = f'doi:{id}'

    params = {}
    if kwargs.get('cites', False):
        params['filter'] = f'cites:{id}'
        params['per-page'] = 200
    else:
        id_part = f"/{id}"
    if kwargs.get('select', None) is not None:
        params['select'] = kwargs["select"]
    if kwargs.get('page', 0) > 0:
        params['page'] = kwargs["page"]

    works = []
    cursor = "*"

    async with httpx.AsyncClient() as client:
        while cursor:
            current_params = params.copy()
            current_params['cursor'] = cursor
            url = f"{BASE_URL}{id_part if not kwargs.get('cites', False) else ''}?" + urlencode(current_params)

            try:
                work = await _async_get_url(client, url)
                works.append(work)
                cursor = work.get('meta', {}).get('next_cursor')
                logger.debug(f'Getting next cursor {cursor}')
            except (httpx.HTTPError, ValueError) as e:
                logger.error(f"Error fetching {url}: {e}")
                break  # Stop fetching on error

    return works

async def _async_get_url(client, url, retries: int = 5, timeout: float = 10.0):
    """Fetch URL with retries and exponential backoff. Records failures."""
    logger.debug(f"Fetching {url}")
    backoff = 1.0
    for attempt in range(1, retries + 1):
        try:
            response = await client.get(url, follow_redirects=True, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as err:
            status = err.response.status_code
            if status == 429 or 500 <= status < 600:
                if attempt < retries:
                    sleep_time = min(backoff, 10.0) + random.random()
                    logger.warning(f"HTTP {status} fetching {url}, retry {attempt}/{retries}, retrying in {sleep_time:.1f}s")
                    await asyncio.sleep(sleep_time)
                    backoff *= 2
                    continue
                else:
                    msg = f"HTTP {status} fetching {url} after {retries} attempts"
                    logger.error(msg)
                    failures.append((url, msg))
                    return {}
            else:
                if status == 404:
                    msg = f"Could not resolve with openalex: {url} (status 404)"
                else:
                    msg = f"Error {status} while fetching {url}"
                logger.error(msg)
                failures.append((url, msg))
                return {}
        except (httpx.RequestError, httpx.ReadTimeout) as err:
            if attempt < retries:
                sleep_time = min(backoff, 10.0) + random.random()
                logger.warning(f"{err.__class__.__name__} fetching {url}: {err}, retry {attempt}/{retries}, retrying in {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
                backoff *= 2
                continue
            else:
                msg = f"{err.__class__.__name__} fetching {url} after {retries} attempts: {err}"
                logger.error(msg)
                failures.append((url, msg))
                return {}
        except json.JSONDecodeError as err:
            msg = f"Invalid JSON response from {url}: {err}"
            logger.error(msg)
            failures.append((url, msg))
            return {}
        except httpx.InvalidURL as err:
            msg = f"Invalid URL {url}: {err}"
            logger.error(msg)
            failures.append((url, msg))
            return {}


async def async_get_cited(dois: List[str]) -> List[str]:
    _dois = []

    async def process_doi(doi):
        if not doi:
            return
        async with throttler:
            works = await async_get_work_by(doi, select='referenced_works', doi=True)
        if works:
            for work in works:
                ids = work.get('referenced_works', [])
                for id in ids:
                    async with throttler:
                        _doid = await async_get_work_by(id.replace('https://openalex.org/', ''), select='doi')
                    if _doid and _doid[0].get('doi'):
                        _doi = _doid[0]['doi'].replace('https://doi.org/', '')
                        if _doi:
                            _dois.append(_doi)

    tasks = [process_doi(doi) for doi in dois]
    await asyncio.gather(*tasks)

    return dois + _dois

async def async_get_citing(dois: List[str]) -> List[str]:
    works = []
    _dois = []
    results = []
    throttler = Throttler(rate_limit=5, period=1)  # 5 requests per second (adjust as needed)

    async def fetch_doi(doi):
        if not doi:
            return
        async with throttler:
            _id = await async_get_work_by(doi, select='id', doi=True)
        if _id:
            id = _id[0].get('id', '').replace('https://openalex.org/', '')
            async with throttler:
                citing_works = await async_get_work_by(id, select='doi', cites=True)
            results.append(citing_works)

    tasks = [fetch_doi(doi) for doi in dois]
    await asyncio.gather(*tasks)

    for work_list in results:
        if work_list:
            for work in work_list:
                for result in work.get('results', []):
                    if result and result.get('doi'):
                        _doi = result['doi'].replace('https://doi.org/', '')
                        if _doi:
                            _dois.append(_doi)

    return dois + _dois

