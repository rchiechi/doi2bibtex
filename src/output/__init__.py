from .bibtexdb import do_bibtexdb
from .clipboard import do_clipboard

def bibtexdb(library, args):
    return do_bibtexdb(library, args)

def clipboard(library, args):
    return do_clipboard(library, args)
