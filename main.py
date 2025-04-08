import imghdr, os
from flask import Flask, render_template, request, send_from_directory, url_for, session, redirect
from werkzeug.utils import secure_filename


# Configuracion del servidor
app = Flask(__name__)
app.config['UPLOAD_PATH'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 # max 2 MB
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
app.secret_key = 'super_secret_key@'

users = {
    'joe': {'password': '12345678', 'id': 1},
    '12345678': {'password': '12345678', 'id': 2}
}

# Decorador para proteger las rutas privadas
def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            #flash('Debes iniciar sesión para acceder a esta página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__ 
    return wrap

# retorna None si no es imagen
def validate_image(stream):
    header = stream.read(512)
    stream.seek(0) 
    format = imghdr.what(None, header) 
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

# funcion para retornar un nombre unico 
def get_unique_filename(upload_path, filename):
    base_name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    
    while os.path.exists(os.path.join(upload_path, new_filename)):
        new_filename = f"{base_name}({counter}){ext}"
        counter += 1
    
    return new_filename
#### VISTAS
# login 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # validar si existe usuario
        if username in users:
            # Verificar la contraseña
            if users[username]['password'] == password:
                user_id = users[username]['id']
                session['user_id'] = {"id": user_id, "username": username}
                return redirect(url_for('index'))
        
        #'Usuario o contraseña incorrectos'
        return redirect(url_for('login'))

    return render_template('login.html')

# cerrar sesion
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Eliminar la sesión del usuario
    return redirect(url_for('login'))  # Redirigir al login

# vista principal
@app.route('/')
@login_required
def index():
    path = os.path.join(app.config['UPLOAD_PATH'],str(session['user_id']['id']))
    os.makedirs(path, exist_ok=True) # crear si no existe la ruta
    files = os.listdir(path)
    return render_template('index.html', files=files)

# Error en caso que se mayor
@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413

# logica de subir el archivo
@app.route('/', methods=['POST'])
@login_required
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename) #convierte en solo caracteres seguros
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        # validar si es imagen y si es una extension permitida
        if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(uploaded_file.stream):
            return 'Invalid image', 400
        path = os.path.join(app.config['UPLOAD_PATH'],str(session['user_id']['id'])) # crear ruta para cada id de usuario
        os.makedirs(path, exist_ok=True) # crear si no existe la ruta
        unique_filename = get_unique_filename(path, filename) # archivo unico
        uploaded_file.save(os.path.join(path, unique_filename))
    return '', 204

# Retorna la imagen subida del servidor
@app.route('/uploads/<filename>')
@login_required
def upload(filename):
    path = os.path.join(app.config['UPLOAD_PATH'],str(session['user_id']['id']))
    return send_from_directory(path, filename)

if __name__ == "__main__":
    # ejecutando configuracion
    app.run(host="0.0.0.0",port=5000,debug=True)
