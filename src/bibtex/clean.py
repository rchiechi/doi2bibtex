'''The main class for parsing BiBTeX records'''
import sys
import Levenshtein  # pip3 install python-levenshtein
from titlecase import titlecase
from bibtexparser.customization import page_double_hyphen
from bibtexparser.latexenc import string_to_latex
from colorama import init,Fore,Style
from util import getlogger

logger = getlogger(__name__)

# Setup colors
init(autoreset=True)


class EntryCleaner:

    recordkeys = ('key', 'title', 'journal')

    def __init__(self, library, journals):
        self.library = library
        self.journals = journals
        self.errors = []
        self.history = {}
        self.stats = {'n_cleaned':0,
                      'n_parsed':0,
                      'n_abbreviated':0}

    def consider(self, entry):
        '''Main record handling method that gets called when bibtexparser adds an entry'''
        for key in RecordHandler.recordkeys:
            if key not in entry: # and record['ENTRYTYPE'] == 'journal':
                logger.info('%sCannot parse %s' % (Fore.RED, entry.key))
                self.errors.append(entry)
                # self.clean.append(record)
                return entry
        # for _key in ('pages', 'volume'):
        #     if _key not in entry:
        #         entry[_key] = ''
        cleantitle = titlecase(entry['title'])
        if cleantitle != entry['title']:
            self.stats['n_cleaned'] += 1
            entry.fields_dict['title'].value = cleantitle
        # File entries are pointless in shared bib files
        for key in ('file', 'bdsk-file-1'):
            if key in record:
                del record[key]
        # Non-numeric months do not sort
        if 'month' in record:
            if convertmonth(record['month']):
                record['month']=convertmonth(record['month'])
        # Names should be separated by 'and'; comma is to reverse name/surname order
        if 'author' in record:
            # logger.info(record['author'].split(','))
            if ' and ' not in record['author'] and ',' in record['author']:
                authors=[]
                for author in record['author'].split(','):
                    authors.append('{'+author.strip()+'}')
                record['author'] = " and ".join(authors)
        return self.__getuserinput(record)

    def __getuserinput(self, record):
        '''Determine if we need to ask the user for input and then do it.'''
        fuzzy,score = self.__fuzzymatch(record['journal'])
        __abbrev = False
        if record['journal'] in self.history:
            fuzzy = self.history[record['journal']]
            __abbrev = bool(fuzzy)
        elif score > 0.95:
            __abbrev = True
        else:
            try:
                _j = input('(%0.1f%%) Replace "%s%s%s" with "%s%s%s" or something else? ' % (
                    score*100,Style.BRIGHT+Fore.YELLOW,
                    record['journal'],Style.RESET_ALL,
                    Style.BRIGHT+Fore.GREEN,
                    fuzzy,Style.RESET_ALL))
                if _j.lower() in ('y','yes'):
                    __abbrev = True
                elif _j.lower() in ('n','no',''):
                    self.history[record['journal']] = None
                elif _j:
                    fuzzy = _j
                    __abbrev = True
            except KeyboardInterrupt:
                logger.info('')
                sys.exit()

        if __abbrev and not record['journal'] == fuzzy:
            self.history[record['journal']] = fuzzy
            logger.info('%s%s%s%s -> %s%s%s' % (Style.BRIGHT,Fore.CYAN,record['journal'],
                Fore.WHITE,Fore.CYAN,fuzzy,Style.RESET_ALL))
            self.stats['n_abbreviated'] += 1
            record['journal'] = fuzzy
        record['journal'] = string_to_latex(record['journal'])
        record = page_double_hyphen(record)
        self.stats['n_parsed'] += 1
        return record

    def __fuzzymatch(self,journal):
        '''Private method to do a fuzzy match of journal names'''
        i = ('',0)
        for key in self.journals:
            _a = Levenshtein.ratio(journal,key) #pylint: disable=E1101
            _b = Levenshtein.ratio(journal,self.journals[key]) #pylint: disable=E1101
            if _a > i[1]:
                i = [self.journals[key],_a]
            if _b > i[1]:
                i = [self.journals[key],_b]
        return i

    def getcustom(self):
        '''Return any custom journal abbreviations entered during handle_record'''
        unique = []
        for key in self.history:
            if self.history[key] is None:
                continue
            if key not in self.journals:
                unique.append(";".join([key, self.history[key]]))
                logger.info("%sCaching %s%s ==> %s" % (
                    Style.BRIGHT+Fore.CYAN, Fore.WHITE,
                    key, self.history[key]))
        return unique

    def logger.infostats(self):
        '''logger.info stats in pretty colors'''
        logger.info('%s%sParsed: %s\n%sCleaned: %s\n%sAbbreviated: %s\n%sFailed:%s%s' % \
                (Style.BRIGHT,Fore.GREEN,self.stats['n_parsed'],Fore.YELLOW,
                    self.stats['n_cleaned'],Fore.MAGENTA,self.stats['n_abbreviated'],
                    Fore.RED,len(self.errors),Style.RESET_ALL))
        if self.errors:
            logger.info('\nEntries that produced errors:\n')
            #logger.info(self.errors)
            for err in self.errors:
                logger.info('* * * * * * * * * * * * * * * *')
                for key in RecordHandler.recordkeys:
                    if key not in err:
                        logger.info('%s%s%s: -' % (Fore.RED,titlecase(key),Style.RESET_ALL))
                    else:
                        logger.info('%s: %s%s' % (titlecase(key),Style.BRIGHT,err[key]))
