from .doitobibtex import get_bibtex_from_url
from .getlogger import return_logger

def doitobibtex(doi):
    return get_bibtex_from_url(doi)

def getlogger(_name=None, **kwargs):
    return return_logger(_name, **kwargs)