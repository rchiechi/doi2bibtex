import re
from pathlib import Path
import shutil
from rich.console import Console
import doi2bibtex.interact as interact
from doi2bibtex.bibtex.read import load_bib
from doi2bibtex.bibtex.dedupe import dedupe_bib_library
from doi2bibtex.output.bibtexdb import write_bib

console = Console()

def check_tex_cites(tex_files, bib_database, use_llm=False, llm_model=None):
    """
    Check the entire bibtextdb for duplicates, consolidate them,
    and then update the .tex files to use the canonical citation keys.
    """
    console.print(f"Reading BibTeX database: {bib_database}")
    bib_library = load_bib(bib_database)

    console.print("Checking for duplicate entries in the BibTeX database...")
    consolidated_library, key_map = dedupe_bib_library(
        bib_library, use_llm=use_llm, llm_model=llm_model
    )

    if not key_map:
        console.print("No duplicate citations found or no changes were made.")
        return

    console.print("\nUpdating .tex files with canonical citation keys...")
    for tex_file in tex_files:
        console.print(f"  - Processing {tex_file}")
        file_path = Path(tex_file)
        try:
            _backup = f'{tex_file}.bak'
            console.print(f"    [bold yellow]Backing up [cyan]{tex_file}[/cyan] as [cyan]{_backup}[/cyan][/bold yellow]")
            shutil.copy(tex_file, _backup)

            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            for old_key, new_key in key_map.items():
                # Use regex to replace keys within \cite commands to be safer.
                # This looks for the key as a whole word, potentially followed by a comma or whitespace.
                content = re.sub(r'(\{|,)\s*' + re.escape(old_key) + r'\s*(?=[,}])', r'\g<1>' + new_key, content)

            if content != original_content:
                file_path.write_text(content, encoding='utf-8')
                console.print(f"    [green]Updated citations in {tex_file}[/green]")
            else:
                console.print(f"    No instances of duplicate keys found in {tex_file}.")

        except Exception as e:
            console.print(f"    [red]Error processing {tex_file}: {e}[/red]")

    console.print()
    if interact.ask(f"Save the consolidated library back to {bib_database}?"):
        write_bib(consolidated_library, bib_database)

    console.print("Done.")