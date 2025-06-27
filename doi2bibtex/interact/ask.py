from colorama import Fore, Style

def ask_yes_no(msg: str) -> bool:
    '''Ask user a yes/no question'''
    print(f"{Style.BRIGHT}{Fore.WHITE}{msg}")
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
    print('\t\t# # #')
    dupelist = {str(i + 1): entry for i, entry in enumerate(entries)}

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
        return dupelist[keep].key
    
    # If the user chooses to keep all, we'll just return the first one as the "canonical" key for this session.
    # The calling function can then decide how to handle this (e.g., by not creating a key_map entry).
    return entries[0].key
