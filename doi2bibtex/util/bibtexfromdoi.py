import urllib.request
from urllib.error import HTTPError
import http
import asyncio
import re
from typing import Union
import httpx
from .getlogger import return_logger
from doi2bibtex.bibtex import get_metadata_from_dois
from colorama import Fore, Style
from json import JSONDecodeError

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
            response = await client.get(url,
                                        headers={'Accept': 'application/x-bibtex'},
                                        follow_redirects=True,
                                        timeout=30)
            response.raise_for_status()
            bibtex = response.text
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 404:
                logger.error(f"Could not resolve {doi}")
            elif err.response.status_code == 429:
                logger.error(f"Rate-limit exteeded for {BASE_URL}")
            else:
                logger.error(f"Error {err.response.status_code} while fetching {url}")
        except httpx.InvalidURL:
            logger.error(f"'{doi}' is not a valid url")
        except httpx.ReadTimeout:
            logger.error(f"Timeout fetching {url}")
        except httpx.ConnectError as err:
            logger.error(f"Connection error fetching {url}: {err}")
    if 'pages' not in bibtex.lower():
        bibtex = await add_pages(bibtex, doi)
    return bibtex

async def add_pages(bibtex, doi):
    page = ''
    logger.info("Looking for page in json from DOI:%s", doi)
    
    if isinstance(doi, bytes):
        doi = str(doi, encoding='utf-8')
    
    metadata = await async_get_metadata_from_dois([doi])
    page_info = extract_page_info_from_aleks(list(metadata.values())[0])
    
    if page_info['first_page']:
        page = page_info['first_page']
    
    if not page:
        url = BASE_URL + doi
        json_bib = {}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url,
                                            headers={'Accept': 'application/json'},
                                            follow_redirects=True,
                                            timeout=30)
                response.raise_for_status()
                json_bib = response.json()
            except httpx.HTTPStatusError as err:
                if err.response.status_code == 404:
                    logger.error(f"Could not resolve {doi}")
                else:
                    logger.error(f"Error {err.response.status_code} while fetching {url}")
            except httpx.InvalidURL:
                logger.error(f"'{doi}' is not a valid url")
            except JSONDecodeError:
                logger.error(f"{url} did not return valid json.")
            except httpx.ReadTimeout:
                logger.error(f"Timeout fetching {url}")
            except httpx.ConnectError as err:
                logger.error(f"Connection error fetching {url}: {err}")
        for key in ('article-number',):
            if key in json_bib:
                page = json_bib[key]
    
    if page:
        logger.info(f"{Fore.YELLOW}page={page} from {key}{Style.RESET_ALL}")
        _biblist = bibtex.split(',')
        _biblist.insert(-1, f'pages={page}')
        return ','.join(_biblist)

    return guess_pages(bibtex, doi)

def guess_pages(bibtex, doi):
    page = ''
    
    for _pagere in PAGERES:
        m = re.match(_pagere, doi)
        try:
            page = m.group(1)
            logger.info(f"{Fore.YELLOW}page={page} from {doi}{Style.RESET_ALL}")
            break
        except (AttributeError, IndexError):
            continue
    if not page:
        return bibtex
    _biblist = bibtex.split(',')
    _biblist.insert(-1, f'pages={page}')
    return ','.join(_biblist)

def extract_page_info_from_aleks(work: dict) -> dict:
    """
    Extract page/article identifier information from OpenAlex work.
    
    Returns dict with 'pages', 'article_number', and 'page_type' fields.
    """
    biblio = work.get('biblio', {})
    first_page = biblio.get('first_page', '')
    last_page = biblio.get('last_page', '')
    
    page_info = {
        'first_page': first_page,
        'last_page': last_page,
        'pages': None,
        'article_number': None,
        'page_type': None
    }
    
    if first_page:
        # Check if it's likely an article number
        if (first_page.startswith('e') or 
            first_page.startswith('E') or
            'article' in str(first_page).lower() or
            (first_page.isdigit() and len(first_page) > 4 and not last_page)):
            page_info['article_number'] = first_page
            page_info['page_type'] = 'article_number'
        else:
            # Traditional page numbers
            if last_page:
                page_info['pages'] = f"{first_page}-{last_page}"
            else:
                page_info['pages'] = first_page
            page_info['page_type'] = 'traditional'
    
    return page_info
