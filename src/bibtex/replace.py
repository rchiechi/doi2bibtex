# import os
import re
import mmap
from util import getlogger


logger = getlogger(__name__)


def replace_doi_in_file(fn, library, citecmd, trim=[]):
    citecmd = bytes(citecmd.strip('\\'), encoding='utf-8')
    trim = [bytes(c, encoding='utf-8') for c in trim]
    doimap = {}
    for entry in library.entries:
        for _key in ('doi', 'DOI'):
            try:
                doimap[bytes(entry.fields_dict[_key].value, encoding='utf-8')] = bytes(entry.key, encoding='utf-8')
            except KeyError:
                continue
    logger.debug(f'doimap: {doimap}')
    replacements = _replace_with_trim(fn, doimap, trim)
    with open(fn, 'r+b') as fh:
        _file = fh.read()
    for rep in replacements:
        if rep[0].replace(b' ',b'')[1:4] != b'10.':
            logger.warn(f'Not replacing non-doi {rep[0]}')
            continue
        _citecmd = rep[1].replace(trim[0], b'\\'+citecmd+b'{').replace(trim[1], b'}')
        _file = _file.replace(rep[0], _citecmd)
        print(f'{rep[0]} -> {_citecmd}')
    return _file


def _replace_with_trim(fn, doimap, trim):
    if any(c for c in [b'[', b'}', b')'] if c in trim):
        regex = re.compile(b'\\'+trim[0]+b'.+?'+b'\\'+trim[1])
    else:
        regex = re.compile(trim[0]+b'.+?'+trim[1])
    replacements = []
    with open(fn, 'r+b') as fh:
        _file = mmap.mmap(fh.fileno(), 0)
        for _m in re.findall(regex, _file):
            _r = _m
            logger.debug(f"considering {_m}")
            for doi in doimap:
                if not doi.upper() in _m.upper():
                    continue
                _r = _r.replace(doi, doimap[doi]).replace(doi.lower(), doimap[doi]).replace(doi.upper(), doimap[doi]).replace(b' ',b'')
            replacements.append([_m, _r])
    return replacements
