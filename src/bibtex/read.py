import os
import bibtexparser
import bibtexparser.middlewares as m
from .month import MonthIntStrMiddleware
from util import getlogger
from .dedupe import dedupe_bib_library

logger = getlogger(__name__)

layers = [
    MonthIntStrMiddleware(True), # Months should be represented as str-int (0-12)
    m.LatexDecodingMiddleware(True)
]

def load_bib(bibtex, dedupe=False):
    logger.debug(f"Loading bib with dedupe={dedupe}")
    if os.path.exists(bibtex):
        library = bibtexparser.parse_file(bibtex, append_middleware=layers)
    else:
        library = bibtexparser.parse_string(bibtex, append_middleware=layers)
    if dedupe:
        return dedupe_bib_library(library)
    return library
