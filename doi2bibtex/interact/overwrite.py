from colorama import init,Fore,Style,Back
from doi2bibtex.util import getlogger

logger = getlogger(__name__)

# Setup colors
init(autoreset=True)

def ask_overwrite(fn: str) -> bool:
    '''Ask user to overwrite a file'''
    print(f"{Style.BRIGHT}{Fore.WHITE}Overwrite {Fore.YELLOW}{fn}{Fore.WHITE}?")
    answer = ''
    while answer.lower() not in ('y','n','yes','no'):
        answer = input('y/n: ')
    if answer.lower() in ('y', 'yes'):
        return True
    return False