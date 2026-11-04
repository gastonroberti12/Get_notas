from flask import render_template, redirect, url_for, request
from api_cliente import llamar_api, mensaje_error
from routes.roles import es_admin
from routes.backoffice.backoffice import backoffice_bp


@backoffice_bp.route("/backoffice/servicios", methods=["GET", "POST"])
def servicios_admin():
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))

    error_alta = None

    if request.method == "POST":
        precio = request.form.get("precio", "").strip()

        if not precio.isdigit():
            error_alta = "El precio debe ser un número entero."
        else:
            nuevo = {
                "nombre": request.form.get("nombre", "").strip(),
                "descripcion": request.form.get("descripcion", "").strip() or None,
                "precio": int(precio),
                "activo": "activo" in request.form,
            }
            status, cuerpo = llamar_api("POST", "/servicios", nuevo)

            if status == 201:
                return redirect(url_for("backoffice.servicios_admin"))

            error_alta = mensaje_error(status, cuerpo, "No se pudo crear el servicio.")

    status, datos = llamar_api("GET", "/servicios?_limit=100")

    return render_template(
        "backadmin/servicios_adicionales.html",
        servicios=datos.get("servicios", []) if status in (200, 204) else [],
        error=None if status in (200, 204) else mensaje_error(status, datos, "No se pudieron obtener los servicios."),
        error_alta=error_alta
    )
