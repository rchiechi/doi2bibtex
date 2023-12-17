# import os
import re
import mmap
# import bibtexparser
# import bibtexparser.middlewares as m
# from .month import MonthIntStrMiddleware
from util import getlogger


logger = getlogger(__name__)

# layers = [
#     m.LatexDecodingMiddleware(True),
#     m.MonthIntMiddleware(True)
# ]
# 
# def load_bib(bibtex, dedupe=False):
#     logger.debug(f"Loading bib with dedupe={dedupe}")
#     if os.path.exists(bibtex):
#         library = bibtexparser.parse_file(bibtex, append_middleware=layers)
#     else:
#         library = bibtexparser.parse_string(bibtex, append_middleware=layers)
#     if dedupe:
#         return dedupe_bib_library(library)
#     return library
# 
# import os
# import re
# import mmap
# from .getlogger import return_logger
# 
# # https://www.crossref.org/blog/dois-and-matching-regular-expressions/
# 
# DOIREGEX = [re.compile(b'10.\d{4,9}/[-._;()/:A-Z0-9]+'),
#             re.compile(b'10.1002/[^\s]+'),
#             re.compile(b'10.\d{4}/\d+-\d+X?(\d+)\d+<[\d\w]+:[\d\w]*>\d+.\d+.\w+;\d'),
#             re.compile(b'10.1021/\w\w\d++'),
#             re.compile(b'10.1207/[\w\d]+\&\d+_\d+')]
# 
# logger = return_logger(__name__)
# 
# def find_doi(_str: str):
#     if isinstance(_str, str):
#         _str = bytes(_str, encoding='utf-8')
#     if len(_str) < 255 and os.path.exists(_str):
#         logger.debug(f'Searching file {_str} for dois')
#         return find_doi_in_file(_str)
#     logger.debug('Searching string for dois')
#     return find_doi_in_bytearray(_str)
# 
# def find_doi_in_bytearray(textstring: bytearray):
#     dois = []
#     for regex in DOIREGEX:
#         for _m in re.findall(regex, textstring):
#             logger.debug(f"Found doi {_m}")
#             dois.append(_m)
#     return dois

def replace_doi_in_file(fn, library, citecmd, trim=[]):
    citecmd = citecmd.strip('\\')
    doimap = {}
    for entry in library.entries:
        try:
            doimap[entry.fields_dict['doi'].value] = entry.key
        except KeyError:
            print(entry.fields_dict.keys())
    _replace_with_trim(fn, doimap, trim)

def _replace_with_trim(fn, doimap, trim):
    regex = re.compile(bytes(trim[0])+b'.*?'+bytes(trim[1]))
    replacemap = []
    with open(fn, 'r+b') as fh:
        _file = mmap.mmap(fh.fileno(), 0)
        for _m in re.findall(regex, _file):
            for doi in doimap:
                print(_m.replace(doi, doimap[doi]))
                
    

def _replace_no_trim(fn, library, citecmd):
    with open(fn, 'r+b') as fh:
        # _file = mmap.mmap(fh.fileno(), 0)
        _file = fh.read()
        for entry in library.entries:
            doi = bytes(entry.field_dict['doi'].value, encoding='utf-8')
            # _citekey = b'\\'+citecmd+b'{'+'}
            # _file.replace(doi, b'\'+citecmd+b'{'+'}
            