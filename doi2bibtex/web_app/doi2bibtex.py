import os
import asyncio
from io import BytesIO
from .output import list_dois, bib_bytes
import doi2bibtex.bibtex as bibtex
import doi2bibtex.util as util
from asyncio_throttle import Throttler

OK_TO_RUN=False
try:
    from quart import Quart, render_template, request, send_from_directory, jsonify, send_file
    import magic
    OK_TO_RUN=True
except ImportError as e:
    print(f"Error importing package, you will not be able to run the web_server: {e}")

logger = util.getlogger(__name__)

ALLOWED_EXTENSIONS = {'.txt', '.bib', '.tex'}
ALLOWED_MIMETYPES = {"text/plain", "text/x-bibtex", "application/x-latex"}

throttler = Throttler(rate_limit=3, period=1)

def secure_filename(filename):
    _, ext = os.path.splitext(filename)
    return str(uuid.uuid4()) + ext

def is_allowed_file(file_content, filename):
    file_mime = magic.from_buffer(file_content, mime=True)
    _, file_extension = os.path.splitext(filename)
    logger.debug(f"File magic: {file_mime}")
    return file_extension.lower() in ALLOWED_EXTENSIONS and file_mime in ALLOWED_MIMETYPES



async def getparam(param) -> str:
    """Get parameters of GET or POST request."""
    if request.method == 'POST':
        form = await request.form
        return form.get(param)
    elif request.method == 'GET':
        args = request.args
        return args.get(param)
    return None

app = Quart(__name__)

@app.route("/")
async def home():
    parse_options = ('doi2bibtex', 'references cited', 'citing references')#, 'references cited', 'citing references')
    upload_options = ('bibtex', 'bibtexdb')
    return await render_template("index.html",
                                TITLE="doi2bibtex",
                                parse_options=parse_options,
                                upload_options=upload_options)


@app.route("/doi2bib", methods = ['GET', 'POST'])
async def doi2bib():
    doi = await getparam('doi')
    doi_action = await getparam('parseoption')
    doi_format = await getparam('formatoption')
    if doi is None:
        flash('No DOI found')
        return home()
    logger.debug(f"Parsing {doi}")
    dois = [doi]
    if doi_action == 'references cited':
        dois = await bibtex.async_get_cited(dois)
    elif doi_action == 'citing references':
        dois = await bibtex.async_get_citing(dois)
    library = bibtex.read('')
    async def process_doi(doi):
        nonlocal library
        if not doi:
            return
        async with throttler:
            result = await bibtex.async_get_bibtex_from_url(doi)
        if result: 
            library.add(bibtex.read(result).entries[0])
    tasks = [process_doi(doi) for doi in set(dois)]
    await asyncio.gather(*tasks)        

    if doi_format == 'bibtexdb':        
        file_path = BytesIO(bib_bytes(library))
        file_path.seek(0)
        return await send_file(file_path, as_attachment=True, attachment_filename="library.bib")
    else:
        tex = list_dois(library)
        return await render_template("success.html", HEAD='Bibtex Entry', MESSAGE=tex)

@app.route('/upload', methods=['POST'])
async def upload_file():
    files = await request.files
    file = files.get('file')
    _, ext = os.path.splitext(file.filename)
    if ext.lower() != '.txt':
        logger.debug(f"{file.filename} has bad extension {ext}")
        return await render_template("success.html",
                                      HEAD='Cannot parse',
                                      MESSAGE='I can only parse .txt files for now.')
    doi_format = await getparam('uploadoption')
    if file:
        file_content = file.read()
        if not is_allowed_file(file_content, file.filename):
        # else:
            logger.debug("Invalid file type.")
            return await render_template("success.html",
                                         HEAD='Cannot parse',
                                         MESSAGE='I can only parse .txt files for now.')
    else:
        logger.debug("No file uploaded.")
        return await render_template("success.html",
                                     HEAD='Cannot parse',
                                     MESSAGE='I did not receive a file.')
    dois = []
    file_content = str(file_content, encoding='utf8').strip()
    for delim in (',' ,' ', ';'):
        dois = file_content.split(delim)
    dois += file_content.split('\n')
    library = bibtex.read('')
    async def process_doi(doi):
        nonlocal library
        if not doi:
            return
        async with throttler:
            result = await bibtex.async_get_bibtex_from_url(doi)
        if result: 
            library.add(bibtex.read(result).entries[0])
    tasks = [process_doi(doi) for doi in set(dois)]
    await asyncio.gather(*tasks)
    
    if doi_format == 'bibtexdb':        
        file_path = BytesIO(bib_bytes(library))
        file_path.seek(0)
        return await send_file(file_path, as_attachment=True, attachment_filename="library.bib")

    elif doi_format == 'bibtex':
        tex = list_dois(library)
        return await render_template("success.html", HEAD='Bibtex Entry', MESSAGE=tex)
    else:
        tex = list_dois(library)
        return await render_template("success.html", HEAD='Unknown format', MESSAGE='')
    
@app.route('/success', methods = ['GET', 'POST'])   
async def success():
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    fh = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if fh.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if fh and allowed_file(fh.filename):
        filename = secure_filename(fh.filename)
        fh.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) 
        return await render_template("success.html", HEAD='Uploaded', MESSAGE=f'Received {fh.filename}')
    return await upload()
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)