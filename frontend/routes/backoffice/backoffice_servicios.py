from flask import render_template, redirect, url_for, request, flash
from api_cliente import llamar_api, mensaje_error
from routes.roles import es_admin
from routes.backoffice.backoffice import backoffice_bp


@backoffice_bp.route("/backoffice/servicios", methods=["GET", "POST"]) # asocio servicios_admin al bp backoffice
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

    ver_inactivos = request.args.get("estado") == "inactivos"
    filtro = "false" if ver_inactivos else "true"
    status, datos = llamar_api("GET", f"/servicios?_limit=100&activo={filtro}")

    return render_template(
        "backadmin/servicios_adicionales.html",
        servicios=datos.get("servicios", []) if status in (200, 204) else [],
        error=None if status in (200, 204) else mensaje_error(status, datos, "No se pudieron obtener los servicios."),
        error_alta=error_alta,
        ver_inactivos=ver_inactivos
    )

@backoffice_bp.route("/backoffice/servicios/<int:servicio_id>/estado", methods=["POST"])
def servicios_estado(servicio_id):
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))
    activo = request.form.get("activo") == "true"
    accion = "dado de alta" if activo else "dado de baja"
    status, cuerpo = llamar_api("PATCH", f"/servicios/{servicio_id}", {"activo": activo})
    if status == 204:
        flash(f"Servicio {accion}.", "ok")
    else:
        flash(mensaje_error(status, cuerpo, f"No se pudo dejar el servicio {accion}."), "error")
    if activo:
        return redirect(url_for("backoffice.servicios_admin", estado="inactivos"))
    return redirect(url_for("backoffice.servicios_admin"))

@backoffice_bp.route("/backoffice/servicios/<int:servicio_id>/editar", methods=["GET", "POST"])
def servicios_editar(servicio_id):
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))

    error = None

    if request.method == "POST":
        precio = request.form.get("precio", "").strip()

        if not precio.isdigit():
            error = "El precio debe ser un número entero."
        else:
            cambios = {
                "nombre": request.form.get("nombre", "").strip(),
                "descripcion": request.form.get("descripcion", "").strip() or None,
                "precio": int(precio),
                "activo": "activo" in request.form,
            }
            status, cuerpo = llamar_api("PATCH", f"/servicios/{servicio_id}", cambios)

            if status == 204:
                return redirect(url_for("backoffice.servicios_admin"))

            error = mensaje_error(status, cuerpo, "No se pudo guardar el servicio.")

    status, servicio = llamar_api("GET", f"/servicios/{servicio_id}")

    if status != 200:
        return redirect(url_for("backoffice.servicios_admin"))

    return render_template(
        "backadmin/servicios_editar.html",
        servicio=servicio,
        error=error
    )
