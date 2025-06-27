from colorama import Fore,Style
from doi2bibtex.util import getlogger
from .ask import ask_yes_no

logger = getlogger(__name__)

def ask_overwrite(fn: str) -> bool:
    '''Ask user to overwrite a file'''
    return ask_yes_no(f"{Style.BRIGHT}{Fore.WHITE}Overwrite {Fore.YELLOW}{fn}{Fore.WHITE}?")
