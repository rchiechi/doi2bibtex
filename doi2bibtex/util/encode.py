import os
from pylatexenc.latexencode import UnicodeToLatexEncoder
from .getdoilogger import return_logger

logger = return_logger(__name__)

class LatexEncoder:
    
    def __init__(self):
        self.parser = UnicodeToLatexEncoder(non_ascii_only=True)
    
    def parsefile_inplace(self, fn):
        _ascii = self.parsefile(fn)
        if _ascii:
            with open(fn, 'w') as fh:
                fh.write(_ascii)

    def parsefile(self, fn):
        _ascii = ''
        if os.path.exists(fn):
            with open(fn) as fh:
                _ascii = self.parser.unicode_to_latex(fh.read())
        else:
            logger.error("%s does not exist.", fn)
        return _ascii
    
    def parsestring(self, chrs):
        return self.parser.unicode_to_latex(chrs)