import os
import shutil
from colorama import Fore, Style


def backupandwrite(fn, _content):
    if os.path.exists(fn):
        _backup = f'{fn}.bak'
        print(f'{Style.BRIGHT}{Fore.YELLOW}Backing up {Fore.CYAN}{fn}{Fore.YELLOW} as {Fore.CYAN}{_backup}')
        shutil.copy(fn, _backup)
    with open(fn, 'w+b') as fh:
        fh.write(_content)
        print(f'{Style.BRIGHT}{Fore.YELLOW}Wrote {Fore.CYAN}{fn}{Fore.YELLOW}.')