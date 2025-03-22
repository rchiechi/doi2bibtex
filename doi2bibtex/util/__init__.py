import urllib.parse
from .doitobibtex import async_get_bibtex_from_url, PAGERES
from .getlogger import return_logger
from .doifinder import find_doi, find_doi_in_bytearray
from .cache import loadcache, writetodisk
from .abbreviso import local_iso4
from .LaTexAccents import AccentConverter
from .encode import LatexEncoder
from .spinner import Spinner

# def doitobibtex(doi):
#     return get_bibtex_from_url(doi)

def getlogger(_name=None, **kwargs):
    return return_logger(_name, **kwargs)

def doifinder(textstring):
    return find_doi(textstring)

def loadabbreviations(database, **kwargs):
    return loadcache(database, **kwargs)

def updatecache(journals):
    return writetodisk(journals)

def getISO4(journal):
    return local_iso4(journal)

def doitolink(doi):
    return 'https://dx.doi.org/'+urllib.parse.quote(doi)

def latexAccentConverter():
    return AccentConverter()

def unicodeTolatex():
    return LatexEncoder()
