from flask import render_template, redirect, url_for, flash, request
from api_cliente import llamar_api, mensaje_error
from datos_perfil import formatear_fecha
from routes.products import obtener_listado
from routes.roles import solo_admin
from routes.backoffice.backoffice import backoffice_bp


@backoffice_bp.route("/backoffice/funciones")
@solo_admin
def funciones_admin():
    funciones, error = obtener_listado("funciones", "funciones")
    for f in funciones:
        f["fecha_texto"] = formatear_fecha(f["fecha_hora"], "%d/%m/%Y %H:%M")
    return render_template("backadmin/funciones.html", funciones=funciones, error=error)


def _formulario(funcion=None, error=None):
    peliculas, err_p = obtener_listado("peliculas", "peliculas", "&activa=true")
    salas, err_s = obtener_listado("salas", "salas")
    return render_template("backadmin/funcion_form.html", funcion=funcion,
                           peliculas=peliculas, salas=salas, error=error or err_p or err_s)


def _leer_formulario():
    return {c: request.form.get(c, "").strip() for c in ("pelicula_id", "sala_id", "fecha_hora", "precio")}


def _payload(valores):
    # El backend exige precio entero; si no es numérico lo manda tal cual y él lo rechaza.
    precio = valores["precio"]
    return {**valores, "precio": int(precio) if precio.isdigit() else precio}


@backoffice_bp.route("/backoffice/funciones/nueva", methods=["GET", "POST"])
@solo_admin
def nueva_funcion():
    if request.method == "GET":
        return _formulario()
    valores = _leer_formulario()
    status, cuerpo = llamar_api("POST", "/funciones", _payload(valores))
    if status == 201:
        flash("Función creada.", "ok")
        return redirect(url_for("backoffice.funciones_admin"))
    return _formulario(valores, mensaje_error(status, cuerpo, "No se pudo crear la función."))


@backoffice_bp.route("/backoffice/funciones/<int:funcion_id>/editar", methods=["GET", "POST"])
@solo_admin
def editar_funcion(funcion_id):
    if request.method == "GET":
        status, funcion = llamar_api("GET", f"/funciones/{funcion_id}")
        if status != 200:
            flash(mensaje_error(status, funcion, "No se pudo obtener la función."), "error")
            return redirect(url_for("backoffice.funciones_admin"))
        funcion["fecha_hora"] = funcion["fecha_hora"][:16]  # formato de datetime-local
        return _formulario(funcion)
    valores = _leer_formulario()
    status, cuerpo = llamar_api("PATCH", f"/funciones/{funcion_id}", _payload(valores))
    if status == 204:
        flash("Función actualizada.", "ok")
        return redirect(url_for("backoffice.funciones_admin"))
    return _formulario({**valores, "id": funcion_id},
                       mensaje_error(status, cuerpo, "No se pudo actualizar la función."))