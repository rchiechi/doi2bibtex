from collections import defaultdict
from itertools import combinations
from rich.console import Console
from doi2bibtex.util.getdoilogger import return_logger as getlogger
from doi2bibtex.llm.config import get_llm_provider, save_llm_config, load_llm_config
from Levenshtein import ratio

logger = getlogger(__name__)
console = Console()

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
        console.print(f"[bold]Failed:[red] {entry.key}")

    dupe_groups = []

    if use_llm:
        console.print("Using LLM for deduplication (this may take a while)...")
        if llm_model:
            config = load_llm_config()
            config['default_model'] = llm_model
            save_llm_config(config)
            
        llm_provider = get_llm_provider(llm_model)
        if not llm_provider:
            console.print("Could not initialize LLM provider. Falling back to standard deduplication.")
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
        
        llm_dupe_pairs = []
        for group in candidate_groups.values():
            if len(group) < 2:
                continue
            for key1, key2 in combinations(group, 2):
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
                            llm_dupe_pairs.append((key1, key2))
        
        # Find connected components to group the duplicates correctly
        adj = defaultdict(list)
        for u, v in llm_dupe_pairs:
            adj[u].append(v)
            adj[v].append(u)

        visited = set()
        for key in adj:
            if key not in visited:
                component = []
                q = [key]
                visited.add(key)
                while q:
                    curr = q.pop(0)
                    component.append(curr)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            q.append(neighbor)
                dupe_groups.append(component)

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
        
        dupe_groups.extend([keys for keys in dupe_candidates.values() if len(keys) > 1])

    if dupe_groups:
        return dodedupe(library, dupe_groups)
    
    console.print("No potential duplicates found.")
    return library, {}


def dodedupe(library, dupe_groups):
    '''Function that does the actual deduping'''
    console.print('\nPossible dupes found:\n')
    
    processed_keys = set()
    key_map = {}
    
    for group in dupe_groups:
        if all(key in processed_keys for key in group):
            continue

        console.print('\t\t# # #')
        
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
                console.print(f'[bold yellow]{n}):[/bold yellow]   [cyan]{entry.key}[/cyan]')
                journal = entry.fields_dict.get('journal', 'N/A')
                volume = entry.fields_dict.get('volume', 'N/A')
                pages = entry.fields_dict.get('pages', 'N/A')
                console.print(f'[yellow]Journal: [bold white]{journal.value if hasattr(journal, "value") else journal}[/bold white]')
                console.print(f'[yellow]Volume: [bold white]{volume.value if hasattr(volume, "value") else volume}[/bold white]')
                console.print(f'[yellow]Pages: [bold white]{pages.value if hasattr(pages, "value") else pages}[/bold white]\n')
            except Exception as e:
                console.print(f"Error parsing entry: {e}")

        keep = input('Keep which one? (Enter number, or anything else to keep all) ')
        
        if keep in dupelist:
            key_to_keep = dupelist[keep].key
            console.print(f'[bold green]Keeping {key_to_keep}.[/bold green]')
            
            for n, entry_to_delete in dupelist.items():
                if n != keep:
                    key_to_delete = entry_to_delete.key
                    console.print(f'[yellow on red]Deleting[/yellow on red] [bold red]{key_to_delete}[/bold red]')
                    library.remove(library.entries_dict[key_to_delete])
                    processed_keys.add(key_to_delete)
                    key_map[key_to_delete] = key_to_keep
            processed_keys.add(key_to_keep)
        else:
            console.print('[green]Keeping all in this group.[/green]')
            for entry in dupelist.values():
                processed_keys.add(entry.key)

    return library, key_map