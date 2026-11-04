from flask import render_template, redirect, url_for
from api_cliente import llamar_api, mensaje_error
from routes.roles import es_admin
from routes.backoffice.backoffice import backoffice_bp


@backoffice_bp.route("/backoffice/servicios")
def servicios_admin():
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))

    status, datos = llamar_api("GET", "/servicios?_limit=100")

    if status not in (200, 204):
        return render_template(
            "backadmin/servicios_adicionales.html",
            servicios=[],
            error=mensaje_error(status, datos, "No se pudieron obtener los servicios.")
        )

    return render_template(
        "backadmin/servicios_adicionales.html",
        servicios=datos.get("servicios", []),
        error=None
    )
