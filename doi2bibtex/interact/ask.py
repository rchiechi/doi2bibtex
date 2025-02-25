from colorama import init,Fore,Style,Back
from doi2bibtex.util import getlogger

logger = getlogger(__name__)

# Setup colors
init(autoreset=True)

def ask_yes_no(msg: str) -> bool:
    print(f"{Style.BRIGHT}{msg}")
    answer = ''
    while answer.lower() not in ('y','n','yes','no'):
        answer = input('y/n: ')
    if answer.lower() in ('y', 'yes'):
        return True
    return False