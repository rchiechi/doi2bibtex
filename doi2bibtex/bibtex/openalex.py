import urllib.request
from urllib.error import HTTPError
import http
import asyncio
import json
from typing import List
from urllib.parse import urlencode
import httpx
from asyncio_throttle import Throttler
from doi2bibtex.util.getlogger import return_logger

BASE_URL = 'https://api.openalex.org/works'

logger = return_logger(__name__)

def get_work_by(id, **kwargs):
    if isinstance(id, bytes):
        id = str(id, encoding='utf-8')
    if kwargs.get('doi', False):
        id = f'doi:{id}'
    _q = '?'
    if kwargs.get('cites', False):
        url = f'{BASE_URL}{_q}filter=cites:{id}&per-page=200'
        _q = '&'
    else:
        url = f'{BASE_URL}/{id}'
    if kwargs.get('select', None) is not None:
        url = f'{url}{_q}select={kwargs["select"]}'
        _q = '&'
    if kwargs.get('page', 0) > 0:
        url = f'{url}{_q}page={kwargs["page"]}'
        _q = '&'
    works = [_geturl(f'{url}{_q}cursor=*')]
    while works[-1].get('meta', {'next_cursor': None})['next_cursor'] is not None:
        _next = works[-1]["meta"]["next_cursor"]
        logger.debug(f'Getting next cursor {_next}')
        works.append(_geturl(f'{url}{_q}cursor={_next}'))
    return works

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

def _geturl(url):
    work = {}
    logger.debug(f"Fetching {url}")
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as f:
            print('.', end='')
            work = json.load(f)
    except HTTPError as err:
        if err.code == 404:
            logger.error(f"Could not resolve {id} with openalex: {url}")
        else:
            logger.error(f"Error {err.code} while fetching {url}")
    except http.client.InvalidURL:
        logger.error(f"'{url}' is not a valid url")
    return work

async def _async_get_url(client, url):
    logger.debug(f"Fetching {url}")
    try:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        print('.', end='')
        return response.json()
    except httpx.HTTPStatusError as err:
        if err.response.status_code == 404:
            logger.error(f"Could not resolve with openalex: {url}")
        else:
            logger.error(f"Error {err.response.status_code} while fetching {url}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON response from {url}")
        return {}
    except httpx.InvalidURL:
        logger.error(f"'{url}' is not a valid url")
        return {}

def get_cited(dois):
    _dois = []
    for doi in dois:
        if not doi:
            continue
        works = get_work_by(doi, select='referenced_works', doi=True)
        for work in works:
            ids = work.get('referenced_works', [])
            for id in ids:
                _doi = get_work_by(id.replace('https://openalex.org/', ''), select='doi')[0].get('doi', 'https://doi.org/')
                if _doi is not None:
                    _doi = _doi.replace('https://doi.org/', '')
                if _doi:
                    _dois.append(_doi)
    return dois + _dois

async def async_get_cited(dois: List[str]) -> List[str]:
    _dois = []
    throttler = Throttler(rate_limit=10, period=1)  # 10 requests per second (OpenAlex limit)

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


# async def async_get_cited(dois):
#     _dois = []
#     for doi in dois:
#         if not doi:
#             continue
#         works = await async_get_work_by(doi, select='referenced_works', doi=True)
#         for work in works:
#             ids = work.get('referenced_works', [])
#             for id in ids:
#                 _doid = await async_get_work_by(id.replace('https://openalex.org/', ''), select='doi')
#                 _doi = [0].get('doi', 'https://doi.org/')
#                 if _doi is not None:
#                     _doi = _doi.replace('https://doi.org/', '')
#                 if _doi:
#                     _dois.append(_doi)
#     return dois + _dois

def get_citing(dois):
    works = []
    _dois = []
    for doi in dois:
        if not doi:
            continue
        _id = get_work_by(doi, select='id', doi=True)
        id = _id[0].get('id', '').replace('https://openalex.org/', '')
        works += get_work_by(id, select='doi', cites=True)
    for work in works:
        for result in work.get('results', {'doi':''}):
            if result['doi'] is not None:
                _doi = result['doi'].replace('https://doi.org/', '')
            else:
                _doi = ''
            if _doi:
                _dois.append(_doi)
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

# async def async_get_citing(dois):
#     works = []
#     _dois = []
#     for doi in dois:
#         if not doi:
#             continue
#         _id = await async_get_work_by(doi, select='id', doi=True)
#         id = _id[0].get('id', '').replace('https://openalex.org/', '')
#         works += await async_get_work_by(id, select='doi', cites=True)
#     for work in works:
#         for result in work.get('results', {'doi':''}):
#             if result['doi'] is not None:
#                 _doi = result['doi'].replace('https://doi.org/', '')
#             else:
#                 _doi = ''
#             if _doi:
#                 _dois.append(_doi)
#     return dois + _dois