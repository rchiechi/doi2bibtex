import os
import shutil
import bibtex
import bibtexparser
from colorama import Fore, Style

bibtex_format = bibtexparser.BibtexFormat()
bibtex_format.indent = '    '
bibtex_format.block_separator = '\n\n'


def do_textfile(library, args):
    if args.replace:
        _file = bibtex.replacedois(args.doifile, library, args.citecmd, args.trim)
    else:
        _file = bytes(bibtexparser.write_string(library, bibtex_format=bibtex_format), encoding='utf-8')
    if not _file:
        print(f'{Style.BRIGHT}{Fore.YELLOW}Not writing empty file.')
        return
    if os.path.exists(args.out):
        _backup = f'{args.out}.bak'
        print(f'{Style.BRIGHT}{Fore.YELLOW}Backing up {Fore.CYAN}{args.out}{Fore.YELLOW} as {Fore.CYAN}{_backup}')
        shutil.copy(args.out, _backup)
    with open(args.out, 'w+b') as fh:
        fh.write(_file)
        print(f'{Style.BRIGHT}{Fore.YELLOW}Wrote {Fore.CYAN}{args.out}{Fore.YELLOW}.')
