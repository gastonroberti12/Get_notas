from flask import render_template, redirect, url_for, flash
from api_cliente import llamar_api, mensaje_error
from routes.roles import es_admin
from routes.backoffice.backoffice import backoffice_bp


@backoffice_bp.route("/backoffice/peliculas")
def peliculas_admin():
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))
    status, datos = llamar_api("GET", "/peliculas?_limit=100")
    if status not in (200, 204):
        error = mensaje_error(status, datos, "No se pudieron obtener las películas.")
        return render_template("backadmin/peliculas_listado.html", peliculas=[], error=error)
    return render_template("backadmin/peliculas_listado.html",
                           peliculas=datos.get("peliculas", []), error=None)


@backoffice_bp.route("/backoffice/peliculas/nueva")
def nueva_pelicula():
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))
    return render_template("backadmin/subirpelicula.html")


@backoffice_bp.route("/backoffice/peliculas/<int:pelicula_id>/baja", methods=["POST"])
def baja_pelicula(pelicula_id):
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))
    status, datos = llamar_api("DELETE", f"/peliculas/{pelicula_id}")
    if status == 204:
        flash("Película dada de baja.", "ok")
    else:
        flash(mensaje_error(status, datos, "No se pudo dar de baja la película."), "error")
    return redirect(url_for("backoffice.peliculas_admin"))