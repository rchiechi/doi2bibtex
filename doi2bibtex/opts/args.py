import argcomplete, argparse
import sys

OUTPUTCMDS = ('bibtexdb', 'html', 'clipboard', 'textfile')

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help(sys.stderr)
        sys.exit(2)


desc = '''
        A python script for interacting with DOIs and bibtex.
       '''

epilog = '''
        Invoke a subcommand with -h to see options specific to that command.
        '''

parser = MyParser(description=desc, epilog=epilog,
                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--dois', metavar='dois-to-parse', type=str, default='',
                    help='DOIs to parse, comma-separated. For example --dois \'10.1234/journal1, 10.4567/journal2\'')
parser.add_argument('--doifile', metavar='find-dois-in-file', type=str,
                    help='Search a text file for dois.')
parser.add_argument('--bibtexdb', type=str,
                    help='Bibtexdb to use as input, otherwise create a blank library.')
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
parser.add_argument('--cited', action='store_true', default=False,
                    help="Return the bibliographies of the papers in the input doi(s).")
parser.add_argument('--citing', action='store_true', default=False,
                    help="Return dois that cite the papers in the input doi(s).")
parser.add_argument('--llm-model', type=str, default=None,
                    help="Specify the LLM model to use from config. Updates the default.")

#  Initialize Subparsers
subparsers = parser.add_subparsers(help='sub-command help', required=True, dest='outputmode',
                                   description='Options specific to the selected output mode.')

# # # Bibtexdb subparser options # # #
subparser_bibtexdb = subparsers.add_parser('bibtexdb', help='Write output to a bibtex databse')

subparser_bibtexdb.add_argument('more_dois', type=str, nargs='*', default=[],
                                help='Additional DOIs supplied on the command line.')
subparser_bibtexdb.add_argument('-o', '--out', metavar='output file', type=str,
                                help='File to write to (defaults to input bibtexdb file, if provided).')
subparser_bibtexdb.add_argument('--clean', action='store_true', default=False,
                                help="Clean bibtex db entries (implies dedupe).")
subparser_bibtexdb.add_argument('--dedupe', action='store_true', default=False,
                                help='Dedupe the bibtex library.')
subparser_bibtexdb.add_argument('--llm', action='store_true', default=False,
                                help='Use LLM for deduplication (experimental).')

# # #  HTML subparser options # # #
subparser_html = subparsers.add_parser('html', help='Write output to HTML bibliography.')

subparser_html.add_argument('more_dois', type=str, nargs='*', default=[],
                            help='Additional DOIs supplied on the command line.')
subparser_html.add_argument('-o', '--out', metavar='output file', type=str,
                            help='File to write to. Prints to stdout if not provided.')
subparser_html.add_argument('--nobreaks', action='store_true', default=False,
                            help='Do not insert line breaks for readabiltiy.')
subparser_html.add_argument('-b', '--boldname', type=str, default='',
                            help='Bold this name in HTML output.')

# # #  HTML subparser options # # #
subparser_html = subparsers.add_parser('markdown', help='Write output to markdown bibliography.')

subparser_html.add_argument('more_dois', type=str, nargs='*', default=[],
                            help='Additional DOIs supplied on the command line.')
subparser_html.add_argument('-o', '--out', metavar='output file', type=str,
                            help='File to write to. Prints to stdout if not provided.')
subparser_html.add_argument('-b', '--boldname', type=str, default='',
                            help='Bold this name in markdown output.')

# # #  Text list subparser options # # #
subparser_textlist = subparsers.add_parser('textlist', help='Write output to plain text bibliography.')

subparser_textlist.add_argument('more_dois', type=str, nargs='*', default=[],
                                help='Additional DOIs supplied on the command line.')
subparser_textlist.add_argument('-o', '--out', metavar='output file', type=str,
                                help='File to write to. Prints to stdout if not provided.')
subparser_textlist.add_argument('-b', '--boldname', type=str, default='',
                                help='Add asterisk to this name.')
subparser_textlist.add_argument('-y', '--years', action='store_true', default=False,
                                help='Include years as headers on separate lines.')

# # #  Clipboard subparser options # # #
subparser_clipboard = subparsers.add_parser('clipboard', help='Copy output to clipboard.')

