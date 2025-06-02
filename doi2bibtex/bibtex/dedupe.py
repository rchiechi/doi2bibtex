from colorama import Fore,Style,Back
from doi2bibtex.util.getdoilogger import return_logger as getlogger

logger = getlogger(__name__)


def dedupe_bib_library(library):
    '''Check for duplicate bibtex entries'''
    logger.debug("Starting dedupe run")
    for entry in library.failed_blocks:
        print(f"{Style.BRIGHT}Failed:{Fore.RED} {entry.key}")
    dedupe = []
    dupes = {}
    for entry in library.entries:
        _key, _p, _v, _j, _doi = entry.key, '', '', '', ''
        for _field in entry.fields_dict:
            if _field.lower() in ('page', 'pages'):
                _p = entry.fields_dict[_field].value.split('-')[0].strip().strip('-')
            if _field.lower() == 'journal':
                _j = entry.fields_dict[_field].value
            if _field.lower() == 'volume':
                _v = entry.fields_dict[_field].value
            if _field.lower() == 'doi':
                _doi = entry.fields_dict[_field].value
        if _p and _v or _doi:
            dedupe.append((_key, _p, _v, _j, _doi))
        else:
            logger.warn(f'Cannot dedue {entry.key}')
            continue
    while dedupe:
        # Pop a dedupe tuple off the list
        _e = dedupe.pop()
        for _c in dedupe:
            # See if it overlaps with tuples in the list
            if _e[1:3] == _c[1:3] and _e[4] == _c[4]:
                # Create a dictionary of lists of potential dupes keyed by ID
                if _e[0] in dupes:
                    dupes[_e[0]].append(_c)
                else:
                    dupes[_e[0]] = [_c]
    if dupes:
        return dodedupe(library, dupes)
    return library


def dodedupe(library, dupes):
    '''Function that does the actual deduping'''
    print('\nPossible dupes:\n')
    for _key in dupes:
        # dupe is a tuple (key, pages, volume, journal, doi)
        dupe = dupes[_key]
        i = 1
        dupelist = { str(i):library.entries_dict[_key]  }
        for _d in dupe:
            i += 1
            dupelist[str(i)] = library.entries_dict[_d[0]]
        print('\t\t# # #')
        for _n in dupelist:
            try:
                print('%s%s%s):   %s%s' % (Style.BRIGHT,Fore.YELLOW,_n,Fore.CYAN,dupelist[_n].key))
                print('%sJournal: %s%s%s' %(Fore.YELLOW,Style.BRIGHT,Fore.WHITE,dupelist[_n].fields_dict['journal'].value))
                print('%sVolume: %s%s%s' %(Fore.YELLOW,Style.BRIGHT,Fore.WHITE,dupelist[_n].fields_dict['volume'].value))
                print('%sPages: %s%s%s' %(Fore.YELLOW,Style.BRIGHT,Fore.WHITE,dupelist[_n].fields_dict['pages'].value), end='\n\n')
            except KeyError as msg:
                print("Error parsing entry: %s" % str(msg))
        keep = input('Keep which one?  ')
        if keep not in dupelist:
            print('%sKeeping all.' % (Fore.GREEN) )
        else:
            print('%sKeeping %s%s.' % (Style.BRIGHT,Fore.GREEN,dupelist[keep].key))
            for _n in dupelist:
                if _n == keep:
                    continue
                for entry in library.entries:
                    if entry.key == dupelist[_n].key:
                        print('%s%sDeleting%s %s%s%s' % (Fore.YELLOW,Back.RED,
                            Style.RESET_ALL,Style.BRIGHT,Fore.RED,entry.key))
                        library.remove(entry)
                        break
    return library