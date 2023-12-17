import urllib.parse
import urllib.request
from urllib.error import HTTPError
from .getlogger import return_logger

BASE_URL='https://abbreviso.toolforge.org/abbreviso/a'

def query_abbreviso(journal):
    url = f'{BASE_URL}/{urllib.parse.quote(journal)}'
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=3) as f:
            abbreviation = f.read().decode()
    except HTTPError as err:
        if err.code == 404:
            logger.error(f"Could not resolve {journal}")
        else:
            logger.error(f"Error {err.code} while fetching {url}")
    return abbreviation
