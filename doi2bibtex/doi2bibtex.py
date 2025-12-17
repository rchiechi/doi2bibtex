#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import sys
import asyncio
from asyncio_throttle import Throttler
import doi2bibtex.opts as opts
import doi2bibtex.util as util
import doi2bibtex.bibtex as bibtex
from doi2bibtex.bibtex.openalex import get_failures
import doi2bibtex.output as output
import doi2bibtex.web_app as web_app
from doi2bibtex.tex import cites
from doi2bibtex.llm import config_cli
from rich.console import Console
from tqdm.asyncio import tqdm_asyncio
import logging
from contextlib import contextmanager

console = Console()
 
@contextmanager
def _buffer_logs():
    """Temporarily buffer all 'doi2bib' logger output and flush after context."""
    root_logger = logging.getLogger('doi2bib')
    orig_handlers = root_logger.handlers[:]
    buf_records = []
    class BufferHandler(logging.Handler):
        def emit(self, record):
            buf_records.append(record)
    buf_handler = BufferHandler()
    # Replace handlers with buffer
    root_logger.handlers = [buf_handler]
    try:
        yield
    finally:
        # Flush buffered records
        for rec in buf_records:
            for h in orig_handlers:
                h.handle(rec)
        # Restore original handlers
        root_logger.handlers = orig_handlers



async def async_main():
    args = opts.getopts()
    
    logger = util.getlogger('doi2bib', root=True, loglevel=args.loglevel)
    
    logger.debug("Debug logging enabled.")
    if args.outputmode == 'webserver':
        logger.info(f"Starting server on {args.addr}:{args.port}")
        await web_app.web_server(args.addr, args.port)
        sys.exit()

    if args.outputmode == 'llm-config':
        config_cli.llm_config_main(args)
        sys.exit()

    if args.outputmode == 'tex':
        if args.check_cites:
            if not args.bibtexdb:
                logger.error("The --check-cites option requires a --bibtexdb to be specified.")
                sys.exit(1)
            cites.check_tex_cites(args.tex_files, args.bibtexdb, use_llm=args.llm, llm_model=args.llm_model)
        sys.exit()
    
    if args.bibtexdb:
        library = bibtex.read(args.bibtexdb)
        logger.debug(f"Parsed {len(library.entries)} from {args.bibtexdb}.")
    else:
        library = bibtex.read('')
    
    dois = list(map(str.strip, args.dois.split(','))) + args.more_dois
    if args.doifile:
        dois += util.doifinder(args.doifile)
        logger.debug(dois)
    
    if args.cited:
        dois = await bibtex.async_get_cited(dois)
    if args.citing:
        dois = await bibtex.async_get_citing(dois)
    
   
    
    added = 0
    dois_in_library = bibtex.listKeyinLibrary(library, 'doi')
    citekeys_in_library = bibtex.listCitekeys(library, lower=True)
    incr = 1
    doi_throttler = Throttler(rate_limit=5, period=1)
    alex_throttler = Throttler(rate_limit=3, period=1)
    async def process_doi(doi):
        nonlocal added
        nonlocal incr
        doi = util.doi_from_url(doi)
        if not doi:
            return
        if doi.lower() in dois_in_library:
            return
        async with alex_throttler:
            metadata = await bibtex.async_get_metadata_from_doi(doi)
        async with doi_throttler:
            result = await bibtex.async_get_bibtex_from_url(doi, metadata)
        if result:
            try:
                _entry = bibtex.read(result).entries[0]
                if _entry.key.lower() in citekeys_in_library:
                    _entry.key = f"{_entry.key}_{incr}"
                    incr += 1
                library.add(_entry)
                citekeys_in_library.append(_entry.key.lower())
                added += 1
            except IndexError:
                logger.warning(f"Error adding doi: {doi}")
    
    with _buffer_logs():        
        if len(dois) < 10:
            async with util.Spinner("Resolving: ") as spinner:
                tasks = [asyncio.create_task(process_doi(doi)) for doi in set(dois)]
                pending = set(tasks)
                while pending:
                    done, pending = await asyncio.wait(pending, timeout=0.1, return_when=asyncio.FIRST_COMPLETED)
                    await spinner.update()
        else:
            tasks = [process_doi(doi) for doi in set(dois)]
            await tqdm_asyncio.gather(*tasks, desc="Processing dois", colour='blue', unit='bib')
    if added:
        console.print(f"[cyan]Updated library with [bold]{added}[/bold] DOIs.[/cyan]")
    # Summarize any OpenAlex fetch failures
    failures = get_failures()
    if failures:
        console.print()
        console.print(f"[red]⚠️  {len(failures)} OpenAlex fetches failed.[/red]")
        for url, msg in failures:
            console.print(f"  • {url}: {msg}")

    await getattr(output, args.outputmode)(library, args)


   
def main():
    asyncio.run(async_main())
    
if __name__ == "__main__":
    main()
