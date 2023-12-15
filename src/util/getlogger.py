import logging

def return_logger(_name=None, **kwargs):
    if _name is not None:
        return logging.getLogger(_name)
    logger = logging.getLogger()
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(logging.Formatter("%(name)s:[%(levelname)-5.5s] %(message)s"))
    logger.addHandler(streamHandler)
    logger.setLevel(getattr(logging, kwargs.get('loglevel', 'INFO').upper()))
    return logger