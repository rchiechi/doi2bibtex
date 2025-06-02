import urllib.parse
import urllib.request
from urllib.error import HTTPError
from iso4 import abbreviate
from .getdoilogger import return_logger

BASE_URL = 'https://abbreviso.toolforge.org/abbreviso/a'

logger = return_logger(__name__)

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

def local_iso4(journal):
    if len(journal.split('.')) > 2:
        return journal
    try:
        _iso4 = abbreviate(journal)
        if _iso4 and len(_iso4.split('.')):
            return _iso4
        else:
            return journal
    except LookupError:
        logger.info("To use ISO4 locally, install NLTK https://www.nltk.org/data.html")
        return query_abbreviso(journal)
