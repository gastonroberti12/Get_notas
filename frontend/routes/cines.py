from flask import Blueprint, flash, redirect, render_template, session, url_for
from sucursales import contexto_sucursales, obtener_sucursales

cines_bp = Blueprint("cines", __name__)


# Guarda la sucursal elegida y vuelve a la cartelera.
@cines_bp.route("/sucursal/<int:sucursal_id>")
def elegir_sucursal(sucursal_id):
    sucursales = obtener_sucursales()
    
    if any(sucursal["id"] == sucursal_id for sucursal in sucursales):
        session["sucursal_id"] = sucursal_id
    else:
        flash("La sucursal elegida no existe.", "error")

    return redirect(url_for("peliculas.inicio"))


@cines_bp.route("/maps")
def mapa():
    _, sucursal_actual = contexto_sucursales()
    nombre = (
        sucursal_actual.get("nombre", "").strip().casefold()
        if sucursal_actual
        else ""
    )
    plantillas = {
        "centro": "mapscentro.html",
        "palermo": "mapspalermo.html",
        "belgrano": "mapsbelgrano.html",
    }
    plantilla = plantillas.get(nombre, "maps.html")
    return render_template(plantilla, sucursal_actual=sucursal_actual)