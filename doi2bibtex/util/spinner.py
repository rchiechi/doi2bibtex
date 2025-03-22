class Spinner:
    spinner = ('⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷')
    idx = 0
    def __init__(self, prefix=None):
        self.prefix = prefix
    
    async def __aenter__(self):
        # Hide the cursor
        print("\033[?25l", end="", flush=True)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("\033[2K", end="", flush=True)
        print("\033[?25h", end="", flush=True)
        return False
    
    async def update(self):
        print("\r", end="")
        if self.prefix:
            print(f"{self.prefix}: ", end="")
        print(f"{self.spinner[self.idx]}", end="", flush=True)
        if self.idx < len(self.spinner)-1:
            self.idx += 1
        else:
            self.idx = 0
