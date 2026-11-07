from flask import Blueprint, redirect, url_for, render_template, flash, request, abort
from api_cliente import llamar_api, mensaje_error
from datos_perfil import formatear_total
from routes.roles import esta_logueado

purchases_bp = Blueprint("purchases", __name__)


@purchases_bp.route("/reservas/<int:reserva_id>/cancelar", methods=['GET', 'POST'])
def cancelar_reserva(reserva_id):
    if not esta_logueado():
        return redirect(url_for('users.login', next=request.path))
    if request.method == 'GET':
        return render_template('cancelar_reserva.html', reserva_id=reserva_id)
    # El back valida titularidad y la regla de 1 hora; si responde error, el perfil se recarga igual.
    status, cuerpo = llamar_api('PATCH', f'/reservas/{reserva_id}', {'estado': 'cancelada'})
    if status in (200, 204):
        flash('Reserva cancelada con éxito.', 'exito')
    else:
        flash(mensaje_error(status, cuerpo, 'No se pudo cancelar la reserva.'), 'error')
    return redirect(url_for('users.profile'))

@purchases_bp.route("/funciones/<int:funcion_id>/butacas", methods=["GET", "POST"])
def seleccion_butacas(funcion_id):
    if not esta_logueado():
        return redirect(url_for('users.login'))

    status, funcion = llamar_api("GET", f"/funciones/{funcion_id}")
    if status == 404:
        abort(404)
    if status != 200:
        abort(503)

    reserva_id = request.args.get("reserva_id", type=int)
    reserva_pendiente = None
    asientos_ids = set()

    if request.method == "GET" and not reserva_id:
        status_pendientes, datos_pendientes = llamar_api(
            "GET", "/usuarios/me/reservas?estado=pendiente&_limit=100"
        )
        if status_pendientes == 200:
            reserva_actual = next(
                (
                    reserva
                    for reserva in datos_pendientes.get("reservas", [])
                    if int(reserva["funcion_id"]) == funcion_id
                ),
                None,
            )
            if reserva_actual is not None:
                reserva_id = int(reserva_actual["id"])

    if request.method == "POST":
        texto_ids = request.form.get("butacas", "").strip()
        try:
            butaca_ids = [int(valor) for valor in texto_ids.split(",") if valor.strip()]
        except ValueError:
            flash("Las butacas seleccionadas no son válidas.", "error")
            return redirect(url_for("purchases.seleccion_butacas", funcion_id=funcion_id))

        if not butaca_ids:
            flash("Seleccioná al menos una butaca.", "error")
            return redirect(url_for("purchases.seleccion_butacas", funcion_id=funcion_id))

        status_reserva, reserva = llamar_api(
            "POST",
            "/reservas",
            {"funcion_id": funcion_id, "butaca_ids": butaca_ids},
        )
        if status_reserva == 201:
            return redirect(url_for(
                "purchases.checkout",
                reserva_id=reserva["id"],
                funcion_id=funcion_id,
            ))

        flash(mensaje_error(status_reserva, reserva, "No se pudo crear la reserva."), "error")
        return redirect(url_for("purchases.seleccion_butacas", funcion_id=funcion_id))

    if reserva_id:
        status_reserva, reserva = llamar_api("GET", f"/reservas/{reserva_id}")
        if status_reserva == 403:
            abort(403)
        if status_reserva == 404:
            flash("La reserva ya no está disponible. Elegí las butacas nuevamente.", "error")
        elif status_reserva != 200:
            abort(status_reserva or 503)
        elif int(reserva["funcion_id"]) != funcion_id:
            abort(404)
        elif reserva["estado"] == "pendiente":
            status_entradas, datos_entradas = llamar_api(
                "GET", f"/reservas/{reserva_id}/entradas?_limit=100"
            )
            if status_entradas != 200:
                abort(status_entradas or 503)
            asientos_ids = {
                int(entrada["butaca_id"])
                for entrada in datos_entradas.get("entradas", [])
            }
            reserva_pendiente = reserva
        elif reserva["estado"] == "expirada":
            flash("Venció el plazo de pago. Las butacas quedaron disponibles para volver a elegirlas.", "error")
        else:
            flash("La reserva ya no está pendiente de pago.", "error")
            return redirect(url_for("users.profile"))

    status_butacas, disponibles = llamar_api(
        "GET", f"/funciones/{funcion_id}/butacas"
    )
    if status_butacas != 200:
        abort(503)

    status_todas, cuerpo_todas = llamar_api(
        "GET", f"/salas/{funcion['sala_id']}/butacas?_limit=100"
    )
    if status_todas != 200:
        abort(503)

    todas = cuerpo_todas.get("butacas", [])
    disponibles_ids = {int(b["id"]) for b in disponibles}
    filas = sorted({b["fila"] for b in todas})
    butacas_por_fila = {
        fila: sorted(
            (b for b in todas if b["fila"] == fila),
            key=lambda b: int(b["numero"]),
        )
        for fila in filas
    }
    ocupadas_ids = {int(b["id"]) for b in todas if int(b["id"]) not in disponibles_ids}
    asientos_reservados = [
        f"{butaca['fila']}{butaca['numero']}"
        for butaca in todas
        if reserva_pendiente and int(butaca["id"]) in asientos_ids
    ]

    return render_template(
        "seleccion_butacas.html",
        funcion_id=funcion_id,
        funcion=funcion,
        filas=filas,
        butacas=todas,
        butacas_por_fila=butacas_por_fila,
        ocupadas_ids=ocupadas_ids,
        reserva_pendiente=reserva_pendiente,
        asientos_reservados=asientos_reservados,
        precio=float(funcion["precio"]),
    )


