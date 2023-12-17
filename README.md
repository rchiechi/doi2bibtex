# doi2bibtex
### An interactive script to convert DOIs to bibtex entries and cleanup entries in a bibtex database using bibtexparser.
doi2bibtex will:
- Convert DOIs to bibtex entries from a file or command line input
- Crawl through a bibtex database and:
    - Find duplicates
    - Replace journal names with ISO-4 abbreviations
- Save changes to bibtex database
- Replace doi entries with cite commands and keys from the source doi-containing file

#### installation:
```
cd /path/to/doi2bibtex
/usr/bin/env python3 -m pip install --upgrade ./
```

#### Usage:
```
doi2bibtex --bibtexfile references.bib --doifile input.tex --clean --replace

options:
  -h, --help            show this help message and exit
  --dois [dois-to-parse ...]
                        DOIs to parse. (default: [])
  --doifile find-dois-in-file
                        Search a text file for dois. (default: None)
  --replace             Replace DOIs in source document with utocite{@key}. (default: False)
  --trim TRIM TRIM      Trim these two characters surrounding DOIs on replace e.g., square braces from [DOI]. (default: ['[', ']'])
  --citecmd CITECMD     Citekey to use when replacing DOIs. (default: autocite)
  --bibtexfile BIBTEXFILE
                        A bibtex database to read/write from. (default: None)
  --clean               Clean bibtex db entries (implies dedupe). (default: False)
  --dedupe              Dedupe the bibtex library. (default: False)
  --loglevel {info,warn,error,debug}
                        Set the logging level. (default: info)
  --refresh             Refresh cached journal list. (default: False)
  --database DATABASE   Databse of journal abbreviations. (default: https://raw.githubusercontent.com/JabRef/abbrv.jabref.org/master/journals/journal_abbreviations_acs.csv)
  --custom CUSTOM       Custom abbreviations separated by equal signs, e.g., -c 'Journal of Kittens;J. Kitt.'You can call this argument more than once. These will be cached.
                        (default: [])
```
