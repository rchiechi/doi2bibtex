from tempfile import TemporaryDirectory
from flask import Flask, render_template, request, jsonify, send_from_directory, flash, url_for
from werkzeug.utils import secure_filename
from util import getlogger
from web_app import output
import bibtex
import util


logger = getlogger(__name__)

UPLOAD_FOLDER = TemporaryDirectory()
ALLOWED_EXTENSIONS = {'txt', 'bib', 'tex'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def getparam(param) -> str:
    """Get parameters of GET or POST request."""
    if request.method == 'POST':
        if param in request.form:
            return request.form[param]
    elif request.method == 'GET':
        if param in request.args:
            return request.args[param]
    return None

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER.name

@app.route("/")
def home():
    return render_template("index.html", TITLE="doi2bibtex")

@app.route("/doi2bib", methods = ['GET', 'POST'])
def doi2bib():
    doi = getparam('doi')
    if doi is None:
        flash('No DOI found')
        return home()
    logger.debug(f"Parsing {doi}")
    library = bibtex.read('')
    result = util.doitobibtex(doi)
    library.add(bibtex.read(result).entries)
    tex = output.list_dois(library)
    return render_template("success.html", HEAD='Bibtex Entry', MESSAGE=tex)

@app.route("/upload")
def upload():
    filetype = getparam('filetype') or 'bibtexdb'
    return render_template("fileupload.html", TITLE="Upload", FILETYPE=filetype)

@app.route('/success', methods = ['GET', 'POST'])   
def success():
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
        return render_template("success.html", HEAD='Uploaded', MESSAGE=f'Received {fh.filename}')
    return upload()
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)