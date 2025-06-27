from collections import defaultdict
from itertools import combinations
from colorama import Fore,Style,Back
from doi2bibtex.util.getdoilogger import return_logger as getlogger
from doi2bibtex.llm.base import get_llm_provider, save_llm_config, load_llm_config
from Levenshtein import ratio

logger = getlogger(__name__)


def _format_entry_for_llm(entry):
    """Formats a bibtex entry into a simple string for the LLM prompt."""
    details = [f"- Type: {entry.entry_type}", f"- Key: {entry.key}"]
    for key, value in entry.fields_dict.items():
        details.append(f"- {key.capitalize()}: {value.value}")
    return "\n".join(details)

def _get_llm_verdict(llm_provider, entry1, entry2):
    """Gets a verdict from the LLM on whether two entries are duplicates."""
    prompt = f"""You are a bibliographic assistant. Your task is to determine if the following two BibTeX entries refer to the same publication. Consider variations in title, author lists, page numbers, and publication venue (e.g., preprint vs. final journal article).

Respond with only the word 'YES' or 'NO'.

Entry 1:
{_format_entry_for_llm(entry1)}

Entry 2:
{_format_entry_for_llm(entry2)}

Are these two entries for the same publication?"""
    
    response = llm_provider.get_completion(prompt)
    if response:
        return response.strip().upper() == 'YES'
    return False

def dedupe_bib_library(library, use_llm=False, llm_model=None):
    '''Check for duplicate bibtex entries'''
    logger.debug("Starting dedupe run")
    for entry in library.failed_blocks:
        print(f"{Style.BRIGHT}Failed:{Fore.RED} {entry.key}")

    dupe_groups = []

    if use_llm:
        print("Using LLM for deduplication (this may take a while)...")
        if llm_model:
            config = load_llm_config()
            config['default_model'] = llm_model
            save_llm_config(config)
            
        llm_provider = get_llm_provider(llm_model)
        if not llm_provider:
            print("Could not initialize LLM provider. Falling back to standard deduplication.")
            use_llm = False

    if use_llm:
        # LLM-based deduplication
        # Pre-filtering: Group by year and similar journal title
        candidate_groups = defaultdict(list)
        for entry in library.entries:
            year_field = entry.fields_dict.get('year')
            journal_field = entry.fields_dict.get('journal')
            if year_field and journal_field:
                year = year_field.value
                journal = journal_field.value
                # Simple key for grouping
                candidate_key = (year, journal[:5].lower())
                candidate_groups[candidate_key].append(entry.key)
        
        processed_pairs = set()
        llm_dupe_keys = []
        for group in candidate_groups.values():
            if len(group) < 2:
                continue
            for key1, key2 in combinations(group, 2):
                pair = tuple(sorted((key1, key2)))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)

                entry1 = library.entries_dict[key1]
                entry2 = library.entries_dict[key2]

                # Additional check: title similarity
                title1_field = entry1.fields_dict.get('title')
                title2_field = entry2.fields_dict.get('title')
                if title1_field and title2_field:
                    title1 = title1_field.value
                    title2 = title2_field.value
                    if ratio(title1, title2) > 0.8:
                        if _get_llm_verdict(llm_provider, entry1, entry2):
                            llm_dupe_keys.append(key1)
                            llm_dupe_keys.append(key2)
        
        if llm_dupe_keys:
            # This is a simplified grouping. A more robust implementation
            # would create distinct groups of duplicates.
            dupe_groups.append(list(set(llm_dupe_keys)))

    else:
        # Standard, non-LLM deduplication
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

            if _doi:
                dupe_key = ('doi', _doi)
            elif _p and _v and _j:
                dupe_key = ('pvj', _p, _v, _j)
            else:
                continue
            dupe_candidates[dupe_key].append(_key)
        
        dupe_groups = [keys for keys in dupe_candidates.values() if len(keys) > 1]

    if dupe_groups:
        return dodedupe(library, dupe_groups)
    
    print("No potential duplicates found.")
    return library, {}


def dodedupe(library, dupe_groups):
    '''Function that does the actual deduping'''
    print('\nPossible dupes found:\n')
    
    processed_keys = set()
    key_map = {}
    
    for group in dupe_groups:
        if all(key in processed_keys for key in group):
            continue

        print('\t\t# # #')
        
        dupelist = {}
        i = 1
        for key in group:
            if key not in processed_keys:
                dupelist[str(i)] = library.entries_dict[key]
                i += 1

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
                    key_map[key_to_delete] = key_to_keep
            processed_keys.add(key_to_keep)
        else:
            print(f'{Fore.GREEN}Keeping all in this group.')
            for entry in dupelist.values():
                processed_keys.add(entry.key)

    return library, key_map
