'''Simple caching functions for journal abbreviations'''
import sys
import os
import tempfile
import pickle
import requests
from colorama import init,Fore,Style
from .getlogger import return_logger

logger = return_logger(__name__)

# Setup colors
init(autoreset=True)

# Setup cache dir
if 'APPDATA' in os.environ:
    CACHEDIR = os.path.join(
        os.getenv('APPDATA'), 'BibTexCleaner')
else:
    CACHEDIR = os.path.join(
        os.path.expanduser('~'), '.cache')

if not os.path.exists(CACHEDIR):
    try:
        # Create it if it doesn't exist
        os.makedirs(CACHEDIR)
    except OSError as msg:
        # Fall back to global tempdir
        CACHEDIR = tempfile.gettempdir()
JCACHE=os.path.join(CACHEDIR,'journal_abbreviations.cache')


def refresh():
    '''Delete the disk cache'''
    logger.debug(f"Expiring {JCACHE}")
    if os.path.exists(JCACHE):
        os.remove(JCACHE)

def loadcache(database, **kwargs):
    '''Fetch journals from disk cache.'''
    if kwargs.get('refresh', False):
        refresh()
    journals = {}
    if not os.path.exists(JCACHE):
        logger.debug('Fetching list of common journal abbreviations.')
        _r = requests.get(database)
        if _r.status_code != 200:
            logger.error("Error fetching journal abbreviations with code %s", _r.status_code)
        else:
            journals = parseabbreviations(_r.text.split('\n'))
    else:
        try:
            journals = pickle.load(open(JCACHE,'rb'))
            logger.debug('Read journal abbreciations from %s.', JCACHE)
        except OSError:
            logger.error('Error loading cache from %s.', JCACHE)
            kwargs['refresh'] = True
            loadcache(database, **kwargs)
    if kwargs.get('custom', {}):
        journals.update(parseabbreviations(kwargs['custom'], False))
    writetodisk(journals)
    logger.debug(f"Loaded {len(journals)} abbreviations.")
    return journals

def writetodisk(journals):
    '''Save cache to disk'''
    try:
        pickle.dump(journals,open(JCACHE,'wb'))
        logger.debug('Saved cache to %s', JCACHE)
    except OSError:
        logger.debug('Error saving cache to %s' ,JCACHE)

def parseabbreviations(entries, quiet=True):
    '''Parse abbreviations in the format "ACS Applied Materials & Interfaces","ACS Appl. Mater. Interfaces"'''
    journals = {}
    for _l in entries:
        _t, _a = None, None
        for _delim in (',', ';', '='):
            try:
                _t, _a = _l.split(_delim)
            except ValueError:
                continue
        if _t is None or _a is None:
            continue
        journals[_t.strip()] = _a.strip()
        if len(_t.split('(')) > 1:
            journals[_t.split('(')[0].strip()] = _a.split('(')[0].strip()
        if not quiet:
            logger.info("Adding custom journal %s => %s", _t, _a)
    return journals
