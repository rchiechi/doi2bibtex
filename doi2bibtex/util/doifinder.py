import os
import re
import mmap
from urllib.parse import urlparse, unquote
from .getdoilogger import return_logger

# https://www.crossref.org/blog/dois-and-matching-regular-expressions/

DOIREGEX = [re.compile(b'10\\.\\d{4,9}/[-._;()/:A-Za-z0-9]+'),
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
            if _m not in dois:
                dois.append(_m)
    return dois

def find_doi_in_file(fn):
    with open(fn, 'r+b') as fh:
        return find_doi_in_bytearray(mmap.mmap(fh.fileno(), 0))

def parse_doi_from_url(input_string: str) -> str | None:
        """
        Extract a DOI from a URL or return a raw DOI as-is.
        
        Handles:
        - Raw DOIs (e.g., "10.1038/nrd1799")
        - URL-encoded DOIs (e.g., "https://doi.org/10.1038%2Fnrd1799")
        - Various DOI resolver URLs (doi.org, dx.doi.org, etc.)
        - doi: URI scheme (e.g., "doi:10.1038/nrd1799")
        
        Args:
            input_string: A DOI string or URL containing a DOI
            
        Returns:
            The extracted/decoded DOI string, or None if no valid DOI found
        """
        
        if not input_string or not isinstance(input_string, str):
            return input_string
        
        input_string = input_string.strip()
        
        # URL-decode the string to handle encoded characters
        decoded = unquote(input_string)
        
        # Strip common URI schemes/prefixes to get to the DOI
        lower = decoded.lower()
        if lower.startswith('doi:'):
            decoded = decoded[4:].strip()
        elif lower.startswith(('http://', 'https://')):
            try:
                parsed = urlparse(decoded)
                # Extract path, strip leading slash
                decoded = parsed.path.lstrip('/')
                # Append query if present (some URLs embed DOI there)
                if parsed.query:
                    decoded += '?' + parsed.query
            except Exception:
                pass
        
        # Use existing function to find DOIs in the decoded string
        logger.debug(f'Parsing DOI from: {decoded}')
        dois = find_doi_in_bytearray(bytes(decoded, encoding='utf-8'))
        
        if dois:
            # Return first match, decoded to string
            return dois[0].decode('utf-8')
        
        return None