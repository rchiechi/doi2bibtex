from rich.console import Console

console = Console()

def ask_yes_no(msg: str) -> bool:
    '''Ask user a yes/no question'''
    console.print(f"[bold white]{msg}[/bold white]")
    answer = ''
    while answer.lower() not in ('y','n','yes','no'):
        answer = input('y/n: ')
    if answer.lower() in ('y', 'yes'):
        return True
    return False

def ask_which_one_to_keep(entries):
    """
    Given a list of duplicate entries, asks the user which one to keep.
    Returns the key of the chosen entry.
    """
    console.print('\t\t# # #')
    dupelist = {str(i + 1): entry for i, entry in enumerate(entries)}

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
        return dupelist[keep].key
    
    # If the user chooses to keep all, we'll just return the first one as the "canonical" key for this session.
    # The calling function can then decide how to handle this (e.g., by not creating a key_map entry).
    return entries[0].key