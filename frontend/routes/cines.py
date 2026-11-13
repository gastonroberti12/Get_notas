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
    mapas_embebidos = {
        "centro": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3534.1030948370526!2d-58.38976949938131!3d-34.60512090957393!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x95bccac4276b48d1%3A0xfee863ba373fb778!2sCine%20Lorca!5e1!3m2!1ses-419!2sar!4v1794351363046!5m2!1ses-419!2sar",
        "palermo": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2972.8839056683228!2d-58.4041545!3d-34.5752315!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x95bcb5656b045043%3A0x6e41a3e073094b9c!2sAtlas%20Cines%20Alcorta!5e1!3m2!1ses!2sar!4v1794579035919!5m2!1ses!2sar",
        "belgrano": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d11894.22883031673!2d-58.467474474007325!3d-34.55639922536786!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x95bcb42dc3d95ed9%3A0xbfcf33802627903c!2sCine%20Showcase%20Belgrano!5e1!3m2!1ses-419!2sar!4v1794351412196!5m2!1ses-419!2sar",
    }
    return render_template(
        "maps.html",
        sucursal_actual=sucursal_actual,
        mapa_url=mapas_embebidos.get(nombre),
    )