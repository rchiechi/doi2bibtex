from .read import load_bib
from .dedupe import dedupe_bib_library
from .write import write_bib
from .clean import EntryCleaner

def read(fn, dedupe=False):
    return load_bib(fn, dedupe)

def write(library, fn):
    return write_bib(library, fn)

def dedupe(library):
    return dedupe_bib_library(library)

def clean(library, journals):
    return EntryCleaner(library, journals)
