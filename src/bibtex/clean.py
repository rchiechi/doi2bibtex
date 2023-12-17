import Levenshtein
from titlecase import titlecase
from colorama import Fore,Style
from util import getlogger, getISO4

logger = getlogger(__name__)

class EntryCleaner:

    recordkeys = ('title', 'journal')

    def __init__(self, library, journals):
        self.stop = False
        self.library = library
        self.journals = journals
        self.errors = []
        self.history = {}
        self.custom = {}
        self.stats = {'n_cleaned':0,
                      'n_parsed':0,
                      'n_abbreviated':0}

    def clean(self):
        for entry in self.library.entries:
            if self.stop:
                break
            self.library.replace(entry, self._clean_entry(entry))
        return self.library

    def _clean_entry(self, entry):
        '''Main record handling method that gets called when bibtexparser adds an entry'''
        if entry.entry_type.lower() != 'article':
            print(f'{Fore.RED}Cannot parse {entry.key} ({entry.entry_type})')
            self.errors.append(entry)
            return entry
        for key in EntryCleaner.recordkeys:
            if key not in entry.fields_dict:
                print(f'{Fore.RED}Cannot parse {entry.key} (missing: {key})')
                self.errors.append(entry)
                return entry
        cleantitle = titlecase(entry['title'])
        if cleantitle != entry.fields_dict['title']:
            self.stats['n_cleaned'] += 1
            entry.fields_dict['title'].value = cleantitle
        # File entries are pointless in shared bib files
        for key in ('file', 'bdsk-file-1'):
            if key in entry.fields_dict:
                del entry.fields_dict[key]
        if 'author' in entry.fields_dict:
            if ' and ' not in entry.fields_dict['author'].value and ',' in entry.fields_dict['author'].value:
                authors = []
                for author in entry.fields_dict['author'].split(','):
                    authors.append('{'+author.strip()+'}')
                entry.fields_dict['author'].value = " and ".join(authors)
        if entry.fields_dict['journal'] in list(self.journals.values()):
            logger.debug("Entry already parsed, skipping user input.")
            return entry
        return self._getuserinput(entry)

    def _getuserinput(self, entry):
        '''Determine if we need to ask the user for input and then do it.'''
        fuzzy, score = self._fuzzymatch(entry.fields_dict['journal'].value)
        _abbrev = False
        if entry.fields_dict['journal'].value in self.history:
            fuzzy = self.history[entry.fields_dict['journal'].value]
            _abbrev = bool(fuzzy)
        elif score > 0.95:
            _abbrev = True
        else:
            if score < 0.9:
                fuzzy = getISO4(entry.fields_dict['journal'].value)
                logger.debug(f'Using ISO4 "{fuzzy}"')
            try:
                _j = input('(%0.1f%%) Replace "%s%s%s" with "%s%s%s" or something else? ' % (
                    score * 100, Style.BRIGHT + Fore.YELLOW,
                    entry.fields_dict['journal'].value, Style.RESET_ALL,
                    Style.BRIGHT + Fore.GREEN,
                    fuzzy,Style.RESET_ALL))
                if _j.lower() in ('y','yes'):
                    _abbrev = True
                elif _j.lower() in ('n','no',''):
                    self.history[entry.fields_dict['journal'].value] = None
                elif _j:
                    self.custom[entry.fields_dict['journal'].value] = _j
                    fuzzy = _j
                    _abbrev = True
            except KeyboardInterrupt:
                print(' ')
                self.stop = True
                return entry
        if _abbrev and not entry.fields_dict['journal'].value == fuzzy:
            self.history[entry.fields_dict['journal'].value] = fuzzy
            print('%s%s%s%s -> %s%s%s' % (Style.BRIGHT, Fore.CYAN, entry.fields_dict['journal'].value,
                  Fore.WHITE, Fore.CYAN, fuzzy,Style.RESET_ALL))
            self.stats['n_abbreviated'] += 1
            entry.fields_dict['journal'].value = fuzzy
        entry.fields_dict['journal'].value = self._page_double_hyphen(entry.fields_dict['journal'].value)
        self.stats['n_parsed'] += 1
        return entry

    def _page_double_hyphen(self, page):
        if len(page.split('-')) in (1,3):
            return page
        elif len(page.split('-')) >= 2:
            return(f"{page.split('-')[0]}--{page.split('-')[-1]}")
        return page

    def _fuzzymatch(self, journal):
        '''Do a fuzzy match of journal names'''
        i = ('', 0)
        for key in self.journals:
            _a = Levenshtein.ratio(journal, key)
            _b = Levenshtein.ratio(journal, self.journals[key])
            if _a > i[1]:
                i = [self.journals[key], _a]
                # print(f'{journal}:{key}=>{_a}')
            if _b > i[1]:
                i = [self.journals[key], _b]
                # print(f'{journal}:{self.journals[key]}=>{_b}')
        return i

    def printinfostats(self):
        '''print stats in pretty colors'''
        print('%s%sParsed: %s\n%sCleaned: %s\n%sAbbreviated: %s\n%sFailed:%s%s' %
              (Style.BRIGHT, Fore.GREEN, self.stats['n_parsed'], Fore.YELLOW,
               self.stats['n_cleaned'], Fore.MAGENTA, self.stats['n_abbreviated'],
               Fore.RED, len(self.errors), Style.RESET_ALL))
        if self.errors:
            print('\nEntries that produced errors:\n')
            for err in self.errors:
                logger.info('* * * * * * * * * * * * * * * *')
                for key in EntryCleaner.recordkeys:
                    if key not in err:
                        logger.info('%s%s%s: -' % (Fore.RED,titlecase(key),Style.RESET_ALL))
                    else:
                        logger.info('%s: %s%s' % (titlecase(key),Style.BRIGHT,err[key]))
