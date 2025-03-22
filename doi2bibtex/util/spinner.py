from random import randint

class Spinner:
    spinner = ('⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷')
    colors_fore = (cm.Fore.RED, cm.Fore.GREEN, 
                   cm.Fore.YELLOW, cm.Fore.BLUE, cm.Fore.MAGENTA,
                   cm.Fore.CYAN, cm.Fore.WHITE)
    colors_back = (cm.Back.RED, cm.Back.GREEN, 
                   cm.Back.YELLOW, cm.Back.BLUE, cm.Back.MAGENTA,
                   cm.Back.CYAN, cm.Back.WHITE)
    styles = (cm.Style.DIM, cm.Style.NORMAL, cm.Style.BRIGHT)
    idx = 0
    def __init__(self, prefix=None):
        self.prefix = prefix
    
    async def __aenter__(self):
        # Hide the cursor
        print("\033[?25l", end="", flush=True)
        print(cm.Back.BLACK, end="")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print(cm.Style.RESET_ALL, end="\r")
        print("\033[2K", end="", flush=True)
        print("\033[?25h", end="", flush=True)
        return False
    
    async def update(self):
        print("\r", end="")
        if self.prefix:
            # print(f"{cm.Style.RESET_ALL}{self.prefix}: ", end="")
            for chr in self.prefix:
                print(f"{self.styles[randint(0, len(self.styles)-1)]}", end="")
                print(f"{self.colors_fore[randint(0, len(self.colors_fore)-1)]}", end="")
                print(chr, end="")
        print(f"{cm.Style.RESET_ALL}: ", end="")
        print(f"{self.styles[randint(0, len(self.styles)-1)]}", end="")
        print(f"{self.colors_fore[randint(0, len(self.colors_fore)-1)]}", end="")
        # print(f"{self.colors_back[randint(0, len(self.colors_back)-1)]}", end="")
        print(f"{self.spinner[self.idx]}", end="", flush=True)
        if self.idx < len(self.spinner)-1:
            self.idx += 1
        else:
            self.idx = 0
