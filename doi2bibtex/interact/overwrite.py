from rich.console import Console
from doi2bibtex.util import getlogger
from .ask import ask_yes_no

logger = getlogger(__name__)
console = Console()

def ask_overwrite(fn: str) -> bool:
    '''Ask user to overwrite a file'''
    return ask_yes_no(f"[bold white]Overwrite [yellow]{fn}[/yellow]?[/bold white]")