# doi2bibtex
### An interactive script to convert DOIs to bibtex entries and cleanup entries in a bibtex database using bibtexparser.
doi2bibtex will:
- Convert DOIs to bibtex entries from a file or command line input
- Crawl through a bibtex database and:
    - Find duplicates
    - Replace journal names with ISO-4 abbreviations
- Save changes to bibtex database
- Replace DOI entries with cite commands and keys from the source doi-containing file
- Create a bibtex database containing all of the papers cited in the DOI(s) provided.
- Create a bibtex database containing all of the papers that cite the DOI(s) provided.
- Export a bibtex database as an HTML-formatted biblography (as an unordered list amenable to my website).
- Export a numbered list of references.

I wrote this for myself, to make it easier to compile bibliographic databases with collaborators who use disparate reference managers. Thus, it is only tested insofar as I use it.

**Warning**: doi2bibtex cannot fetch page numbers from certain journals and publishers that do not formally use page-numbers, e.g., Wiley journals.

#### installation:
```
cd /path/to/doi2bibtex
/usr/bin/env python3 -m pip install --upgrade ./
```
To enable tab completion via [argcomplete](https://github.com/kislyuk/argcomplete): (you might need to use sudo)
```
activate-global-python-argcomplete
``` 

Then add this line to `.bashrc` or `.zshrc`:
```
eval "$(register-python-argcomplete doi2bibtex)"
```

#### Usage:
```
usage: doi2bibtex [-h] [--dois dois-to-parse] [--doifile find-dois-in-file] [--bibtexdb BIBTEXDB] [--loglevel {info,warning,error,debug}] [--refresh] [--database DATABASE] [--custom CUSTOM] [--cited] [--citing] {bibtexdb,html,textlist,clipboard,textfile} ...

A python script for interacting with DOIs and bibtex.

options:
  -h, --help            show this help message and exit
  --dois dois-to-parse  DOIs to parse, comma-separated. For example --dois '10.1234/journal1, 10.4567/journal2' (default: )
  --doifile find-dois-in-file
                        Search a text file for dois. (default: None)
  --bibtexdb BIBTEXDB   Bibtexdb to use as input, otherwise create a blank library. (default: None)
  --loglevel {info,warning,error,debug}
                        Set the logging level. (default: warning)
  --refresh             Refresh cached journal list. (default: False)
  --database DATABASE   Databse of journal abbreviations. (default: https://raw.githubusercontent.com/JabRef/abbrv.jabref.org/master/journals/journal_abbreviations_acs.csv)
  --custom CUSTOM       Custom abbreviations separated by equal signs, e.g., -c 'Journal of Kittens;J. Kitt.'You can call this argument more than once. These will be cached. (default: [])
  --cited               Return the bibliographies of the papers in the input doi(s). (default: False)
  --citing              Return dois that cite the papers in the input doi(s). (default: False)

subcommands:
  Options specific to the selected output mode.

  {bibtexdb,html,textlist,clipboard,textfile}
                        sub-command help
    bibtexdb            Write output to a bibtex databse
    html                Write output to HTML.
    textlist            Write output to HTML.
    clipboard           Copy output to clipboard.
    textfile            Write output to a standard text file.

Invoke a subcommand with -h to see options specific to that command.
```

**bibtexdb** Read from (and write to) a bibtex database, e.g., to abbreviate and texify a bibliography prior to submission
```
usage: doi2bibtex bibtexdb [-h] [-o output file] [--clean] [--dedupe] [more_dois ...]

positional arguments:
  more_dois             Additional DOIs supplied on the command line.

options:
  -h, --help            show this help message and exit
  -o output file, --out output file
                        File to write to (defaults to input bibtexdb file, if provided).
  --clean               Clean bibtex db entries (implies dedupe).
  --dedupe              Dedupe the bibtex library.
```

**html** Generates a bibliography in HTML format (quite specific to my personal use case)
```
usage: doi2bibtex html [-h] [-o output file] [--nobreaks] [-b BOLDNAME] [more_dois ...]

positional arguments:
  more_dois             Additional DOIs supplied on the command line.

options:
  -h, --help            show this help message and exit
  -o output file, --out output file
                        File to write to. Prints to stdout if not provided.
  --nobreaks            Do not insert line breaks for readabiltiy.
  -b BOLDNAME, --boldname BOLDNAME
                        Bold this name in HTML output.
```

**textlist** Generates a bibliography in text format, e.g., for a CV
```
usage: doi2bibtex textlist [-h] [-o output file] [-b BOLDNAME] [-y] [more_dois ...]

positional arguments:
  more_dois             Additional DOIs supplied on the command line.

options:
  -h, --help            show this help message and exit
  -o output file, --out output file
                        File to write to. Prints to stdout if not provided.
  -b BOLDNAME, --boldname BOLDNAME
                        Add asterisk to this name.
  -y, --years           Include years as headers on separate lines.
```

**clipboard** Resolves DOIs to bibtex entries and copies them to the clipboard (or prints them to stdout)
```
usage: doi2bibtex clipboard [-h] [--stdout] [--noclean] [more_dois ...]

positional arguments:
  more_dois   Additional DOIs supplied on the command line.

options:
  -h, --help  show this help message and exit
  --stdout    Write to stdout instead of cliboard.
  --noclean   Do not convert unicode to LaTeX.
```

**textfile** Parses a textfile and replaces instances of [_doi_] with `\autocite{cite_key}` (does not always work)
```
usage: doi2bibtex textfile [-h] [-o output file] [--replace REPLACE] [--trim TRIM TRIM] [--citecmd CITECMD] [more_dois ...]

positional arguments:
  more_dois             Additional DOIs supplied on the command line.

options:
  -h, --help            show this help message and exit
  -o output file, --out output file
                        File to write to (defaults to input doi file, if provided).
  --replace REPLACE     Replace DOIs in source document with \citecmd'{@key} and write to provided bibtexdb. Requires --doifile.
  --trim TRIM TRIM      Trim these two characters surrounding DOIs on replace e.g., square braces from [DOI].
  --citecmd CITECMD     Citekey to use when replacing DOIs.
```


You can also feed it more DOIs on the command line after the subcommand.


