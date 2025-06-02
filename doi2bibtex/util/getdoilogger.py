import logging

def return_logger(_name, **kwargs):
    if kwargs.get('root', False):
        logger = logging.getLogger(_name)
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(logging.Formatter("%(name)s:[%(levelname)-5.5s] %(message)s"))
        logger.addHandler(streamHandler)
        logger.setLevel(getattr(logging, kwargs.get('loglevel', 'INFO').upper()))
    else:
        logger = logging.getLogger(f'doi2bib.{_name}')
    return logger