subparser_clipboard.add_argument('more_dois', type=str, nargs='*', default=[],
                                 help='Additional DOIs supplied on the command line.')
subparser_clipboard.add_argument('--stdout', action='store_true', default=False,
                                 help='Write to stdout instead of cliboard.')
subparser_clipboard.add_argument('--noclean', action='store_true', default=False,
                                 help='Do not convert unicode to LaTeX.')

# # #  PDF downloader subparser options # # #
subparser_pdf = subparsers.add_parser('pdf', help='Download a PDF from a doi.')

subparser_pdf.add_argument('more_dois', type=str, nargs='*', default=[],
                                 help='Additional DOIs supplied on the command line.')
subparser_pdf.add_argument('--proxy', type=str, default="http://localhost:3128",
                                 help='Proxy server to use.')
subparser_pdf.add_argument('--mirror', type=str, default="https://sci-hub.se",
                                  help='Mirror to use to resolve PDFs.')
subparser_pdf.add_argument('--filename', type=str,
                                 help='Base filename (defaults to doi).')

# # #  Textfile subparser options # # #
subparser_textfile = subparsers.add_parser('textfile', help='Write output to a standard text file.')

subparser_textfile.add_argument('more_dois', type=str, nargs='*', default=[],
                                help='Additional DOIs supplied on the command line.')
subparser_textfile.add_argument('-o', '--out', metavar='output file', type=str,
                                help='File to write to (defaults to input doi file, if provided).')
subparser_textfile.add_argument('--replace', action='store_true', default=False,
                                help="Replace DOIs in source document with \\citecmd'{@key} and write to bibtexdb bib file. Requires --doifile.")
subparser_textfile.add_argument('--trim', nargs=2, default=['[',']'],
                                help="Trim these two characters surrounding DOIs on replace e.g., square braces from [DOI].")
subparser_textfile.add_argument('--citecmd', type=str, default='autocite',
                                help='Citekey to use when replacing DOIs.')

# # #  Webserver subparser options # # #
subparser_webserver = subparsers.add_parser('webserver', help='Run doi2bibtex as a standalone web server.')
subparser_webserver.add_argument('more_dois', type=str, nargs='*', default=[],
                                 help='Additional DOIs supplied on the command line (does nothing in webserver mode).')
subparser_webserver.add_argument('--port', type=int, default=8080,
                                 help="Port to run server on.")
subparser_webserver.add_argument('--addr', type=str, default='127.0.0.1',
                                 help="Address to bind.")

# # #  LLM Config subparser options # # #
subparser_llm_config = subparsers.add_parser('llm-config', help='Configure LLM models.')
subparser_llm_config.add_argument('llm_action', type=str, choices=['list', 'add', 'rm', 'default'],
                                  help='Action to perform.')

# # #  Tex subparser options # # #
subparser_tex = subparsers.add_parser('tex', help='Tools for working with .tex files.')
subparser_tex.add_argument('tex_files', type=str, nargs='+',
                           help='One or more .tex files to process.')
subparser_tex.add_argument('--check-cites', action='store_true', default=False,
                           help='Check for and consolidate duplicate citations.')
subparser_tex.add_argument('--llm', action='store_true', default=False,
                           help='Use LLM for deduplication (experimental).')


argcomplete.autocomplete(parser)
opts = parser.parse_args()

if opts.outputmode == 'webserver' and opts.loglevel == 'warning':
    opts.loglevel = 'info'

if opts.outputmode == 'bibtexdb':
    if opts.clean:
        opts.dedue = True
    if not opts.bibtexdb and not opts.out:
        opts.out = 'doi2bibtex.bib'
    elif opts.bibtexdb and not opts.out:
        opts.out = opts.bibtexdb
if opts.outputmode == 'textfile':
    if opts.replace and not opts.doifile:
        parser.error('--replace requires --doifile')
    if opts.replace and not opts.bibtexdb:
        opts.bibtexdb = 'doi2bibtex.bib'
    if not opts.doifile and not opts.out:
        opts.out = 'doi2bibtex.txt'
    elif opts.doifile and not opts.out:
        opts.out = opts.doifile
