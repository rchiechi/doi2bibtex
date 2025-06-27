import os
import shutil
import bibtexparser
import bibtexparser.middlewares as m
from rich.console import Console
import doi2bibtex.util as util
import doi2bibtex.bibtex as bibtex
import doi2bibtex.interact as interact

logger = util.getlogger(__name__)
console = Console()

layers = [
    m.LatexEncodingMiddleware(True)
]

async def do_bibtexdb(library: bibtexparser.library, args):
    journals = util.loadabbreviations(args.database,
                                      custom=args.custom,
                                      refresh=args.refresh)
    if args.clean and journals:
        cleaner = bibtex.EntryCleaner(library, journals)
        library = await cleaner.clean()
        journals.update(cleaner.custom)
        util.updatecache(journals)
    elif args.clean:
        console.print("[bold red]No journals parsed, cannot clean.[/bold red]")
    if args.dedupe:
        library, _ = bibtex.dedupe(library, use_llm=args.llm, llm_model=args.llm_model)
    if not library.entries:
        console.print('[bold yellow]Not writing empty library to file.[/bold yellow]')
    elif interact.ask(f"Save library to {args.out}?"):
        write_bib(library, args.out)
        if args.clean:
            parser = util.unicodeTolatex()
            parser.parsefile_inplace(args.out)


def write_bib(library: bibtexparser.library, db: str):
    if os.path.exists(db):
        _backup = f'{db}.bak'
        console.print(f'[bold yellow]Backing up [cyan]{db}[/cyan] as [cyan]{_backup}[/cyan][/bold yellow]')
        shutil.copy(db, _backup)
    bibtex_format = bibtexparser.BibtexFormat()
    bibtex_format.indent = '    '
    bibtex_format.block_separator = '\n\n'
    bibtexparser.write_file(db, library, bibtex_format=bibtex_format)
    console.print(f'[bold yellow]Wrote [cyan]{db}[/cyan].[/bold yellow]')