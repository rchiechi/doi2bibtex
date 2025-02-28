#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import sys
import asyncio
from asyncio_throttle import Throttler
import doi2bibtex.opts as opts
import doi2bibtex.util as util
import doi2bibtex.bibtex as bibtex
import doi2bibtex.output as output
import doi2bibtex.web_app as web_app
from colorama import init, Fore, Style

# Setup colors
init(autoreset=True)



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
    throttler = Throttler(rate_limit=5, period=1)
    async def process_doi(doi):
        nonlocal added
        nonlocal incr
        if not doi:
            print(f'{Fore.BLUE}{Style.BRIGHT}_', end=Style.RESET_ALL)
            return
        if doi.lower() in dois_in_library:
            print(f'{Fore.RED}{Style.BRIGHT}!', end=Style.RESET_ALL)
            return
        #print(f'{Style.BRIGHT}*', end=Style.RESET_ALL)
        async with throttler:
            result = await util.async_get_bibtex_from_url(doi)
        if result:
            _entry = bibtex.read(result).entries[0]
            if _entry.key.lower() in citekeys_in_library:
                _entry.key = f"{_entry.key}_{incr}"
                incr += 1
                #print(f"|{Fore.YELLOW}Duplicate key replaced with {_entry.key}|", end=Style.RESET_ALL)
            library.add(_entry)
            citekeys_in_library.append(_entry.key.lower())
            print(f"|{Fore.GREEN}{_entry.key}:{doi}", end=Style.RESET_ALL+'|')
            added += 1
        else:
            print(f'{Fore.RED}{Style.BRIGHT}X', end=Style.RESET_ALL)
    tasks = [process_doi(doi) for doi in set(dois)]
    await asyncio.gather(*tasks)
    
    print('')
    if added:
        print(f"{Fore.CYAN}Upadted library with {Style.BRIGHT}{added}{Style.NORMAL} DOIs.")

    await getattr(output, args.outputmode)(library, args)


   
def main():
    asyncio.run(async_main())
    
if __name__ == "__main__":
    main()