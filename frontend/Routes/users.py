import requests
from flask import Blueprint, render_template, request, redirect, url_for, session
from Routes.roles import esta_logueado


users_bp = Blueprint("users", __name__)

API_URL = 'http://127.0.0.1:5001' # completar con la URL que pongan en el backend


def llamar_api(metodo, endpoint, datos=None):
    # Llama al back y devuelve (status_http, json). Si no hay conexion, status es None.
    # Si hay sesion, manda el token en Authorization: Bearer.
    headers = {}
    if 'token' in session:
        headers['Authorization'] = f"Bearer {session['token']}"
    try:
        r = requests.request(metodo, f'{API_URL}{endpoint}', json=datos, headers=headers, timeout=5)
        return r.status_code, (r.json() if r.content else {})
    except (requests.RequestException, ValueError):
        return None, {}
    
def mensaje_error(status, cuerpo, por_defecto):
    if status is None:
        return 'No se pudo conectar con el servidor.'
    errores = cuerpo.get('errors') or [{}]
    return errores[0].get('message', por_defecto)

@users_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        status, cuerpo = llamar_api('POST', '/auth/login', {'email': email, 'contrasenia': password})
        if status == 200:
            session['token'] = cuerpo['token']
            session['usuario'] = cuerpo['usuario'] # incluye el rol
            return redirect('/')
        
        error = mensaje_error(status, cuerpo, 'Email o contraseña incorrectos.')
        return render_template('login.html', error=error, email=email)
    
    return render_template("login.html")


@users_bp.route("/registro", methods=['GET', 'POST']) # el back no loguea al registrar, por eso redirigimos al login
def registro():
    if request.method == 'POST':
        datos = {
            'nombre':   request.form.get('nombre', '').strip(),
            'apellido': request.form.get('apellido', '').strip(),
            'email':    request.form.get('email', '').strip(),
            'contrasenia': request.form.get('password', ''),
        }

        status, cuerpo = llamar_api('POST', '/usuarios', datos)
        if status == 201:
            return redirect(url_for('users.login'))

        error = mensaje_error(status, cuerpo, 'No se pudo crear la cuenta.')
        return render_template('registro.html', error=error, nombre=datos['nombre'], apellido=datos['apellido'], email=datos['email'])

    return render_template("registro.html")

@users_bp.route("/logout", methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('peliculas.inicio'))

@users_bp.route("/perfil")
def profile():
    if not esta_logueado():
        return redirect(url_for('users.login'))
    return render_template("usuario.html")