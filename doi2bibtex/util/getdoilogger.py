import logging
from rich.logging import RichHandler

def return_logger(_name, **kwargs):
    if kwargs.get('root', False):
        logger = logging.getLogger(_name)
        rich_handler = RichHandler(rich_tracebacks=True, show_path=False, show_time=False)
        rich_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(rich_handler)
        logger.setLevel(getattr(logging, kwargs.get('loglevel', 'INFO').upper()))
    else:
        logger = logging.getLogger(f'doi2bib.{_name}')
    return logger
