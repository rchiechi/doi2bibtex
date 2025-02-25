from .overwrite import ask_overwrite
from .ask import ask_yes_no

def overwrite(fn):
    return ask_overwrite(fn)

def ask(msg):
    return ask_yes_no(msg)
