import urllib.request
from urllib.error import HTTPError
import http
import json
from util.getlogger import return_logger

BASE_URL = 'https://api.openalex.org/works'

logger = return_logger(__name__)

def get_work_by(id, **kwargs):
    if isinstance(id, bytes):
        id = str(id, encoding='utf-8')
    if kwargs.get('doi', False):
       id = f'doi:{id}'
    work = {}
    if kwargs.get('cites', False):
        url = f'{BASE_URL}?filter=cites:{id}'
    else:
        url = f'{BASE_URL}/{id}'
    if kwargs.get('select', None) is not None:
        url = f'{url}?select={kwargs["select"]}'
    logger.debug(f"Fetching {url}")
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as f:
            # work = f.read().decode()
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
        for id in get_work_by(doi, select='referenced_works', doi=True).get('referenced_works', []):
            _doi = get_work_by(id.replace('https://openalex.org/', ''), select='doi').get('doi', 'https://doi.org/')
            if _doi is not None:
                _doi = _doi.replace('https://doi.org/', '')
            if _doi:
                _dois.append(_doi)
    return dois + _dois

def get_citing(dois):
    _dois = []
    for doi in dois:
        if not doi:
            continue
        id = get_work_by(doi, select='id', doi=True).get('id', '').replace('https://openalex.org/', '')
        work = get_work_by(id, cites=True)
        print(work)
        print("Not ipmlemented")
        return dois
    #     _doi = get_work_by(id.replace('https://openalex.org/', ''), 'doi').get('doi', 'https://doi.org/')
    #         if _doi is not None:
    #             _doi = _doi.replace('https://doi.org/', '')
    #         if _doi:
    #             _dois.append(_doi)
    # return dois + _dois
