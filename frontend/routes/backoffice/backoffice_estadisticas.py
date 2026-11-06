from flask import render_template, request
from dashboard import armar_dashboard, leer_filtros
from routes.roles import solo_admin
from routes.backoffice.backoffice import backoffice_bp


@backoffice_bp.route("/backoffice/estadisticas")
@solo_admin
def estadisticas_admin():
    filtros = leer_filtros(request.args)
    return render_template("backadmin/estadisticas.html", filtros=filtros, d=armar_dashboard(filtros, SECCIONES_COMPLETAS))