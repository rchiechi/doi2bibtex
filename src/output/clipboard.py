import sys
import pyperclip
import bibtexparser
import bibtexparser.middlewares as m

layers = [
    m.LatexEncodingMiddleware(True)
]

def do_clipboard(library, args):
    bibtex_format = bibtexparser.BibtexFormat()
    bibtex_format.indent = '    '
    bibtex_format.block_separator = '\n\n'
    bibtex = bibtexparser.write_string(library, bibtex_format=bibtex_format)
    if args.stdout:
        sys.stdout.write(bibtex)
        sys.stdout.flush()
    else:
        pyperclip.copy(bibtex)