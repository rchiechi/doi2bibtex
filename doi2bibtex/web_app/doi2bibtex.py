import os
from tempfile import NamedTemporaryFile
from quart import Quart, render_template, request, send_from_directory, jsonify
import magic
from .output import list_dois
import doi2bibtex.bibtex as bibtex
import doi2bibtex.util as util


logger = util.getlogger(__name__)

ALLOWED_EXTENSIONS = {'txt', 'bib', 'tex'}
ALLOWED_MIMETYPES = {"text/plain", "text/x-bibtex", "application/x-latex"}

def secure_filename(filename):
    _, ext = os.path.splitext(filename)
    return str(uuid.uuid4()) + ext

def is_allowed_file(file_content, filename):
    file_mime = magic.from_buffer(file_content, mime=True)
    _, file_extension = os.path.splitext(filename)
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
    parse_options = ('bibtex', 'references cited', 'citing references')
    upload_options = ('bibtexdb', 'markdown')
    return await render_template("index.html",
                                TITLE="doi2bibtex",
                                parse_options=parse_options,
                                upload_options=upload_options)

@app.route("/doi2bib", methods = ['GET', 'POST'])
async def doi2bib():
    doi = await getparam('doi')
    if doi is None:
        flash('No DOI found')
        return home()
    logger.debug(f"Parsing {doi}")
    library = bibtex.read('')
    result = await util.async_get_bibtex_from_url(doi)
    library.add(bibtex.read(result).entries)
    tex = list_dois(library)
    return await render_template("success.html", HEAD='Bibtex Entry', MESSAGE=tex)

@app.route("/upload")
async def upload():
    filetype = await getparam('filetype') or 'bibtexdb'
    return await render_template("fileupload.html", TITLE="Upload", FILETYPE=filetype)

@app.route('/upload', methods=['POST'])
async def upload_file():
    file = await request.files.get('file')
    if file:
        file_content = await file.read()
        if is_allowed_file(file_content, file.filename):
            #file_path = NamedTemporaryFile()
            # secure_name = secure_filename(file.filename)
            # file_path = os.path.join("/tmp", secure_name) #Change this to your upload directory
            # with open(file_path, 'wb') as f:
            #file_path.write(file_content)
            with NamedTemporaryFile() as file_path:
                file_path.write(file_content)
            logger.debug(f"File uploaded successfully as {file_path.name}")
        else:
            logger.debug("Invalid file type.")
    else:
        logger.debug("No file uploaded.")

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