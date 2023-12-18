import sys
import argparse

OUTPUTCMDS = ('bibtexdb', 'html', 'clipboard', 'textfile')

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help(sys.stderr)
        sys.exit(2)

desc = '''
        A python script for interacting with DOIs and bibtex.
       '''

epilog= '''
        Invoke a subcommand with -h to see options specific to that command.
        '''

parser = MyParser(description=desc, epilog=epilog,
                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--dois', metavar='dois-to-parse', type=str, nargs='*', default=[],
                    help='DOIs to parse.')
parser.add_argument('--doifile', metavar='find-dois-in-file', type=str,
                    help='Search a text file for dois.')
parser.add_argument('--loglevel', default='warning', choices=('info', 'warning', 'error', 'debug'),
                    help="Set the logging level.")
parser.add_argument('--refresh', action='store_true', default=False,
                    help="Refresh cached journal list.")
parser.add_argument('--database', type=str,
                    default='https://raw.githubusercontent.com/JabRef/'
                            'abbrv.jabref.org/master/journals/journal_abbreviations_acs.csv',
                    help="Databse of journal abbreviations.")
parser.add_argument('--custom', action='append', default=[],
                    help="Custom abbreviations separated by equal signs, e.g., -c 'Journal of Kittens;J. Kitt.'"
                         "You can call this argument more than once. These will be cached.")

subparsers = parser.add_subparsers(help='sub-command help', required=True, dest='outputmode',
                                   description='Options specific to the selected output mode.')

subparser_bibtexdb = subparsers.add_parser('bibtexdb', help='Write output to a bibtex databse')


subparser_bibtexdb.add_argument('--bibtexfile', type=str,
                    help='A bibtex database to read/write from.')
subparser_bibtexdb.add_argument('--clean', action='store_true', default=False,
                    help="Clean bibtex db entries (implies dedupe).")
subparser_bibtexdb.add_argument('--dedupe', action='store_true', default=False,
                    help='Dedupe the bibtex library.')

subparser_html = subparsers.add_parser('html', help='Write output to HTML.')
subparser_html.add_argument('-o', '--out', metavar='output file', type=str,
                            help='File to write to. Prints to stdout if not provided.')

subparser_clipboard = subparsers.add_parser('clipboard', help='Copy output to clipboard.')

subparser_textfile = subparsers.add_parser('textfile', help='Write output to a standard text file.')
subparser_textfile.add_argument('-o', '--out', metavar='output file', type=str,
                                help='File to write to (defaults to input doi file, if provided).')
subparser_textfile.add_argument('--replace', action='store_true', default=False,
                    help="Replace DOIs in source document with \autocite{@key}.")
subparser_textfile.add_argument('--trim', nargs=2, default=['[',']'],
                    help="Trim these two characters surrounding DOIs on replace e.g., square braces from [DOI].")
subparser_textfile.add_argument('--citecmd', type=str, default='autocite',
                    help='Citekey to use when replacing DOIs.')


opts = parser.parse_args()
if opts.clean:
    opts.dedue = True
if opts.outputmode == 'textfile':
    if opts.doifile and not opts.out:
        opts.out = opts.doifile
