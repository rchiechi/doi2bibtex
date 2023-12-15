import argparse


desc = '''
        A python script for interacting with DOIs and bibtex.
       '''



parser = argparse.ArgumentParser(description=desc,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--dois', metavar='dois-to-parse', type=str, nargs='*', default=[],
        help='DOIs to parse.')
parser.add_argument('--fromfile', metavar='find-dois-in-file', type=str,
        help='Search a text file for dois.')
parser.add_argument('--bibtexfile', type=str,
        help='A bibtex database to read/write from.')
parser.add_argument('--dedupe', action='store_true', default=False,
        help='Dedupe the bibtex library.')
parser.add_argument('--loglevel', default='info', choices=('info', 'warn', 'error', 'debug'),
        help="Set the logging level.")

opts = parser.parse_args()
