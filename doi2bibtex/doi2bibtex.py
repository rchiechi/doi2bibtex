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
from colorama import init, Fore, Style
from tqdm.asyncio import tqdm_asyncio
import logging
from contextlib import contextmanager

# Setup colors
init(autoreset=True)
 
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
        if not doi:
            # print(f'{Fore.BLUE}{Style.BRIGHT}_', end=Style.RESET_ALL)
            return
        if doi.lower() in dois_in_library:
            # print(f'{Fore.RED}{Style.BRIGHT}!', end=Style.RESET_ALL)
            return
        #print(f'{Style.BRIGHT}*', end=Style.RESET_ALL)
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
                    #print(f"|{Fore.YELLOW}Duplicate key replaced with {_entry.key}|", end=Style.RESET_ALL)
                library.add(_entry)
                citekeys_in_library.append(_entry.key.lower())
                # print(f"|{Fore.GREEN}{_entry.key}:{doi}", end=Style.RESET_ALL+'|')
                added += 1
            # else:
            #     print(f'{Fore.RED}{Style.BRIGHT}X', end=Style.RESET_ALL)
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
            # Buffer log messages during the progress bar to avoid interleaving
            await tqdm_asyncio.gather(*tasks, desc="Processing dois", colour='blue', unit='bib')
    if added:
        print(f"{Fore.CYAN}Upadted library with {Style.BRIGHT}{added}{Style.NORMAL} DOIs.")
    # Summarize any OpenAlex fetch failures
    failures = get_failures()
    if failures:
        print()
        print(f"{Fore.RED}⚠️  {len(failures)} OpenAlex fetches failed.{Style.RESET_ALL}")
        for url, msg in failures:
            print(f"  • {url}: {msg}")

    await getattr(output, args.outputmode)(library, args)


   
def main():
    asyncio.run(async_main())
    
if __name__ == "__main__":
    main()