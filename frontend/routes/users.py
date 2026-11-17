from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from api_cliente import llamar_api, mensaje_error
from routes.roles import esta_logueado, es_cliente
from datos_perfil import SIN_DATO, armar_reserva, clasificar_reserva, parsear_fecha


users_bp = Blueprint("users", __name__)

def destino_seguro(destino):
    """Solo rutas internas del sitio (evita open redirect)."""
    if destino and destino.startswith('/') and not destino.startswith('//') and '\\' not in destino:
        return destino
    return '/'

@users_bp.route("/login", methods=['GET', 'POST'])
def login():
    siguiente = request.values.get('next', '')  # viene por URL (GET) o por campo oculto (POST)
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        status, cuerpo = llamar_api('POST', '/auth/login', {'email': email, 'contrasenia': password})
        if status == 200:
            session['token'] = cuerpo['token']
            session['usuario'] = cuerpo['usuario'] # incluye el rol
            session.pop('sucursal_id', None) # al loguearse vuelve a la sucursal principal
            flash('Sesión iniciada con éxito.', 'exito') # flash: mensaje que se muestra en la siguiente página
            return redirect(destino_seguro(siguiente))

        error = mensaje_error(status, cuerpo, 'Email o contraseña incorrectos.')
        return render_template('login.html', error=error, email=email, siguiente=siguiente)

    return render_template("login.html", siguiente=siguiente)
    

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
    if status in (401, 404):  # token vencido: se limpia la sesion para no quedar "logueado" sin poder consultar
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

    # las reservas del perfil las devuelve /usuarios/me/reservas (solo clientes; 204 = sin reservas)
    reservas_api = []
    if es_cliente():
        status_reservas, cuerpo_reservas = llamar_api('GET', '/usuarios/me/reservas?_limit=100')
        if status_reservas == 200:
            reservas_api = cuerpo_reservas.get('reservas', [])
        elif status_reservas != 204:
            flash('No se pudieron cargar tus reservas. Probá de nuevo en unos minutos.', 'error')
            
    proximas = []
    historial = []
    for reserva in reservas_api:
        ubicacion = clasificar_reserva(reserva)
        
        if ubicacion == "proximas":
            proximas.append(armar_reserva(reserva))
        
        elif ubicacion == "historial":
            historial.append(armar_reserva(reserva))

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


CONTRASENIA_MINIMA = 8    # mismos límites que valida el back (validators/auth.py)
CONTRASENIA_MAXIMA = 128

    
@users_bp.route("/perfil/contrasenia", methods=['GET', 'POST'])
def cambiar_contrasenia():
    if not esta_logueado():
        return redirect(url_for('users.login', next=request.path))

    if request.method == 'POST':
        actual = request.form.get('actual', '')
        nueva = request.form.get('nueva', '')
        repetir = request.form.get('repetir', '')

        error = None
        if not actual or not nueva or not repetir:
            error = 'Completá todos los campos.'
        elif nueva != repetir:
            error = 'La nueva contraseña y su repetición no coinciden.'
        elif len(nueva) < CONTRASENIA_MINIMA or len(nueva) > CONTRASENIA_MAXIMA:
            error = f'La nueva contraseña debe tener entre {CONTRASENIA_MINIMA} y {CONTRASENIA_MAXIMA} caracteres.'

        if error is None:
            # el back verifica la actual, rechaza una nueva igual y cierra las sesiones anteriores
            status, cuerpo = llamar_api('POST', '/usuarios/me/contrasenia', {'contrasenia_actual': actual, 'contrasenia_nueva': nueva})
            if status == 204:
                session.clear()
                flash('Contraseña actualizada. Iniciá sesión con la nueva.', 'exito')
                return redirect(url_for('users.login'))
            if status == 401:  # token vencido
                session.clear()
                return redirect(url_for('users.login'))
            error = mensaje_error(status, cuerpo, 'No se pudo cambiar la contraseña.')

        return render_template('cambiar_contrasenia.html', error=error, minimo=CONTRASENIA_MINIMA, maximo=CONTRASENIA_MAXIMA)

    return render_template('cambiar_contrasenia.html', minimo=CONTRASENIA_MINIMA, maximo=CONTRASENIA_MAXIMA)


# Página con todas las reseñas que escribió el cliente
@users_bp.route("/perfil/resenas")
def mis_resenas():
    if not esta_logueado():
        return redirect(url_for('users.login', next=request.path))
    if not es_cliente():
        return redirect(url_for('users.profile'))

    status, cuerpo = llamar_api('GET', '/usuarios/me/resenas?_limit=100')
    if status not in (200, 204):
        flash(mensaje_error(status, cuerpo, 'No se pudieron cargar tus reseñas.'), 'error')
        return redirect(url_for('users.profile'))

    resenas = cuerpo.get('resenas', [])
    for r in resenas:
        fecha = parsear_fecha(r.get('fecha'))
        r['fecha_texto'] = fecha.strftime('%d/%m/%Y') if fecha else ''

    return render_template('mis_resenas.html', resenas=resenas)