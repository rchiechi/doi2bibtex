import bibtexparser
import bibtexparser.middlewares as m
from util import getlogger
from .dedupe import dedupe_bib_library

logger = getlogger(__name__)

def load_bib_from_file(fn, dedupe=False):
    layers = [
        #m.MonthIntMiddleware(True), # Months should be represented as int (0-12)
        m.LatexEncodingMiddleware(True)
        ]
    library = bibtexparser.parse_file(fn, append_middleware=layers)
    if dedupe:
        return dedupe_bib_library(library)
    return library