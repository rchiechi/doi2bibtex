import re
from collections import defaultdict
from pathlib import Path

from doi2bibtex.bibtex.dedupe import dedupe_bib_library
from doi2bibtex.bibtex.read import load_bib
from doi2bibtex.interact.ask import ask_which_one_to_keep


def find_citation_keys(tex_files):
    """Find all citation keys in a list of .tex files."""
    citation_keys = set()
    cite_pattern = re.compile(r'\\cite[t|p|year|author|full|yearpar|text|parencites|footcite|footcitetext|textcite|smartcite|supercite|autocite|parencite|footfullcite]*\[.*?\]*\{(.*?)\}')

    for tex_file in tex_files:
        with open(tex_file, 'r', encoding='utf-8') as f:
            content = f.read()
            matches = cite_pattern.findall(content)
            for group in matches:
                keys = [key.strip() for key in group.split(',')]
                citation_keys.update(keys)
    return list(citation_keys)


def check_tex_cites(tex_files, bib_database, use_llm=False):
    """
    Check .tex files for duplicate citations and consolidate them.
    """
    print(f"Reading BibTeX database: {bib_database}")
    bib_library = load_bib(bib_database)

    print("Finding all citation keys in .tex files...")
    all_cite_keys = find_citation_keys(tex_files)
    
    # Create a temporary library with only the cited entries
    cited_library = load_bib('')
    cited_library.entries = [entry for entry in bib_library.entries if entry.key in all_cite_keys]
    
    print("Checking for duplicate entries in the cited library...")
    # This function now needs to be adapted to return the dupe groups
    # and not perform the interactive deduplication itself.
    # For now, we'll assume a similar structure and call a modified or new function.
    
    # Let's simulate the dupe finding part from the refactored dedupe.py
    dupe_candidates = defaultdict(list)
    for entry in cited_library.entries:
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

    if not dupe_groups:
        print("No duplicate citations found in the .tex files.")
        return

    print("Found duplicate citations. Consolidating...")
    key_map = {}
    for group in dupe_groups:
        entries = [bib_library.entries_dict[key] for key in group]
        chosen_key = ask_which_one_to_keep(entries)
        for key in group:
            if key != chosen_key:
                key_map[key] = chosen_key

    if not key_map:
        print("No changes to make.")
        return

    # Replace duplicate keys in .tex files
    for tex_file in tex_files:
        print(f"Updating citations in {tex_file}...")
        file_path = Path(tex_file)
        content = file_path.read_text(encoding='utf-8')
        
        # This is a simplistic replacement and might not handle all edge cases.
        # A more robust solution would use regex to replace keys within \cite commands.
        for old_key, new_key in key_map.items():
            # Using word boundaries to avoid replacing parts of other keys
            content = re.sub(r'\\b' + re.escape(old_key) + r'\\b', new_key, content)
            
        file_path.write_text(content, encoding='utf-8')

    print("Done.")
