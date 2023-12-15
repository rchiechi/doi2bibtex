import os
import bibtexparser
import bibtexparser.middlewares as m
from util import getlogger
from .dedupe import dedupe_bib_library

logger = getlogger(__name__)

layers = [
    #m.MonthIntMiddleware(True), # Months should be represented as int (0-12)
    m.LatexEncodingMiddleware(True)
]

def load_bib(bibtex, dedupe=False):
    if os.path.exists(bibtex):
        library = bibtexparser.parse_file(bibtex, append_middleware=layers)
    else:
        library = bibtexparser.parse_string(bibtex, append_middleware=layers)
    if dedupe:
        return dedupe_bib_library(library)
    return library
