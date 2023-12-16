import os
import bibtexparser
import bibtexparser.middlewares as m
from .month import MonthIntMiddleware
from util import getlogger
from .dedupe import dedupe_bib_library
import interact

logger = getlogger(__name__)

layers = [
    m.RemoveEnclosingMiddleware(True), # Remove enclosures to parse dates correctly
    m.MonthIntMiddleware(True), # Months should be represented as int (0-12)
    m.LatexDecodingMiddleware(True)
]

def write_bib(library, db):
    if os.path.exists(db):
        if not interact.overwrite(os.path.basename(db)):
            return
    bibtexparser.write_file(db, library)
