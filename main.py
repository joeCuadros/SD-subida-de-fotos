import imghdr, os
from flask import Flask, render_template, request, send_from_directory, url_for, session, redirect, flash
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash #,generate_password_hash, 
"""
generate_password_hash(contraseña) #genera contraseña
"""
# Configuracion del servidor
app = Flask(__name__)
app.config['UPLOAD_PATH'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 # max 2 MB
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
app.secret_key = 'qpTI!vMBI1FpkvEkQ4*X^afdcSu0zhvi'
app.config.update(
    SESSION_COOKIE_HTTPONLY=True #no se puede leer por javascript
)
# usuario con contraseñas encriptadas
users = {
    'joe': {'id': 1,'password': 'scrypt:32768:8:1$YuLFzGcwJVbaou7G$2c9c2f21d858a2121d10644537c872c5efbe9d39825e6139fc3e6ebccd668a770242fd42a872cce9fc5148657d532991ecedf497ca79339ddbf5403c4df2f28d'},
    'misael': {'id': 2,'password': 'scrypt:32768:8:1$LPOUjOJrmGFshjyD$724a223d766c805912eee91f02b24214c6fd427d9645fae3bbb857f2e67aa3badd1e6b23f5c8073ee5839f17dd0307a40e062864449edbd0e6ef379aadb94dba'},
    'sebastian': {'id': 3,'password': 'scrypt:32768:8:1$x81vogaNFuwwWboO$ec5c0a2a8c1a6f3362ec0faf2347f1885b99584d0265eeadfce52df5c401cc699f5e5a9536ec18c3da6281238e79a29e5b261675c9d52d99e765ff6d9064040a'},
    'rodrigo': {'id': 4,'password': 'scrypt:32768:8:1$sXzsAW3BMK2QRA5F$23be256b413782396d45f28ca790eadf54474f21a31a8fcf4467c7b738e09a4bffc75b2ce333f51ad8b7800e307a85e5a371efe5a4d636b96021b5eed5b8e02f'},
}

# Decorador para proteger las rutas privadas
def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
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
        if username in users:
            # Verificar la contraseña
            if check_password_hash(users[username]['password'],password):
                user_id = users[username]['id']
                session['user_id'] = {"id": user_id, "username": username}
                return redirect(url_for('index'))
        
        flash('Invalid username or password','danger') # mandar error
        return render_template('login.html',username = request.form['username'])

    return render_template('login.html')

# cerrar sesion
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logout successful.','success') # mandar notificacion
    return redirect(url_for('login')) 

# vista principal
@app.route('/')
@login_required
def index():
    path = os.path.join(app.config['UPLOAD_PATH'],str(session['user_id']['id'])) # crear ruta para cada id de usuario
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
    # validar que no existe imagen
    if 'file' not in request.files:
        return 'No file part', 400
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename) #convierte en solo caracteres seguros
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        # su nombre no perteneza al formato ascii
        if file_ext == "":
            file_ext = f".{os.path.splitext(filename)[0]}"
            filename = f"imagen.{os.path.splitext(filename)[0]}" # imagen predeterminada
        # validar si es imagen y si es una extension permitida
        if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(uploaded_file.stream):
            return 'Invalid image', 400
        path = os.path.join(app.config['UPLOAD_PATH'],str(session['user_id']['id'])) # crear ruta para cada id de usuario
        os.makedirs(path, exist_ok=True) # crear si no existe la ruta
        unique_filename = get_unique_filename(path, filename) # archivo unico
        uploaded_file.save(os.path.join(path, unique_filename))
        return '', 204
    return 'Invalid image', 400 #no tiene nombre seguro

# Retorna la imagen subida del servidor
@app.route('/uploads/<filename>')
@login_required
def upload(filename):
    path = os.path.join(app.config['UPLOAD_PATH'],str(session['user_id']['id'])) # crear ruta para cada id de usuario
    return send_from_directory(path, filename)

if __name__ == "__main__":
    # ejecutando configuracion
    app.run(host="0.0.0.0",port=5000,debug=True)
    