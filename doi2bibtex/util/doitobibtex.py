import urllib.request
from urllib.error import HTTPError
import http
import asyncio
import re
from typing import Union
import httpx
from .getlogger import return_logger

BASE_URL = 'https://dx.doi.org/'
PAGERES = (re.compile(r'^\d+\.\d+/\D+\.20(\d+)$'),
           re.compile(r'^\d+\.\d+/\D+(\d+)$'),
           re.compile(r'^\d+\.\d+/\D+\.\d+\.(\d+)$'))
logger = return_logger(__name__)


async def async_get_bibtex_from_url(doi: Union[str, bytes, None]) -> str:
    if doi is None:
        return ''
    if isinstance(doi, bytes):
        doi = str(doi, encoding='utf-8')
    bibtex = ''
    url = BASE_URL + doi
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers={'Accept': 'application/x-bibtex'}, follow_redirects=True)
            response.raise_for_status()
            bibtex = response.text
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 404:
                logger.error(f"Could not resolve {doi}")
            else:
                logger.error(f"Error {err.response.status_code} while fetching {url}")
        except httpx.InvalidURL:
            logger.error(f"'{doi}' is not a valid url")
    if 'pages' not in bibtex.lower():
        bibtex = await add_pages(bibtex, doi)
    return bibtex

# def get_bibtex_from_url(doi):
#     if doi is None:
#         return ''
#     if isinstance(doi, bytes):
#         doi = str(doi, encoding='utf-8')
#     bibtex = ''
#     url = BASE_URL + doi
#     req = urllib.request.Request(url)
#     req.add_header('Accept', 'application/x-bibtex')
#     try:
#         with urllib.request.urlopen(req) as f:
#             bibtex = f.read().decode()
#     except HTTPError as err:
#         if err.code == 404:
#             logger.error(f"Could not resolve {doi}")
#         else:
#             logger.error(f"Error {err.code} while fetching {url}")
#     except http.client.InvalidURL:
#         logger.error(f"'{doi}' is not a valid url")
#     if 'pages' not in bibtex.lower():
#         bibtex = add_pages(bibtex, doi)
#     return bibtex

async def add_pages(bibtex, doi):
    logger.info("Looking for page in json from DOI:%s", doi)
    if isinstance(doi, bytes):
        doi = str(doi, encoding='utf-8')
    url = BASE_URL + doi
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers={'Accept': 'application/json'}, follow_redirects=True)
            response.raise_for_status()
            json_bib = response.json()
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 404:
                logger.error(f"Could not resolve {doi}")
            else:
                logger.error(f"Error {err.response.status_code} while fetching {url}")
        except httpx.InvalidURL:
            logger.error(f"'{doi}' is not a valid url")
    for key in ('article-number',):
        if key in json_bib:
            page = json_bib[key]
            logger.info(f"Using key {key}:{page} as page number.")
            _biblist = bibtex.split(',')
            _biblist.insert(-1, f'pages={page}')
            return ','.join(_biblist)
    return guess_pages(bibtex, doi)

def guess_pages(bibtex, doi):
    page = ''
    logger.warning("Guessing page from DOI:%s", doi)
    for _pagere in PAGERES:
        m = re.match(_pagere, doi)
        try:
            page = m.group(1)
            break
        except (AttributeError, IndexError):
            continue
    if not page:
        return bibtex
    _biblist = bibtex.split(',')
    _biblist.insert(-1, f'pages={page}')
    return ','.join(_biblist)
