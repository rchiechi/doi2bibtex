import os
import bibtexparser
import bibtexparser.middlewares as m
# from .month import MonthIntStrMiddleware
from doi2bibtex.util.getdoilogger import return_logger as getlogger
from .dedupe import dedupe_bib_library

logger = getlogger(__name__)

layers = [
    m.LatexDecodingMiddleware(True),
    m.MonthIntMiddleware(True)
]

def load_bib(bibtex, dedupe=False):
    logger.debug(f"Loading bib with dedupe={dedupe}")
    library = bibtexparser.parse_string('')
    try:
        if os.path.exists(bibtex):
            library = bibtexparser.parse_file(bibtex, append_middleware=layers)
        else:
            library = bibtexparser.parse_string(bibtex, append_middleware=layers)
        if dedupe:
            return dedupe_bib_library(library)
    except Exception as e:
        logger.error(e)
    finally:
        return library

def getkeys(library, key, lower=True):
    keys = []
    for entry in library.entries:
        for _field in entry.fields_dict:
            if _field.lower() == key.lower():
                if lower:
                    _val = str(entry.fields_dict[_field].value).lower()
                else:
                    _val = str(entry.fields_dict[_field].value)
                keys.append(_val)
    return keys

def getcitekeys(library, lower=False):
    keys = []
    for entry in library.entries:
        if lower:
            keys.append(entry.key.lower())
        else:
            keys.append(entry.key)
    return keys