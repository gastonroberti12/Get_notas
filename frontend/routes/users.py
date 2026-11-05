from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from api_cliente import llamar_api, mensaje_error
from routes.roles import esta_logueado, es_cliente
from datos_perfil import ESTADOS_PROXIMAS, ESTADOS_HISTORIAL, SIN_DATO, armar_reserva


users_bp = Blueprint("users", __name__)

@users_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        status, cuerpo = llamar_api('POST', '/auth/login', {'email': email, 'contrasenia': password})
        if status == 200:
            session['token'] = cuerpo['token']
            session['usuario'] = cuerpo['usuario'] # incluye el rol
            flash('Sesión iniciada con éxito.', 'exito') # flash: mensaje que se muestra en la siguiente página
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
            flash('Te registraste con éxito. Ya podés iniciar sesión.', 'exito')
            return redirect(url_for('users.login'))

        error = mensaje_error(status, cuerpo, 'No se pudo crear la cuenta.')
        return render_template('registro.html', error=error, nombre=datos['nombre'], apellido=datos['apellido'], email=datos['email'])

    return render_template("registro.html")

@users_bp.route("/logout", methods=['POST'])
def logout():
    session.clear()
    flash('Sesión cerrada con éxito.', 'exito')
    return redirect(url_for('peliculas.inicio'))

@users_bp.route("/perfil")
def profile():
    if not esta_logueado():
        return redirect(url_for('users.login'))
    
    #pedir datos del usuario y sus reservas al backend
    status, usuario = llamar_api('GET', '/usuarios/me')
    if status == 401:  # token vencido: se limpia la sesion para no quedar "logueado" sin poder consultar
        session.clear()
        return redirect(url_for('users.login'))
    if status != 200:
        return render_template('errores/503.html'), 503

    perfil = {
        'nombre': usuario['nombre'],
        'apellido': usuario['apellido'],
        'email': usuario['email'],
        'anio_registro': (usuario.get('fecha_registro') or '')[:4] or SIN_DATO,
    }

    reservas_api = []
    if es_cliente():
        status, cuerpo = llamar_api('GET', '/usuarios/me/reservas?_limit=100')
        reservas_api = cuerpo.get('reservas', []) if status in (200, 204) else []
    cache = {}  # cache compartido por todas las reservas de este request
    proximas = [armar_reserva(reserva, cache) for reserva in reservas_api if reserva['estado'] in ESTADOS_PROXIMAS]
    historial = [armar_reserva(reserva, cache) for reserva in reservas_api if reserva['estado'] in ESTADOS_HISTORIAL]

    return render_template('perfil.html', perfil=perfil, reservas_proximas=proximas, reservas_historial=historial)

@users_bp.route("/perfil/actualizar", methods=['POST'])
def actualizar_perfil():
    if not esta_logueado():
        return redirect(url_for('users.login'))

    datos = {campo: request.form.get(campo, '').strip() for campo in ('nombre', 'apellido', 'email')}

    status, _ = llamar_api('PATCH', f"/usuarios/{session['usuario']['id']}", datos)
    if status == 204:
        session['usuario'] = {**session['usuario'], 'nombre': datos['nombre']}  # el navbar muestra el nombre
    return redirect(url_for('users.profile'))