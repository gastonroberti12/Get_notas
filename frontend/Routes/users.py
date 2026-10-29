import requests
from flask import Blueprint, render_template, request, redirect, url_for, session

users_bp = Blueprint("users", __name__)

API_URL = 'http://127.0.0.1:5001' # completar con la URL que pongan en el backend


def llamar_api(endpoint, datos):
    # POST al back. Devuelve (respuesta_json, error_de_conexion).
    try:
        r = requests.post(f'{API_URL}{endpoint}', json=datos, timeout=5)
        return r.json(), None
    except (requests.RequestException, ValueError):
        return None, 'No se pudo conectar con el servidor.'

@users_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        respuesta, error = llamar_api('/auth/login', {'email': email, 'password': password}) # completar con la URL que pongan en el backend
        if error is None and respuesta.get('ok'):   # hacer coincidir con la respuesta del backend, ver si es ok o un codigo http
            session['usuario'] = respuesta['usuario']
            return redirect('/')
        error = error or respuesta.get('mensaje', 'Email o contraseña incorrectos.')
        return render_template('login.html', error=error, email=email)
    
    return render_template("login.html")


@users_bp.route("/registro", methods=['GET', 'POST']) # si el backend lo hace se puede hacer que al registrarse se loguee automaticamente, por ahora lo dejamos asi.
def registro():
    if request.method == 'POST':
        datos = {
            'nombre':   request.form.get('nombre', '').strip(),
            'apellido': request.form.get('apellido', '').strip(),
            'email':    request.form.get('email', '').strip(),
            'password': request.form.get('password', ''),
        }

        respuesta, error = llamar_api('/auth/registro', datos) # completar con la URL que pongan en el backend
        if error is None and respuesta.get('ok'): # hacer coincidir con la respuesta del backend, ver si es ok o un codigo http
            return redirect(url_for('users.login'))

        error = error or respuesta.get('mensaje', 'No se pudo crear la cuenta.')
        return render_template('registro.html', error=error, nombre=datos['nombre'], apellido=datos['apellido'], email=datos['email'])

    return render_template("registro.html")

@users_bp.route("/perfil")
def profile():
    return render_template("perfil.html")