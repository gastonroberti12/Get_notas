from flask import Blueprint, flash, redirect, request, session, url_for
from sucursales import obtener_sucursales

cines_bp = Blueprint("cines", __name__)

# Guarda en la session la sucursal elegida y vuelve a la página anterior.
@cines_bp.route("/sucursal/<int:sucursal_id>")
def elegir_sucursal(sucursal_id):
    existe = False
    for sucursal in obtener_sucursales():
        if sucursal["id"] == sucursal_id:
            existe = True
    if existe:
        session["sucursal_id"] = sucursal_id
    else:
        flash("La sucursal elegida no existe.", "error")
    return redirect(request.referrer or url_for("peliculas.inicio"))