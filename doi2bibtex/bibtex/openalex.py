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
from doi2bibtex.util.getdoilogger import return_logger as getlogger
from colorama import Fore, Style

BASE_URL = 'https://api.openalex.org/works'

logger = getlogger(__name__)

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

async def async_get_metadata_from_dois(dois: List[str]) -> dict:
    """
    Fetch metadata including abstracts for a list of DOIs from OpenAlex.
    
    Args:
        dois: List of DOI strings (without https://doi.org/ prefix)
        
    Returns:
        Dictionary mapping DOIs to their metadata dictionaries
    """
    metadata_dict = {}
    
    async def fetch_doi_metadata(doi):
        if not doi:
            return
            
        async with throttler:
            try:
                # Fetch full work data (no select parameter means all fields)
                works = await async_get_work_by(doi, doi=True)
                
                if works and len(works) > 0:
                    work = works[0]
                    
                    # Extract relevant metadata
                    metadata = {
                        'doi': doi,
                        'title': work.get('title'),
                        'abstract': _reconstruct_abstract(work.get('abstract_inverted_index', {})),
                        'publication_date': work.get('publication_date'),
                        'publication_year': work.get('publication_year'),
                        'type': work.get('type'),
                        'language': work.get('language'),
                        'primary_location': work.get('primary_location', {}),
                        'open_access': work.get('open_access', {}),
                        'authorships': [{
                            'author_position': auth.get('author_position'),
                            'author': auth.get('author', {}),
                            'institutions': auth.get('institutions', []),
                            'raw_author_name': auth.get('raw_author_name'),
                            'raw_affiliation_strings': auth.get('raw_affiliation_strings', [])
                        } for auth in work.get('authorships', [])],
                        'cited_by_count': work.get('cited_by_count'),
                        'biblio': work.get('biblio', {}),
                        'is_retracted': work.get('is_retracted'),
                        'is_paratext': work.get('is_paratext'),
                        'concepts': work.get('concepts', []),
                        'mesh': work.get('mesh', []),
                        'keywords': work.get('keywords', []),
                        'grants': work.get('grants', []),
                        'referenced_works_count': work.get('referenced_works_count'),
                        'related_works': work.get('related_works', []),
                        'sustainable_development_goals': work.get('sustainable_development_goals', []),
                        'openalex_id': work.get('id'),
                        'openalex_url': f"https://openalex.org/{work.get('id', '').split('/')[-1]}"
                    }
                    
                    metadata_dict[doi] = metadata
                else:
                    logger.warning(f"No metadata found for DOI: {doi}")
                    metadata_dict[doi] = None
                    
            except Exception as e:
                logger.error(f"Error fetching metadata for DOI {doi}: {e}")
                metadata_dict[doi] = None
    
    # Create tasks for all DOIs
    tasks = [fetch_doi_metadata(doi) for doi in dois]
    
    # Execute all tasks concurrently
    await asyncio.gather(*tasks)
    
    return metadata_dict


def _reconstruct_abstract(inverted_index: dict) -> str:
    """
    Reconstruct abstract text from OpenAlex inverted index format.
    
    Args:
        inverted_index: Dictionary mapping words to their positions in the abstract
        
    Returns:
        Reconstructed abstract text
    """
    if not inverted_index:
        return ""
    
    # Create a list of (position, word) tuples
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    
    # Sort by position
    word_positions.sort(key=lambda x: x[0])
    
    # Join words to form the abstract
    return " ".join(word for _, word in word_positions)


# Convenience synchronous wrapper
def get_metadata_from_dois(dois: List[str]) -> dict:
    """
    Synchronous wrapper for async_get_metadata_from_dois.
    
    Args:
        dois: List of DOI strings (without https://doi.org/ prefix)
        
    Returns:
        Dictionary mapping DOIs to their metadata dictionaries
    """
    return async_get_metadata_from_dois(dois)


'''
# Async usage
dois = ["10.1038/nature12373", "10.1126/science.1259855"]
metadata = await async_get_metadata_from_dois(dois)

# Synchronous usage
metadata = get_metadata_from_dois(dois)

# Access metadata
for doi, data in metadata.items():
    if data:
        print(f"Title: {data['title']}")
        print(f"Abstract: {data['abstract']}")
        print(f"Authors: {len(data['authorships'])} authors")
'''

