from flask import Blueprint, render_template, redirect, url_for, flash , request
from logica.roles import solo_admin
from services.api_cliente import mensaje_error
from services.salas import listar_salas
from logica.dashboard import armar_dashboard

backoffice_bp = Blueprint("backoffice", __name__)

def ver_inactivos():
    # True si la URL pide la pestaña de dados de baja (?estado=inactivos).
    return request.args.get("estado") == "inactivos"


def cambiar_estado(actualizar_estado, recurso_id, texto_exito, listado):
    # Alta y baja común de películas, funciones y servicios.
    # actualizar_estado es la función de services que manda el PATCH (por ejemplo, actualizar_estado_funcion).
    # El formulario manda activa=true para dar de alta y activa=false para dar de baja.
    activa = request.form.get("activa") == "true"
    status, cuerpo = actualizar_estado(recurso_id, activa)
    if status == 204:
        flash(f"{texto_exito} de {'alta' if activa else 'baja'}.", "exito")
    else:
        flash(mensaje_error(status, cuerpo, "No se pudo cambiar el estado."), "error")
    if activa:
        return redirect(url_for(listado, estado="inactivos"))
    return redirect(url_for(listado))

@backoffice_bp.route("/backoffice")
@solo_admin
def panel():
    resumen = armar_dashboard({}, ("ocupacion", "entradas", "importe", "cancelaciones", "generos", "franjas"))
    return render_template("backadmin/panel.html", d=resumen)


@backoffice_bp.route("/backoffice/salas")
@solo_admin
def salas_admin():
    # Solo lectura: las salas vienen predefinidas.
    status, datos = listar_salas()
    salas = datos.get("salas", [])
    error = None
    if status not in (200, 204):
        error = mensaje_error(status, datos, "No se pudieron obtener los datos.")
    return render_template("backadmin/salas.html", salas=salas, error=error)