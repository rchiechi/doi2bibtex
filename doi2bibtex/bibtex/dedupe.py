from collections import defaultdict
from colorama import Fore,Style,Back
from doi2bibtex.util.getdoilogger import return_logger as getlogger
from doi2bibtex.llm.base import get_llm_provider, get_llm_config

logger = getlogger(__name__)


def dedupe_bib_library(library, use_llm=False):
    '''Check for duplicate bibtex entries'''
    logger.debug("Starting dedupe run")
    for entry in library.failed_blocks:
        print(f"{Style.BRIGHT}Failed:{Fore.RED} {entry.key}")

    if use_llm:
        print("Using LLM for deduplication...")
        config = get_llm_config()
        if not config:
            print("Could not load LLM config. Falling back to standard deduplication.")
            use_llm = False
        else:
            llm_provider = get_llm_provider(config.get('llm', {}))
            if not llm_provider:
                print("Could not initialize LLM provider. Falling back to standard deduplication.")
                use_llm = False

    if use_llm:
        # This is a placeholder for the LLM-based deduplication logic.
        # It would involve creating prompts to ask the LLM if two entries are duplicates
        # and then processing the responses.
        print("LLM-based deduplication is not yet fully implemented.")
        # For now, we'll just fall back to the standard method.
    
    # Create a dictionary to hold potential duplicates.
    # The key will be a tuple of (doi) or (pages, volume, journal)
    # The value will be a list of entry keys that match.
    dupe_candidates = defaultdict(list)
    
    for entry in library.entries:
        _key = entry.key
        _p, _v, _j, _doi = '', '', '', ''
        
        fields_lower = {k.lower(): v for k, v in entry.fields_dict.items()}
        
        if 'pages' in fields_lower:
            _p = fields_lower['pages'].value.split('-')[0].strip().strip('-')
        elif 'page' in fields_lower:
            _p = fields_lower['page'].value.split('-')[0].strip().strip('-')
        
        if 'journal' in fields_lower:
            _j = fields_lower['journal'].value
        
        if 'volume' in fields_lower:
            _v = fields_lower['volume'].value
            
        if 'doi' in fields_lower:
            _doi = fields_lower['doi'].value

        # Prefer DOI for matching, fall back to page/volume/journal
        if _doi:
            dupe_key = ('doi', _doi)
        elif _p and _v and _j:
            dupe_key = ('pvj', _p, _v, _j)
        else:
            logger.warning(f'Cannot build a reliable dedupe key for {entry.key}')
            continue
            
        dupe_candidates[dupe_key].append(_key)

    # Filter for actual duplicates (groups with more than one entry)
    dupe_groups = [keys for keys in dupe_candidates.values() if len(keys) > 1]

    if dupe_groups:
        return dodedupe(library, dupe_groups)
    
    print("No potential duplicates found.")
    return library


def dodedupe(library, dupe_groups):
    '''Function that does the actual deduping'''
    print('\nPossible dupes found:\n')
    
    processed_keys = set()
    
    for group in dupe_groups:
        # Skip if all keys in this group have been processed already
        if all(key in processed_keys for key in group):
            continue

        print('\t\t# # #')
        
        # Build a numbered list of entries for user selection
        dupelist = {}
        i = 1
        for key in group:
            if key not in processed_keys:
                dupelist[str(i)] = library.entries_dict[key]
                i += 1

        # If there's less than 2 entries, it's not a duplicate group anymore
        if len(dupelist) < 2:
            continue

        for n, entry in dupelist.items():
            try:
                print(f'{Style.BRIGHT}{Fore.YELLOW}{n}):   {Fore.CYAN}{entry.key}')
                journal = entry.fields_dict.get('journal', 'N/A')
                volume = entry.fields_dict.get('volume', 'N/A')
                pages = entry.fields_dict.get('pages', 'N/A')
                print(f'{Fore.YELLOW}Journal: {Style.BRIGHT}{Fore.WHITE}{journal.value if hasattr(journal, "value") else journal}')
                print(f'{Fore.YELLOW}Volume: {Style.BRIGHT}{Fore.WHITE}{volume.value if hasattr(volume, "value") else volume}')
                print(f'{Fore.YELLOW}Pages: {Style.BRIGHT}{Fore.WHITE}{pages.value if hasattr(pages, "value") else pages}\n')
            except Exception as e:
                print(f"Error parsing entry: {e}")

        keep = input('Keep which one? (Enter number, or anything else to keep all) ')
        
        if keep in dupelist:
            key_to_keep = dupelist[keep].key
            print(f'{Style.BRIGHT}{Fore.GREEN}Keeping {key_to_keep}.')
            
            for n, entry_to_delete in dupelist.items():
                if n != keep:
                    key_to_delete = entry_to_delete.key
                    print(f'{Fore.YELLOW}{Back.RED}Deleting{Style.RESET_ALL} {Style.BRIGHT}{Fore.RED}{key_to_delete}')
                    library.remove(library.entries_dict[key_to_delete])
                    processed_keys.add(key_to_delete)
            processed_keys.add(key_to_keep)
        else:
            print(f'{Fore.GREEN}Keeping all in this group.')
            # Mark all as processed so we don't ask again
            for entry in dupelist.values():
                processed_keys.add(entry.key)

    return library
