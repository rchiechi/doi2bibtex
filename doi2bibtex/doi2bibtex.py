#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import sys
import doi2bibtex.opts as opts
import doi2bibtex.util as util
import doi2bibtex.bibtex as bibtex
import doi2bibtex.output as output
import doi2bibtex.web_app as web_app
from colorama import init, Fore, Style

# Setup colors
init(autoreset=True)

args = opts.getopts()

logger = util.getlogger('doi2bib', root=True, loglevel=args.loglevel)

logger.debug("Debug logging enabled.")

def main():

    if args.outputmode == 'webserver':
        logger.info(f"Starting server on {args.addr}:{args.port}")
        web_app.web_server(args.addr, args.port)
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
        dois = bibtex.get_cited(dois)
    if args.citing:
        dois = bibtex.get_citing(dois)
    
    added = 0
    dois_in_library = bibtex.listKeyinLibrary(library, 'doi')
    for doi in dois:
        print('.', end='')
        if not doi:
            print('x', end='')
            continue
        if doi.lower() in dois_in_library:
            print('!')
            continue
        result = util.doitobibtex(doi)
        if result:
            library.add(bibtex.read(result).entries)
            logger.debug(f"Added {doi} to library")
            added += 1
    print('')
    if added:
        print(f"{Fore.YELLOW}Upadted library with {Style.BRIGHT}{added}{Style.NORMAL} DOIs.")
    
    getattr(output, args.outputmode)(library, args)

if __name__ == '__main__':
    main()
