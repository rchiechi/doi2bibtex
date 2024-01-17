import os
import re
import mmap
from .getlogger import return_logger

# https://www.crossref.org/blog/dois-and-matching-regular-expressions/

DOIREGEX = [re.compile(b'10\\.\\d{4,9}/[-._;()/:A-Z0-9]+'),
            # re.compile(b'10.1002/[^\\s]+'),
            re.compile(b'10\\.1002/[^,\\s\\[\\]]+'),
            re.compile(b'10\\.\\d{4}/\\d+-\\d+X?(\\d+)\\d+<[\\d\\w]+:[\\d\\w]*>\\d+.\\d+.\\w+;\\d'),
            re.compile(b'10\\.1021/\\w\\w\\d++[A-Za-z]?'),
            re.compile(b'10\\.1207/[\\w\\d]+\\&\\d+_\\d+')]

logger = return_logger(__name__)

def find_doi(_str: str):
    if isinstance(_str, str):
        _str = bytes(_str, encoding='utf-8')
    if len(_str) < 255 and os.path.exists(_str):
        logger.debug(f'Searching file {_str} for dois')
        return find_doi_in_file(_str)
    logger.debug('Searching string for dois')
    return find_doi_in_bytearray(_str)

def find_doi_in_bytearray(textstring: bytearray):
    dois = []
    for regex in DOIREGEX:
        for _m in re.findall(regex, textstring):
            logger.debug(f"Found doi {_m}")
            if _m in dois:
                logger.warn(f"Skipping duplicate DOI {_m}")
            else:
                dois.append(_m)
    return dois

def find_doi_in_file(fn):
    with open(fn, 'r+b') as fh:
        return find_doi_in_bytearray(mmap.mmap(fh.fileno(), 0))