@purchases_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    if not esta_logueado():
        return redirect(url_for("users.login"))

    reserva_id = request.args.get("reserva_id", type=int)
    if not reserva_id:
        return redirect(url_for("peliculas.inicio"))

    if request.method == "POST":
        for clave, cantidad_texto in request.form.items():
            if not clave.startswith("servicio_"):
                continue
            try:
                cantidad = int(cantidad_texto)
                servicio_id = int(clave.removeprefix("servicio_"))
            except ValueError:
                continue
            if cantidad <= 0:
                continue
            status_servicio, _ = llamar_api(
                "POST",
                f"/reservas/{reserva_id}/servicios",
                {"servicio_id": servicio_id, "cantidad": cantidad},
            )
            if status_servicio != 201:
                flash("No se pudo agregar un servicio adicional.", "error")
                return redirect(url_for(
                    "purchases.checkout",
                    reserva_id=reserva_id,
                    funcion_id=request.args.get("funcion_id"),
                ))

        datos_pago = {
            campo: request.form.get(campo, "")
            for campo in ("titular", "numero_tarjeta", "mes_vencimiento", "anio_vencimiento", "cvv")
        }
        status, cuerpo = llamar_api("POST", f"/reservas/{reserva_id}/pago", datos_pago)
        if status == 200:
            flash("Pago confirmado. La reserva quedó creada.", "exito")
            return redirect(url_for("users.profile"))
        status_reserva, reserva_actual = llamar_api("GET", f"/reservas/{reserva_id}")
        if status_reserva == 200 and reserva_actual["estado"] == "expirada":
            flash("Venció el plazo de pago de 10 minutos. Elegí nuevamente tus butacas.", "error")
            return redirect(url_for(
                "purchases.seleccion_butacas",
                funcion_id=reserva_actual["funcion_id"],
            ))
        flash(mensaje_error(status, cuerpo, "No se pudo confirmar el pago."), "error")
        return redirect(url_for(
            "purchases.checkout",
            reserva_id=reserva_id,
            funcion_id=request.args.get("funcion_id"),
        ))

    status_reserva, reserva = llamar_api("GET", f"/reservas/{reserva_id}")
    if status_reserva != 200:
        abort(status_reserva or 503)
    if reserva["estado"] == "expirada":
        flash("Venció el plazo de pago de 10 minutos. Elegí nuevamente tus butacas.", "error")
        return redirect(url_for(
            "purchases.seleccion_butacas",
            funcion_id=reserva["funcion_id"],
        ))
    if reserva["estado"] != "pendiente":
        flash("La reserva ya no está pendiente de pago.", "error")
        return redirect(url_for("users.profile"))

    status_funcion, funcion = llamar_api("GET", f"/funciones/{reserva['funcion_id']}")
    if status_funcion != 200:
        abort(status_funcion or 503)

    status_entradas, entradas_data = llamar_api(
        "GET", f"/reservas/{reserva_id}/entradas?_limit=100"
    )
    entradas = entradas_data.get("entradas", []) if status_entradas == 200 else []

    status_servicios, servicios_data = llamar_api("GET", "/servicios?_limit=100")
    servicios = servicios_data.get("servicios", []) if status_servicios == 200 else []
    for servicio in servicios:
        servicio["precio_formateado"] = formatear_total(servicio["precio"])

    return render_template(
        "checkout.html",
        reserva=reserva,
        funcion=funcion,
        entradas=len(entradas),
        precio_entrada=float(funcion["precio"]),
        servicios=servicios,
    )