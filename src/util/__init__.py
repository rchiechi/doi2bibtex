from .doitobibtex import get_bibtex_from_url
from .getlogger import return_logger
from .doifinder import find_doi
from .cache import loadcache, writetodisk

def doitobibtex(doi):
    return get_bibtex_from_url(doi)

def getlogger(_name=None, **kwargs):
    return return_logger(_name, **kwargs)

def doifinder(textstring):
    return find_doi(textstring)

def loadabbreviations(database, **kwargs):
    return loadcache(database, **kwargs)

def updatecache(journals):
    return writetodisk(journals)
