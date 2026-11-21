from flask import render_template, redirect, url_for, request
from services.api_cliente import mensaje_error
from services.servicios import listar_servicios, obtener_servicio, crear_servicio, actualizar_servicio, actualizar_estado_servicio
from logica.roles import solo_admin
from logica.validaciones import validar_entero
from routes.backoffice.backoffice import backoffice_bp, cambiar_estado, ver_inactivos
from routes.errores import abortar_por_status


def _payload():
    # Lee el formulario de alta o edición y arma los datos para el backend. Devuelve (datos, error).
    precio, error = validar_entero(request.form.get("precio"), "El precio debe ser un número entero.")
    datos = {
        "nombre": request.form.get("nombre", "").strip(),
        "descripcion": request.form.get("descripcion", "").strip() or None,
        "precio": precio,
        "activo": "activo" in request.form,
    }
    return datos, error


@backoffice_bp.route("/backoffice/servicios", methods=["GET", "POST"]) # asocio servicios_admin al bp backoffice
@solo_admin
def servicios_admin(): 
    error_alta = None

    if request.method == "POST":
        nuevo, error_alta = _payload()

        if error_alta is None:
            status, cuerpo = crear_servicio(nuevo)

            if status == 201:
                return redirect(url_for("backoffice.servicios_admin"))

            error_alta = mensaje_error(status, cuerpo, "No se pudo crear el servicio.")

    inactivos = ver_inactivos()
    status, datos = listar_servicios("&activo=false" if inactivos else "&activo=true")
    servicios = datos.get("servicios", [])
    error = None
    if status not in (200, 204):
        error = mensaje_error(status, datos, "No se pudieron obtener los servicios.")

    return render_template(
        "backadmin/servicios_adicionales.html",
        servicios=servicios,
        error=error,
        error_alta=error_alta,
        ver_inactivos=inactivos
    )

@backoffice_bp.route("/backoffice/servicios/<int:servicio_id>/estado", methods=["POST"])
@solo_admin
def servicios_estado(servicio_id):
    return cambiar_estado(actualizar_estado_servicio, servicio_id, "Servicio dado", "backoffice.servicios_admin")

@backoffice_bp.route("/backoffice/servicios/<int:servicio_id>/editar", methods=["GET", "POST"])
@solo_admin
def servicios_editar(servicio_id):
    error = None

    if request.method == "POST":
        cambios, error = _payload()

        if error is None:
            status, cuerpo = actualizar_servicio(servicio_id, cambios)

            if status == 204:
                return redirect(url_for("backoffice.servicios_admin"))

            error = mensaje_error(status, cuerpo, "No se pudo guardar el servicio.")

    status, servicio = obtener_servicio(servicio_id)

    if status != 200:
        abortar_por_status(status)

    return render_template(
        "backadmin/servicios_editar.html",
        servicio=servicio,
        error=error
    )