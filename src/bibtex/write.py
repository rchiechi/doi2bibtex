import os
import bibtexparser
import bibtexparser.middlewares as m
from .month import MonthIntMiddleware
from util import getlogger
from .dedupe import dedupe_bib_library
import interact

logger = getlogger(__name__)

layers = [
    m.LatexEncodingMiddleware(True)
]

def write_bib(library, db):
    if os.path.exists(db):
        if not interact.overwrite(os.path.basename(db)):
            return
    bibtexparser.write_file(db, library, append_middleware=layers)
