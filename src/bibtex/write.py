import os
import shutil
import bibtexparser
import bibtexparser.middlewares as m
from colorama import Fore, Style
from util import getlogger
# import interact

logger = getlogger(__name__)

layers = [
    m.LatexEncodingMiddleware(True)
]

def write_bib(library: bibtexparser.library, db: str):
    if os.path.exists(db):
        _backup = f'{db}.bak'
        print(f'{Style.BRIGHT}{Fore.YELLOW}Backing up {Fore.CYAN}{db}{Fore.YELLOW} as {Fore.CYAN}{_backup}')
        shutil.copy(db, _backup)
        # if not interact.overwrite(os.path.basename(db)):
        #     return
    bibtexparser.write_file(db, library, append_middleware=layers)
