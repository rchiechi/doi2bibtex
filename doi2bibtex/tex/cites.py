import re
from pathlib import Path
import shutil
from colorama import Fore, Style
import doi2bibtex.interact as interact
from doi2bibtex.bibtex.read import load_bib
from doi2bibtex.bibtex.dedupe import dedupe_bib_library
from doi2bibtex.output.bibtexdb import write_bib


def check_tex_cites(tex_files, bib_database, use_llm=False, llm_model=None):
    """
    Check the entire bibtextdb for duplicates, consolidate them,
    and then update the .tex files to use the canonical citation keys.
    """
    print(f"Reading BibTeX database: {bib_database}")
    bib_library = load_bib(bib_database)

    print("Checking for duplicate entries in the BibTeX database...")
    consolidated_library, key_map = dedupe_bib_library(
        bib_library, use_llm=use_llm, llm_model=llm_model
    )

    if not key_map:
        print("No duplicate citations found or no changes were made.")
        return

    print("\nUpdating .tex files with canonical citation keys...")
    for tex_file in tex_files:
        print(f"  - Processing {tex_file}")
        file_path = Path(tex_file)
        try:
            _backup = f'{tex_file}.bak'
            print(f"    {Style.BRIGHT}{Fore.YELLOW}Backing up {Fore.CYAN}{tex_file}{Fore.YELLOW} as {Fore.CYAN}{_backup}{Style.RESET_ALL}")
            shutil.copy(tex_file, _backup)

            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            for old_key, new_key in key_map.items():
                # Use regex to replace keys within \cite commands to be safer.
                # This looks for the key as a whole word, potentially followed by a comma or whitespace.
                content = re.sub(r'(\{|,)\s*' + re.escape(old_key) + r'\s*(?=[,}])', r'\g<1>' + new_key, content)

            if content != original_content:
                file_path.write_text(content, encoding='utf-8')
                print(f"    {Fore.GREEN}Updated citations in {tex_file}{Style.RESET_ALL}")
            else:
                print(f"    No instances of duplicate keys found in {tex_file}.")

        except Exception as e:
            print(f"    {Fore.RED}Error processing {tex_file}: {e}{Style.RESET_ALL}")

    print()
    if interact.ask(f"Save the consolidated library back to {bib_database}?"):
        write_bib(consolidated_library, bib_database)

    print("Done.")
