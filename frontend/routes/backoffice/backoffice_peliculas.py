from flask import render_template, redirect, url_for
from routes.roles import es_admin
from routes.backoffice.backoffice import backoffice_bp


@backoffice_bp.route("/backoffice/peliculas")
def peliculas_admin():

    if not es_admin():
        return redirect(url_for("peliculas.inicio"))

    return render_template("backadmin/subirpelicula.html")