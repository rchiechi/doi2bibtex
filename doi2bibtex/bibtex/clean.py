from typing import Dict, List, Tuple, Optional
import bibtexparser
from bibtexparser.model import Entry, Field
from colorama import Fore, Style
from titlecase import titlecase
from colorama import Fore,Style
from doi2bibtex.util import getlogger, getISO4, doitobibtex

logger = getlogger(__name__)

def get_pages(doi):
    page = ''
    if doi is None:
        return page
    _lib = bibtexparser.parse_string(doitobibtex(doi.value))
    for entry in _lib.entries:
        if 'pages' in entry.fields_dict:
            page = entry.fields_dict['pages'].value
    if not page:
        logger.warning(f'Failed to guess pages for {doi.value}')
    return page


class EntryCleaner:

        self.library = library
        self.journals = journals
        for entry in self.library.entries:
            if self.stop:
                break
            self.library.replace(entry, self._clean_entry(entry))
        return self.library

    def _clean_entry(self, entry: Entry) -> Entry:
        """Clean a single entry, handling validation and cleaning steps."""
        # Validate entry type and required fields
        if entry.entry_type.lower() != 'article':
            print(f'{Fore.RED}Cannot parse {entry.key} ({entry.entry_type})')
            self.errors.append(entry)
            return entry
            
        for key in self.REQUIRED_KEYS:
            if key not in entry.fields_dict:
                print(f'{Fore.RED}Cannot parse {entry.key} (missing: {key})')
                self.errors.append(entry)
                return entry

        # Clean title
        clean_title = titlecase(entry.fields_dict['title'].value)
        if clean_title != entry.fields_dict['title'].value:
            self.stats['n_cleaned'] += 1
            entry.fields_dict['title'].value = clean_title

        # Remove unwanted fields
        for key in self.REMOVE_KEYS:
            entry.fields_dict.pop(key, None)

        # Clean author formatting
        if 'author' in entry.fields_dict:
            author_value = entry.fields_dict['author'].value
            if ' and ' not in author_value and ',' in author_value:
                authors = ['{' + author.strip() + '}' for author in author_value.split(',')]
                entry.fields_dict['author'].value = " and ".join(authors)

        # Handle journal abbreviations
        journal_value = entry.fields_dict['journal'].value
        if journal_value in self.journals.values():
            logger.debug("Entry already parsed, skipping user input.")
            return entry

        return self._handle_journal_abbreviation(entry)

    def _handle_journal_abbreviation(self, entry: Entry) -> Entry:
        """Handle journal abbreviation with fuzzy matching and user input."""
        journal = entry.fields_dict['journal'].value
        fuzzy_match, score = self._fuzzy_match(journal)
        should_abbreviate = False

        # Check history or determine if we should abbreviate
        if journal in self.history:
            fuzzy_match = self.history[journal]
            should_abbreviate = bool(fuzzy_match)
        elif score > 0.95:
            should_abbreviate = True
        else:
            if score < 0.9:
                iso4_abbrev = getISO4(journal)
                if iso4_abbrev == journal or journal.replace('.', ',') == iso4_abbrev:
                    should_abbreviate = True
                    fuzzy_match = journal
                else:
                    logger.debug(f'Using ISO4 "{iso4_abbrev}"')
                    fuzzy_match = iso4_abbrev

        # Get user input if needed
        if not should_abbreviate:
            should_abbreviate, fuzzy_match = self._get_user_input(journal, fuzzy_match, score)
            if self.stop:  # Handle interruption
                return entry

        # Apply abbreviation if approved
        if should_abbreviate and journal != fuzzy_match:
            self._apply_abbreviation(entry, journal, fuzzy_match)

        # Handle pages
        self._handle_pages(entry)
        
        self.stats['n_parsed'] += 1
        return entry

    def _fuzzy_match(self, journal: str) -> Tuple[str, float]:
        """Find closest matching journal name using Levenshtein distance."""
        best_match = ('', 0)
        
        for full_name, abbrev in self.journals.items():
            full_score = Levenshtein.ratio(journal, full_name)
            abbrev_score = Levenshtein.ratio(journal, abbrev)
            
            if full_score > best_match[1]:
                best_match = (abbrev, full_score)
            if abbrev_score > best_match[1]:
                best_match = (abbrev, abbrev_score)
                
        return best_match

    def _get_user_input(self, journal: str, suggestion: str, score: float) -> Tuple[bool, str]:
        """Get user input for journal abbreviation decision."""
        try:
            response = input(
                f'({score*100:.1f}%) Replace "{Style.BRIGHT}{Fore.YELLOW}{journal}{Style.RESET_ALL}" '
                f'with "{Style.BRIGHT}{Fore.GREEN}{suggestion}{Style.RESET_ALL}" '
                f'or something else? '
            )
            
            if response.lower() in ('y', 'yes'):
                return True, suggestion
            elif response.lower() in ('n', 'no', ''):
                self.history[journal] = None
                return False, suggestion
            elif response:
                self.custom[journal] = response
                return True, response
                
        except KeyboardInterrupt:
            print(' ')
            self.stop = True
            
        return False, suggestion

    def _apply_abbreviation(self, entry: Entry, original: str, abbreviated: str):
        """Apply approved journal abbreviation and update stats."""
        self.history[original] = abbreviated
        print(f'{Style.BRIGHT}{Fore.CYAN}{original}{Fore.WHITE} -> '
              f'{Fore.CYAN}{abbreviated}{Style.RESET_ALL}')
        self.stats['n_abbreviated'] += 1
        entry.fields_dict['journal'].value = abbreviated

    def _handle_pages(self, entry: Entry):
        """Handle page number formatting and addition."""
        if 'pages' not in entry.fields_dict:
            doi = entry.fields_dict.get('doi', None)
            if doi:
                pages = get_pages(doi)
                if pages:
                    logger.info(f'Inserting field pages = {pages}')
                    try:
                        entry.set_field(Field('pages', pages))
                    except TypeError:
                        logger.warning('Update biblatex parser needed (pip install --upgrade biblatexparser --pre)')

        if 'pages' in entry.fields_dict:
            entry.fields_dict['pages'].value = self._standardize_page_numbers(
                entry.fields_dict['pages'].value
            )

    def _standardize_page_numbers(self, pages: str) -> str:
        """Standardize page number format using double hyphens."""
        if not pages:
            return ''
            
        parts = pages.split('-')
        if len(parts) == 1 or len(parts) == 3:
            return pages
        elif len(parts) >= 2:
            return f"{parts[0]}--{parts[-1]}"
        elif r'{\textendash}' in pages:
            return pages.replace(r'{\textendash}', '--')
            
        return pages

    def print_stats(self):
        """Print cleaning statistics in color."""
        print(
            f'{Style.BRIGHT}'
            f'{Fore.GREEN}Parsed: {self.stats["n_parsed"]}\n'
            f'{Fore.YELLOW}Cleaned: {self.stats["n_cleaned"]}\n'
            f'{Fore.MAGENTA}Abbreviated: {self.stats["n_abbreviated"]}\n'
            f'{Fore.RED}Failed: {len(self.errors)}'
            f'{Style.RESET_ALL}'
        )

        if self.errors:
            print('\nEntries that produced errors:\n')
            for err in self.errors:
                logger.info('* * * * * * * * * * * * * * * *')
                for key in self.REQUIRED_KEYS:
                    if key not in err.fields_dict:
                        logger.info(f'{Fore.RED}{titlecase(key)}{Style.RESET_ALL}: -')
                    else:
                        logger.info(f'{titlecase(key)}: {Style.BRIGHT}{err.fields_dict[key].value}')
