from .bibtexdb import do_bibtexdb
from .clipboard import do_clipboard
from .textfile import do_textfile
from .list import do_html, do_markdown, do_textlist

def bibtexdb(library, args):
    return do_bibtexdb(library, args)

def clipboard(library, args):
    return do_clipboard(library, args)

def textfile(library, args):
    return do_textfile(library, args)

def html(library, args):
    return do_html(library, args)

def markdown(library, args):
    return do_markdown(library, args)

def textlist(library, args):
    return do_textlist(library, args)