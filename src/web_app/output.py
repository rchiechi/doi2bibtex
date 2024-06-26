import sys
import pyperclip
import bibtexparser
import bibtexparser.middlewares as m
from util import unicodeTolatex

layers = [
    m.LatexEncodingMiddleware(True)
]

def list_dois(library, **kwargs):
    bibtex_format = bibtexparser.BibtexFormat()
    bibtex_format.indent = '    '
    bibtex_format.block_separator = '\n\n'
    bibtex = bibtexparser.write_string(library, bibtex_format=bibtex_format)
    if not kwargs.get('noclean', False):
        cleaner = unicodeTolatex()
        bibtex = cleaner.parsestring(bibtex)
    return bibtex
