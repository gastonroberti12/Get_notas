from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services.api_cliente import mensaje_error
from services.usuarios import (iniciar_sesion, cerrar_sesion, registrar_usuario, obtener_mi_usuario,
                               actualizar_usuario, actualizar_contrasenia, listar_mis_reservas, listar_mis_resenas)
from logica.roles import esta_logueado, es_cliente, solo_logueado
from logica.formato import formatear_fecha
from logica.reservas import armar_reserva, clasificar_reserva
from logica.validaciones import CONTRASENIA_MINIMA, CONTRASENIA_MAXIMA, validar_cambio_contrasenia
from routes.errores import abortar_por_status

users_bp = Blueprint("users", __name__)

def destino_seguro(destino):
    #solo rutas internas del sitio (evita open redirect)
    if destino and destino.startswith('/') and not destino.startswith('//') and '\\' not in destino:
        return destino
    return '/'

@users_bp.route("/login", methods=['GET', 'POST'])
def login():
    siguiente = request.values.get('next', '')  # viene por URL (GET) o por campo oculto (POST)
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        status, cuerpo = iniciar_sesion(email, password)
        if status == 200:
            session['token'] = cuerpo['token']
            session['usuario'] = cuerpo['usuario'] # incluye el rol
            session.pop('sucursal_id', None) # al loguearse vuelve a la sucursal principal
            flash('Sesión iniciada con éxito.', 'exito') # flash: mensaje que se muestra en la siguiente pagina
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

        status, cuerpo = registrar_usuario(datos)
        if status == 201:
            flash('Te registraste con éxito. Ya podés iniciar sesión.', 'exito')
            return redirect(url_for('users.login'))

        error = mensaje_error(status, cuerpo, 'No se pudo crear la cuenta.')
        return render_template('registro.html', error=error, nombre=datos['nombre'], apellido=datos['apellido'], email=datos['email'])

    return render_template("registro.html")

@users_bp.route("/logout", methods=['POST'])
def logout():
    if esta_logueado():
        cerrar_sesion()
    session.clear()
    flash('Sesión cerrada con éxito.', 'exito')
    return redirect(url_for('peliculas.inicio'))

@users_bp.route("/perfil")
@solo_logueado
def profile():
    #pedir datos del usuario y sus reservas al backend
    status, usuario = obtener_mi_usuario()
    if status in (401, 404):  # token vencido: se limpia la sesion para no quedar "logueado" sin poder consultar
        session.clear()
        return redirect(url_for('users.login'))
    if status != 200:
        abortar_por_status(status)

    perfil = {
        'nombre': usuario['nombre'],
        'apellido': usuario['apellido'],
        'email': usuario['email'],
        'anio_registro': formatear_fecha(usuario.get('fecha_registro'), '%Y'),
    }

    # las reservas del perfil las devuelve /usuarios/me/reservas (solo clientes; 204 = sin reservas)
    reservas_api = []
    if es_cliente():
        status_reservas, cuerpo_reservas = listar_mis_reservas()
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
@solo_logueado
def actualizar_perfil():
    datos = {campo: request.form.get(campo, '').strip() for campo in ('nombre', 'apellido', 'email')}

    status, _ = actualizar_usuario(session['usuario']['id'], datos)
    if status == 204:
        session['usuario'] = {**session['usuario'], 'nombre': datos['nombre']}  # el navbar muestra el nombre
    return redirect(url_for('users.profile'))


@users_bp.route("/perfil/contrasenia", methods=['GET', 'POST'])
@solo_logueado
def cambiar_contrasenia():
    if request.method == 'POST':
        actual = request.form.get('actual', '')
        nueva = request.form.get('nueva', '')
        repetir = request.form.get('repetir', '')

        _, error = validar_cambio_contrasenia(actual, nueva, repetir)

        if error is None:
            # el back verifica la actual, rechaza una nueva igual y cierra las sesiones anteriores
            status, cuerpo = actualizar_contrasenia(actual, nueva)
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

@users_bp.route("/perfil/resenas")
@solo_logueado
def mis_resenas():
    if not es_cliente():
        return redirect(url_for('users.profile'))

    status, cuerpo = listar_mis_resenas()
    if status not in (200, 204):
        flash(mensaje_error(status, cuerpo, 'No se pudieron cargar tus reseñas.'), 'error')
        return redirect(url_for('users.profile'))

    resenas = cuerpo.get('resenas', [])
    for r in resenas:
        r['fecha_texto'] = formatear_fecha(r.get('fecha'), '%d/%m/%Y', '')

    return render_template('mis_resenas.html', resenas=resenas)