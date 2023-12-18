from .read import load_bib
from .dedupe import dedupe_bib_library
from .clean import EntryCleaner
from .replace import replace_doi_in_file

def read(fn, dedupe=False):
    return load_bib(fn, dedupe)

def dedupe(library):
    return dedupe_bib_library(library)

def clean(library, journals):
    return EntryCleaner(library, journals)

def replacedois(fn, library, citecmd, trim):
    return replace_doi_in_file(fn, library, citecmd, trim)
