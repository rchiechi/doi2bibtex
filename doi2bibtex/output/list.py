import re
import doi2bibtex.util as util
import doi2bibtex.bibtex as bibtex
from .filewriter import backupandwrite
from datetime import datetime as dt
from bibtexparser.model import Entry, Field
from colorama import Fore, Style
from titlecase import titlecase

REDOIURI = re.compile('https?://(dx\\.)?doi\\.org/')

logger = util.getlogger(__name__)

async def do_html(library, args):
    html = ''
    formatted = {'journals':{},'books':{},'patents':{}}
    textf = {'bold': ('<b>','</b>'),
             'italics': ('<i>','</i>'),
             'heading': ('<h2','</h2>'),
             'href': ('<A href=',' target="_blank">','</A>', '')}
    for entry in library.entries:
        year, _formatted = await _parse_entry(entry, args, textf)
        if year is None:
            continue
        if year not in formatted['journals']:
            formatted['journals'][year] = [_formatted]
        else:
            formatted['journals'][year].append(_formatted)

    html = _HTMLblock(formatted, textf, args)
    if args.out is None:
        print(html)
    else:
        print(f"{Style.BRIGHT}Writing to {args.out}")
        backupandwrite(args.out, bytes(html, encoding='utf-8'))

async def do_markdown(library, args):
    txt = ''
    formatted = {'journals':{},'books':{},'patents':{}}
    textf = {'bold': ('**','**'),
             'italics': ('*','*'),
             'heading': ('##',''),
             'href': ('[',']','(', ')')}
    
    for entry in library.entries:
        year, _formatted = await _parse_entry(entry, args, textf)
        if year is None:
            continue
        if year not in formatted['journals']:
            formatted['journals'][year] = [_formatted]
        else:
            formatted['journals'][year].append(_formatted)
    
    txt = _Markdownblock(formatted, textf, args)
    if args.out is None:
        print(txt)
    else:
        print(f"{Style.BRIGHT}Writing to {args.out}")
        backupandwrite(args.out, bytes(txt, encoding='utf-8'))

async def do_textlist(library, args):
    txt = ''
    formatted = {'journals':{},'books':{},'patents':{}}
    for entry in library.entries:
        year, _formatted = await _parse_entry(entry, args)
        if year is None:
            continue
        if year not in formatted['journals']:
            formatted['journals'][year] = [_formatted]
        else:
            formatted['journals'][year].append(_formatted)

    txt = _TXTblock(formatted, args)
    if args.out is None:
        print(txt)
    else:
        print(f"{Style.BRIGHT}Writing to {args.out}")
        backupandwrite(args.out, bytes(txt, encoding='utf-8'))

async def _parse_entry(entry, args, textf=None):
    if entry.entry_type.lower() != 'article':
        print(f'{Fore.RED}Cannot parse {entry.key} ({entry.entry_type})')
        return None, None
    doi = _finddoi(entry)
    if doi is None:
        print(f'{Fore.RED}Missing DOI for {entry.key} ({entry.entry_type})')
        print(entry)
        _href = '/'
    else:
        _href = util.doitolink(doi)
    for key in ('year', 'title', 'author', 'journal', 'volume', 'pages'):
        try:
            entry.fields_dict[key].value
        except KeyError:
            _field = await resolvedoi(doi, key)
            entry.set_field(_field.fields_dict[key])
            print(f'{Style.BRIGHT}{Fore.BLUE}Added {key}: "{entry.fields_dict[key].value}" to {entry.key}')
    try:
        year = int(entry.fields_dict['year'].value)
    except ValueError:
        year = dt.now().year
        print("Warning %s is non-numerical year, setting to %s." % (entry.fields_dict['year'].value, year))

    if textf is not None:
        # clean_title = '<A href="%s" target="_blank">%s</A>' % (_href, titlecase(cleanLatex(entry.fields_dict['title'].value)))
        if textf['href'][3]:
            clean_title = '%s%s%s%s%s%s' % (textf['href'][0],
                                            titlecase(cleanLatex(entry.fields_dict['title'].value)),
                                            textf['href'][1],
                                            textf['href'][2],
                                            _href,
                                            textf['href'][3])
        else:
            clean_title = '%s"%s"%s%s%s' % (textf['href'][0],
                                            _href,
                                            textf['href'][1],
                                            titlecase(cleanLatex(entry.fields_dict['title'].value)),
                                            textf['href'][2])
        clean_authors = parseAuthors(entry.fields_dict['author'].value, args.boldname, textf)
        clean_journal = '%s%s%s' % (textf['italics'][0], cleanLatex(entry.fields_dict['journal'].value), textf['italics'][1])
        clean_pages = cleanLatex(entry.fields_dict['pages'].value)
        clean_volume = '%s%s%s' % (textf['italics'][0], cleanLatex(entry.fields_dict['volume'].value), textf['italics'][1])
        clean_year = '%s%s%s' % (textf['bold'][0], cleanLatex(year), textf['bold'][1])
        _formatted = '%s %s. %s %s, %s, %s' % (clean_authors,
                                               clean_title, clean_journal,
                                               clean_year, clean_volume, clean_pages)
    else:
        clean_title = titlecase(cleanLatex(entry.fields_dict['title'].value))
        clean_authors = parseAuthors(entry.fields_dict['author'].value, args.boldname)
        clean_journal = cleanLatex(entry.fields_dict['journal'].value)
        clean_pages = cleanLatex(entry.fields_dict['pages'].value)
        clean_volume = cleanLatex(entry.fields_dict['volume'].value)
        clean_year = cleanLatex(year)
        _formatted = f'{clean_authors} {clean_title}. {clean_journal} {clean_year}, {clean_volume}, {clean_pages}. DOI:{doi}'
    return year, _formatted

