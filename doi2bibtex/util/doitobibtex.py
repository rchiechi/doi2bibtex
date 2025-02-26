import urllib.request
from urllib.error import HTTPError
import http
import asyncio
import re
from typing import Union
import httpx
from asyncio_throttle import Throttler
from .getlogger import return_logger

BASE_URL = 'https://dx.doi.org/'
PAGERES = (re.compile(r'^\d+\.\d+/\D+\.20(\d+)$'),
           re.compile(r'^\d+\.\d+/\D+(\d+)$'),
           re.compile(r'^\d+\.\d+/\D+\.\d+\.(\d+)$'))
logger = return_logger(__name__)

throttler = Throttler(rate_limit=5, period=1)  # 5 requests per second

async def async_get_bibtex_from_url(doi: Union[str, bytes, None]) -> str:
    if doi is None:
        return ''
    if isinstance(doi, bytes):
        doi = str(doi, encoding='utf-8')
    bibtex = ''
    url = BASE_URL + doi
    async with throttler:
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
        bibtex = add_pages(bibtex, doi)
    return bibtex

def get_bibtex_from_url(doi):
    if doi is None:
        return ''
    if isinstance(doi, bytes):
        doi = str(doi, encoding='utf-8')
    bibtex = ''
    url = BASE_URL + doi
    req = urllib.request.Request(url)
    req.add_header('Accept', 'application/x-bibtex')
    try:
        with urllib.request.urlopen(req) as f:
            bibtex = f.read().decode()
    except HTTPError as err:
        if err.code == 404:
            logger.error(f"Could not resolve {doi}")
        else:
            logger.error(f"Error {err.code} while fetching {url}")
    except http.client.InvalidURL:
        logger.error(f"'{doi}' is not a valid url")
    if 'pages' not in bibtex.lower():
        bibtex = add_pages(bibtex, doi)
    return bibtex

def add_pages(bibtex, doi):
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
