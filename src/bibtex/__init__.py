from .read import load_bib_from_file
from .dedupe import dedupe_bib_library

def read(fn, dedupe=False):
    return load_bib_from_file(fn, dedupe=False)

def dedupe(library):
    return dedupe_bib_library(library)
