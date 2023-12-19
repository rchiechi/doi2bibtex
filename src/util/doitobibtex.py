import urllib.request
from urllib.error import HTTPError
import http
from .getlogger import return_logger

BASE_URL = 'https://dx.doi.org/'

logger = return_logger(__name__)

def get_bibtex_from_url(doi):
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
    return bibtex