def _finddoi(entry):
    doi = None
    for key in ('doi', 'DOI'):
        if key in entry.fields_dict:
            doi = entry.fields_dict[key].value
    if doi is None:
        _keys = list(entry.fields_dict)
        for _key in ('eprint', 'url'):
            if _key in entry.fields_dict:
                _keys = [_key] + _keys
        for _key in _keys:
            _uri = str(entry.fields_dict[_key].value)
            m = re.search(REDOIURI, _uri)
            if m is not None:
                doi = _uri[m.span(0)[1]:]
            if doi:
                break
    return doi or None

def _HTMLblock(formatted, textf, args):
    html = []
    years = list(formatted['journals'].keys())
    years.sort(reverse=True)

    # html.append('<ol>')
    for _year in years:
        html.append('%s id="%s">%s%s' % (textf['heading'][0], _year, _year, textf['heading'][1]))
        for _pub in formatted['journals'][_year]:
            html.append('<li>')
            html.append('<p>%s</p>' % _pub)
            html.append('</li>')

    if args.nobreaks:
        return ''.join(html)
    return '\n'.join(html)

def _Markdownblock(formatted, textf, args):
    txt = []
    years = list(formatted['journals'].keys())
    years.sort(reverse=True)
    for _year in years:
        txt.append('%s %s' % (textf['heading'][0], _year))
        for _pub in formatted['journals'][_year]:
            txt.append(f'- {_pub}')
    return '\n'.join(txt)

def _TXTblock(formatted, args):
    txt = []
    years = list(formatted['journals'].keys())
    years.sort(reverse=True)
    i = 1
    for _year in years:
        if args.years:
            txt.append(f'{_year}')
        for _pub in formatted['journals'][_year]:
            txt.append(f'{i:03}. {_pub}')
            i += 1
    return '\n'.join(txt)

def cleanLatex(latex):
    converter = util.latexAccentConverter()
    _raw = r'{}'.format(latex)
    for _r in (('{',''),('}',''),('--','-'),('–', '-'),('—','-')):
        _raw = _raw.replace(_r[0],_r[1])
    try:
        # cleaned = bytes(_raw, encoding='utf8').decode('latex')
        cleaned = converter.decode_Tex_Accents(_raw, utf8_or_ascii=1)
    except ValueError:
        logger.warn(f'Error decoding {_raw} to latex')
        # cleaned = bytes(_raw, encoding='utf8')
        cleaned = _raw
    return str(cleaned).strip()

def parseAuthors(authors, boldname, textf=None):
    _authorlist = []
    for _author in (authors.split('and')):
        _s = cleanLatex(_author)
        if ',' not in _s:
            _s = '%s, %s' % (_s.split(' ')[-1], ' '.join(_s.split(' ')[:-1]))
        if boldname and (boldname.lower() in _s.lower()) and textf is not None:
            _s = '%s%s%s' % (textf['bold'][0], _s, textf['bold'][1])
        elif boldname and (boldname.lower() in _s.lower()):
            _s = f'*{_s}'
        _authorlist.append(_s)
    return '; '.join(_authorlist)

async def resolvedoi(doi, key='null'):
    entry = Entry('article', str(doi), [Field(key, '')])
    if doi is not None:
        result = await util.async_get_bibtex_from_url(doi)
        if result:
            entry = bibtex.read(result).entries[0]
            print(f'{Style.BRIGHT}{Fore.GREEN}Got record from {doi}.')
    if key in entry.fields_dict:
        return entry
    print(f'{Style.BRIGHT}{Fore.MAGENTA}But {key} was empty {doi}.')
    entry.set_field(Field(key, ''))
    return entry
