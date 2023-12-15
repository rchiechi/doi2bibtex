from .read import load_bib
from .dedupe import dedupe_bib_library

def read(fn, dedupe=False):
    return load_bib(fn, dedupe)

def dedupe(library):
    return dedupe_bib_library(library)
