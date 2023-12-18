from .bibtexdb import do_bibtexdb
from .clipboard import do_clipboard
from .textfile import do_textfile
from .html import do_html

def bibtexdb(library, args):
    return do_bibtexdb(library, args)

def clipboard(library, args):
    return do_clipboard(library, args)

def textfile(library, args):
    return do_textfile(library, args)

def html(library, args):
    return do_html(library, args)