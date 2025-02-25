import doi2bibtex.bibtex as bibtex
from .filewriter import backupandwrite
from .bibtexdb import write_bib
import bibtexparser
from colorama import Fore, Style

bibtex_format = bibtexparser.BibtexFormat()
bibtex_format.indent = '    '
bibtex_format.block_separator = '\n\n'


def do_textfile(library, args):
    if args.replace:
        _file = bibtex.replacedois(args.doifile, library, args.citecmd, args.trim)
        write_bib(library, args.replace)
    else:
        _file = bytes(bibtexparser.write_string(library, bibtex_format=bibtex_format), encoding='utf-8')
    if not _file:
        print(f'{Style.BRIGHT}{Fore.YELLOW}Not writing empty file.')
        return
    backupandwrite(args.out, _file)
