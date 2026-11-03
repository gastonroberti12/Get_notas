from flask import Blueprint, render_template, redirect, url_for
from routes.roles import es_admin

backoffice_bp = Blueprint("backoffice", __name__)


@backoffice_bp.route("/backoffice")
def panel():
    if not es_admin():
        # return render_template("403.html"), 403  , cuando exista el manejo de errores
        return redirect(url_for('peliculas.inicio'))
    return render_template("backadmin/panel.html")