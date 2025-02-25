import urllib.request
from urllib.error import HTTPError
import http
import json
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

def get_citing(dois):
    works = []
    _dois = []
    for doi in dois:
        if not doi:
            continue
        id = get_work_by(doi, select='id', doi=True)[0].get('id', '').replace('https://openalex.org/', '')
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
