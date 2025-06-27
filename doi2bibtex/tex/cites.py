import re
from collections import defaultdict
from pathlib import Path

from doi2bibtex.bibtex.read import load_bib
from doi2bibtex.bibtex.dedupe import dedupe_bib_library
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


def check_tex_cites(tex_files, bib_database, use_llm=False, llm_model=None):
    """
    Check .tex files for duplicate citations and consolidate them.
    """
    print(f"Reading BibTeX database: {bib_database}")
    bib_library = load_bib(bib_database)
    original_keys = {entry.key for entry in bib_library.entries}

    print("Finding all citation keys in .tex files...")
    all_cite_keys = find_citation_keys(tex_files)
    
    # Create a temporary library with only the cited entries
    cited_library = load_bib('')
    for entry in bib_library.entries:
        if entry.key in all_cite_keys:
            cited_library.add(entry)
    
    print("Checking for duplicate entries in the cited library...")
    consolidated_library, key_map = dedupe_bib_library(cited_library, use_llm=use_llm, llm_model=llm_model)

    if not key_map:
        print("No changes to make to .tex files.")
        return

    # Replace duplicate keys in .tex files
    for tex_file in tex_files:
        print(f"Updating citations in {tex_file}...")
        file_path = Path(tex_file)
        content = file_path.read_text(encoding='utf-8')
        
        for old_key, new_key in key_map.items():
            # Using word boundaries to avoid replacing parts of other keys
            content = re.sub(r'\b' + re.escape(old_key) + r'\b', new_key, content)
            
        file_path.write_text(content, encoding='utf-8')

    print("Done.")
