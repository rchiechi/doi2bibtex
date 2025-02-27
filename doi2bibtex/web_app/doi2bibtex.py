from tempfile import TemporaryDirectory
from quart import Quart, render_template, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from .output import list_dois
import doi2bibtex.bibtex as bibtex
import doi2bibtex.util as util


logger = util.getlogger(__name__)

UPLOAD_FOLDER = TemporaryDirectory()
ALLOWED_EXTENSIONS = {'txt', 'bib', 'tex'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER.name

@app.route("/")
async def home():
    return await render_template("index.html", TITLE="doi2bibtex")

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