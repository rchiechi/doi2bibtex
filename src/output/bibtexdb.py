import os
import shutil
import bibtexparser
import bibtexparser.middlewares as m
from colorama import Fore, Style
import util
import bibtex
import interact

logger = util.getlogger(__name__)

layers = [
    m.LatexEncodingMiddleware(True)
]

def do_bibtexdb(library: bibtexparser.library, args):
    journals = util.loadabbreviations(args.database,
                                      custom=args.custom,
                                      refresh=args.refresh)
    if args.clean and journals:
        cleaner = bibtex.clean(library, journals)
        library = cleaner.clean()
        journals.update(cleaner.custom)
        util.updatecache(journals)
    elif args.clean:
        print(f"{Style.BRIGHT}{Fore.RED}No journals parsed, cannot clean.")
    if args.dedupe:
        library = bibtex.dedupe(library)
    if not library.entries:
        print(f'{Style.BRIGHT}{Fore.YELLOW}Not writing empty library to file.')
    elif interact.ask(f"Save library to {args.out}?"):
        write_bib(library, args.out)
        if args.clean:
            parser = util.unicodeTolatex()
            parser.parsefile_inplace(args.out)


def write_bib(library: bibtexparser.library, db: str):
    if os.path.exists(db):
        _backup = f'{db}.bak'
        print(f'{Style.BRIGHT}{Fore.YELLOW}Backing up {Fore.CYAN}{db}{Fore.YELLOW} as {Fore.CYAN}{_backup}')
        shutil.copy(db, _backup)
    bibtex_format = bibtexparser.BibtexFormat()
    bibtex_format.indent = '    '
    bibtex_format.block_separator = '\n\n'
    bibtexparser.write_file(db, library, bibtex_format=bibtex_format)
    print(f'{Style.BRIGHT}{Fore.YELLOW}Wrote {Fore.CYAN}{db}{Fore.YELLOW}.')
