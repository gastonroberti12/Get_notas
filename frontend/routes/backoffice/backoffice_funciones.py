from flask import render_template, redirect, url_for, flash, request
from services.api_cliente import mensaje_error
from services.funciones import listar_funciones, obtener_funcion, crear_funcion, actualizar_funcion, actualizar_estado_funcion
from services.peliculas import listar_peliculas
from services.salas import listar_salas
from logica.formato import FORMATO_INPUT_FECHA, a_iso_gmt3, ahora_argentina, formatear_fecha, parsear_fecha
from logica.roles import solo_admin
from logica.validaciones import validar_entero
from routes.backoffice.backoffice import backoffice_bp, cambiar_estado, ver_inactivos
from routes.errores import abortar_por_status


@backoffice_bp.route("/backoffice/funciones")
@solo_admin
def funciones_admin():
    inactivos = ver_inactivos()
    status, datos = listar_funciones("&activa=false" if inactivos else "&activa=true")
    funciones = datos.get("funciones", [])
    error = None
    if status not in (200, 204):
        error = mensaje_error(status, datos, "No se pudieron obtener los datos.")
    ahora = ahora_argentina()
    for f in funciones:
        f["fecha_texto"] = formatear_fecha(f["fecha_hora"], "%d/%m/%Y %H:%M")
        # las funciones que ya pasaron no se pueden volver a dar de alta.
        fecha = parsear_fecha(f["fecha_hora"])
        f["pasada"] = fecha is not None and fecha < ahora
    return render_template("backadmin/funciones.html", funciones=funciones, error=error, ver_inactivos=inactivos)

def _formulario(funcion=None, error=None):
    # el formulario necesita las peliculas activas y las salas para los <select>.
    status_p, datos_p = listar_peliculas("&activa=true")
    status_s, datos_s = listar_salas()
    if error is None and status_p not in (200, 204):
        error = mensaje_error(status_p, datos_p, "No se pudieron obtener los datos.")
    if error is None and status_s not in (200, 204):
        error = mensaje_error(status_s, datos_s, "No se pudieron obtener los datos.")
    return render_template("backadmin/funcion_form.html", funcion=funcion,
                           peliculas=datos_p.get("peliculas", []), salas=datos_s.get("salas", []), error=error)


def _leer_formulario():
    return {c: request.form.get(c, "").strip() for c in ("pelicula_id", "sala_id", "fecha_hora", "precio")}


def _payload(valores):
    # arma los datos para el backend: precio entero y fecha con la zona argentina. devuelve (datos, error)
    precio, error = validar_entero(valores["precio"], "El precio debe ser un número entero.")
    return {**valores, "precio": precio, "fecha_hora": a_iso_gmt3(valores["fecha_hora"])}, error


@backoffice_bp.route("/backoffice/funciones/nueva", methods=["GET", "POST"])
@solo_admin
def nueva_funcion():
    if request.method == "GET":
        return _formulario()
    valores = _leer_formulario()
    datos, error = _payload(valores)
    if error:
        return _formulario(valores, error)
    status, cuerpo = crear_funcion(datos)
    if status == 201:
        flash("Función creada.", "exito")
        return redirect(url_for("backoffice.funciones_admin"))
    return _formulario(valores, mensaje_error(status, cuerpo, "No se pudo crear la función."))


@backoffice_bp.route("/backoffice/funciones/<int:funcion_id>/editar", methods=["GET", "POST"])
@solo_admin
def editar_funcion(funcion_id):
    if request.method == "GET":
        status, funcion = obtener_funcion(funcion_id)
        if status != 200:
            abortar_por_status(status)
        funcion["fecha_hora"] = formatear_fecha(funcion["fecha_hora"], FORMATO_INPUT_FECHA, "")
        return _formulario(funcion)
    valores = _leer_formulario()
    datos, error = _payload(valores)
    if error:
        return _formulario({**valores, "id": funcion_id}, error)
    status, cuerpo = actualizar_funcion(funcion_id, datos)
    if status == 204:
        flash("Función actualizada.", "exito")
        return redirect(url_for("backoffice.funciones_admin"))
    return _formulario({**valores, "id": funcion_id},
                       mensaje_error(status, cuerpo, "No se pudo actualizar la función."))

@backoffice_bp.route("/backoffice/funciones/<int:funcion_id>/estado", methods=["POST"])
@solo_admin
def cambiar_estado_funcion(funcion_id):
    return cambiar_estado(actualizar_estado_funcion, funcion_id, "Función dada", "backoffice.funciones_admin")