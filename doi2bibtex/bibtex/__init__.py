from .read import load_bib, getkeys, getcitekeys
from .dedupe import dedupe_bib_library
from .clean import EntryCleaner
from .replace import replace_doi_in_file
from .openalex import get_cited, get_citing, async_get_cited, async_get_citing

def read(fn, dedupe=False):
    return load_bib(fn, dedupe)

def dedupe(library):
    return dedupe_bib_library(library)

def clean(library, journals):
    return EntryCleaner(library, journals)

def replacedois(fn, library, citecmd, trim):
    return replace_doi_in_file(fn, library, citecmd, trim)

# def openalex(doi):
#     return get_work_by(doi, doi=True)

def listKeyinLibrary(library, key):
    return getkeys(library, key)

def listCitekeys(library, lower=False):
    return getcitekeys(library, lower)
