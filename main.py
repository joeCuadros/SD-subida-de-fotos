import imghdr, os
from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename


# Configuracion del servidor
app = Flask(__name__)
app.config['UPLOAD_PATH'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 # max 2 MB
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']


# retorna None si no es imagen
def validate_image(stream):
    header = stream.read(512)
    stream.seek(0) 
    format = imghdr.what(None, header) 
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

#### VISTAS
# vista principal
@app.route('/')
def index():
    os.makedirs(app.config['UPLOAD_PATH'], exist_ok=True) # crear si no existe la ruta
    files = os.listdir(app.config['UPLOAD_PATH'])
    return render_template('index.html', files=files)

# Error en caso que se mayor
@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413

@app.route('/', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename) #convierte en solo caracteres seguros
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        # validar si es imagen y si es una extension permitida
        if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(uploaded_file.stream):
            return 'Invalid image', 400
        os.makedirs(app.config['UPLOAD_PATH'], exist_ok=True) # crear si no existe la ruta
        uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    return '', 204

@app.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)

if __name__ == "__main__":
    # ejecutando configuracion
    app.run(host="0.0.0.0",port=5000,debug=True)
