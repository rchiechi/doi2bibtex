from waitress import serve
from . import doi2bibtex

def web_server(addr, port):
    serve(doi2bibtex.app, host=addr, port=port)