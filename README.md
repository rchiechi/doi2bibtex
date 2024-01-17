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
doi2bibtex [-h] [--dois dois-to-parse] [--doifile find-dois-in-file] [--bibtexdb BIBTEXDB] [--loglevel {info,warning,error,debug}] [--refresh] [--database DATABASE] [--custom CUSTOM] {bibtexdb,html,clipboard,textfile} ...

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

subcommands:
  Options specific to the selected output mode.

  {bibtexdb,html,clipboard,textfile}
                        sub-command help
    bibtexdb            Write output to a bibtex databse
    html                Write output to HTML.
    clipboard           Copy output to clipboard.
    textfile            Write output to a standard text file.
```

You can also feed it more DOIs on the command line after the subcommand.