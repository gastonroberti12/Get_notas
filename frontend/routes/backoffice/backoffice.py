from flask import Blueprint, render_template, redirect, url_for, flash , request
from routes.roles import es_admin
from api_cliente import llamar_api, mensaje_error
from dashboard import armar_dashboard
from routes.products import obtener_listado

backoffice_bp = Blueprint("backoffice", __name__)

def ver_inactivos():
    # True si la URL pide la pestaña de dados de baja (?estado=inactivos).
    return request.args.get("estado") == "inactivos"



def cambiar_estado(endpoint, nombre, listado):
    # Da de alta o de baja un recurso con PATCH {"activa": ...} y vuelve a su listado.
    activa = request.form.get("activa") == "true"
    status, cuerpo = llamar_api("PATCH", endpoint, {"activa": activa})
    if status == 204:
        flash(f"{nombre} dada de {'alta' if activa else 'baja'}.", "ok")
    else:
        flash(mensaje_error(status, cuerpo, "No se pudo cambiar el estado."), "error")
    if activa:
        return redirect(url_for(listado, estado="inactivos"))
    return redirect(url_for(listado))

@backoffice_bp.route("/backoffice")
def panel():
    if not es_admin():
        # return render_template("403.html"), 403  , cuando exista el manejo de errores
        return redirect(url_for('peliculas.inicio'))
    resumen = armar_dashboard({}, ("ocupacion", "entradas", "importe", "cancelaciones", "generos", "franjas"))
    return render_template("backadmin/panel.html", d=resumen)

@backoffice_bp.route("/backoffice/locales")
def locales_admin():

    if not es_admin():
        return redirect(url_for("peliculas.inicio"))

    return render_template("backadmin/locales.html")


@backoffice_bp.route("/backoffice/salas")
def salas_admin():

    if not es_admin():
        return redirect(url_for("peliculas.inicio"))

    # Solo lectura: las salas vienen predefinidas. obtener_listado ya pide _limit=100
    # y, si el backend falla, devuelve ([], mensaje de error) en vez de explotar.
    salas, error = obtener_listado("salas", "salas")
    return render_template("backadmin/salas.html", salas=salas, error=error)

