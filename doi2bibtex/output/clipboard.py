import sys
import pyperclip
import bibtexparser
import bibtexparser.middlewares as m
from doi2bibtex.util import unicodeTolatex

layers = [
    m.LatexEncodingMiddleware(True)
]

async def do_clipboard(library, args):
    bibtex_format = bibtexparser.BibtexFormat()
    bibtex_format.indent = '    '
    bibtex_format.block_separator = '\n\n'
    bibtex = bibtexparser.write_string(library, bibtex_format=bibtex_format)
    if not args.noclean:
        cleaner = unicodeTolatex()
        bibtex = cleaner.parsestring(bibtex)
    if args.stdout:
        sys.stdout.write(bibtex)
        sys.stdout.flush()
    else:
        pyperclip.copy(bibtex)