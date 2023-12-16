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
parser.add_argument('--replace', action='store_true', default=False,
        help="Replace DOIs in source document with \autocite{@key}.")
parser.add_argument('--trim', action='append', default=[],
        help="Trim these characters from DOIs on replace e.g., square braces from [DOI].")
parser.add_argument('--bibtexfile', type=str,
        help='A bibtex database to read/write from.')
parser.add_argument('--dedupe', action='store_true', default=False,
        help='Dedupe the bibtex library.')
parser.add_argument('--loglevel', default='info', choices=('info', 'warn', 'error', 'debug'),
        help="Set the logging level.")
parser.add_argument('--refresh', action='store_true', default=False,
    help="Refresh cached journal list.")
parser.add_argument('--database', type=str,
    default='https://raw.githubusercontent.com/JabRef/'\
        +'abbrv.jabref.org/master/journals/journal_abbreviations_acs.csv',
    help="Databse of journal abbreviations.")
parser.add_argument('--custom', action='append', default=[],
        help="Cust abbreviations separated by equal signs, e.g., -c 'Journal of Kittens;J. Kitt.'\
        You can call this argument more than once. These will be cached.")

opts = parser.parse_args()
