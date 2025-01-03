from .read import load_bib, getkeys
from .dedupe import dedupe_bib_library
from .clean import EntryCleaner
from .replace import replace_doi_in_file
from .openalex import get_cited, get_citing, get_work_by

def read(fn, dedupe=False):
    return load_bib(fn, dedupe)

def dedupe(library):
    return dedupe_bib_library(library)

def clean(library, journals):
    return EntryCleaner(library, journals)

def replacedois(fn, library, citecmd, trim):
    return replace_doi_in_file(fn, library, citecmd, trim)

def openalex(doi):
    return get_work_by(doi, doi=True)

def listKeyinLibrary(library, key):
    return getkeys(library, key)
