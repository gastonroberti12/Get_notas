from flask import Blueprint, redirect, url_for, render_template, flash, request
from services.api_cliente import mensaje_error
from services.funciones import obtener_funcion, obtener_butacas_disponibles
from services.reservas import crear_reserva, obtener_reserva, listar_entradas, agregar_servicio, pagar_reserva, solicitar_cancelacion
from services.salas import listar_butacas
from services.servicios import listar_servicios
from services.usuarios import listar_mis_reservas
from logica.formato import formatear_numero, formatear_fecha
from logica.roles import solo_logueado
from logica.validaciones import validar_butacas, validar_cantidades_servicios, SERVICIOS_POR_ENTRADA
from routes.errores import abortar_por_status

purchases_bp = Blueprint("purchases", __name__)


@purchases_bp.route("/reservas/<int:reserva_id>/cancelar", methods=['GET', 'POST'])
@solo_logueado
def cancelar_reserva(reserva_id):
    if request.method == 'GET':
        return render_template('cancelar_reserva.html', reserva_id=reserva_id)
        # El back valida titularidad y la regla de 1 hora, salga bien o mal, vuelve al inicio con el mensaje
    status, cuerpo = solicitar_cancelacion(reserva_id)
    if status in (200, 204):
        flash('Reserva cancelada con éxito.', 'exito')
    else:
        flash(mensaje_error(status, cuerpo, 'No se pudo cancelar la reserva.'), 'error')
    return redirect(url_for('peliculas.inicio'))

@purchases_bp.route("/funciones/<int:funcion_id>/butacas", methods=["GET", "POST"])
@solo_logueado  
def seleccion_butacas(funcion_id):
    """Muestra el mapa de butacas de una función (GET) y crea la reserva con las elegidas (POST).
    Si el usuario ya tiene una reserva pendiente para esta función, la recupera y marca sus butacas."""

    # Datos de la función (sala, precio, fecha). Si no existe -> página de error
    status, funcion = obtener_funcion(funcion_id)
    if status != 200:
        abortar_por_status(status)

    # reserva_id solo viene en la URL cuando volvés desde el checkout ("Volver a mis butacas")
    reserva_id = request.args.get("reserva_id", type=int)
    reserva_pendiente = None   
    asientos_ids = set()       

   #busca si ya tenés una reserva pendiente, para ESTA función, así no se crea otra y te muestra las butacas que ya habías elegido
    if request.method == "GET" and not reserva_id:
        status_pendientes, datos_pendientes = listar_mis_reservas("&estado=pendiente")
        if status_pendientes == 200:
            reserva_actual = next(
                (reserva for reserva in datos_pendientes.get("reservas", [])
                 if int(reserva["funcion_id"]) == funcion_id),
                None,
            )
            if reserva_actual is not None:
                reserva_id = int(reserva_actual["id"])

    # POST al continuar al pago
    if request.method == "POST":
        # Llegan como texto "12,13,14" en un input oculto (lo llena el JS); se pasan a lista de ints
        butaca_ids, error = validar_butacas(request.form.get("butacas"))
        if error:
            flash(error, "error")
            return redirect(url_for("purchases.seleccion_butacas", funcion_id=funcion_id))

        # POST  crea la reserva "pendiente" (el back controla que no estén ocupadas)
        status_reserva, reserva = crear_reserva(funcion_id, butaca_ids)
        if status_reserva == 201:
            return redirect(url_for("purchases.checkout", reserva_id=reserva["id"], funcion_id=funcion_id))

        # Falló (ej. 409: alguien te ganó una butaca) -> aviso y vuelve a mostrar el mapa
        flash(mensaje_error(status_reserva, reserva, "No se pudo crear la reserva."), "error")
        return redirect(url_for("purchases.seleccion_butacas", funcion_id=funcion_id))

    # GET con una reserva previa: según su estado, la recupera o avisa qué pasó
    if reserva_id:
        status_reserva, reserva = obtener_reserva(reserva_id)
        if status_reserva == 404:
            flash("La reserva ya no está disponible. Elegí las butacas nuevamente.", "error")
        elif status_reserva != 200:
            abortar_por_status(status_reserva)
        elif int(reserva["funcion_id"]) != funcion_id:   # la reserva es de otra función (URL manipulada)
            abortar_por_status(404)
        elif reserva["estado"] == "pendiente":
            # Sigue sin pagar: trae sus entradas para marcar esas butacas como "tuyas" en el mapa
            status_entradas, datos_entradas = listar_entradas(reserva_id)
            if status_entradas != 200:
                abortar_por_status(status_entradas)
            asientos_ids = {int(entrada["butaca_id"]) for entrada in datos_entradas.get("entradas", [])}
            reserva_pendiente = reserva
        elif reserva["estado"] == "expirada":
            # Pasaron los minutos para pagar: las butacas se liberaron, elegí de nuevo
            flash("Venció el plazo de pago. Las butacas quedaron disponibles para volver a elegirlas.", "error")
        else:
            # Ya está pagada o cancelada: no tiene sentido volver a elegir butacas
            flash("La reserva ya no está pendiente de pago.", "error")
            return redirect(url_for("users.profile"))

    # Para dibujar la sala hacen falta dos listas del backend:
    # las DISPONIBLES de esta función y TODAS las butacas de la sala
    status_butacas, disponibles = obtener_butacas_disponibles(funcion_id)   # GET /funciones/<id>/butacas
    if status_butacas != 200:
        abortar_por_status(status_butacas)

    status_todas, cuerpo_todas = listar_butacas(funcion["sala_id"])         # GET /salas/<id>/butacas
    if status_todas != 200:
        abortar_por_status(status_todas)

    # Arma los datos del mapa
    todas = cuerpo_todas.get("butacas", [])
    disponibles_ids = {int(b["id"]) for b in disponibles}
    filas = sorted({b["fila"] for b in todas})                     # ["A", "B", "C", ...] sin repetir
    butacas_por_fila = {                                           # {"A": [A1, A2, ...], "B": [...]}
        fila: sorted((b for b in todas if b["fila"] == fila), key=lambda b: int(b["numero"]))
        for fila in filas
    }
    ocupadas_ids = {int(b["id"]) for b in todas if int(b["id"]) not in disponibles_ids}   # ocupada = no disponible
    asientos_reservados = [                                        # ["F5", "F6"]: las de tu reserva pendiente
        f"{butaca['fila']}{butaca['numero']}"
        for butaca in todas
        if reserva_pendiente and int(butaca["id"]) in asientos_ids
    ]

    return render_template(
        "seleccion_butacas.html",
        funcion_id=funcion_id,
        funcion=funcion,
        fecha_funcion=formatear_fecha(funcion.get("fecha_hora"), "%d/%m/%Y"),
        hora_funcion=formatear_fecha(funcion.get("fecha_hora"), "%H:%M"),
        filas=filas,
        butacas=todas,
        butacas_por_fila=butacas_por_fila,
        ocupadas_ids=ocupadas_ids,
        reserva_pendiente=reserva_pendiente,
        asientos_reservados=asientos_reservados,
        precio=float(funcion["precio"]),
    )


@purchases_bp.route("/checkout", methods=["GET", "POST"])
@solo_logueado
def checkout():
    """GET: muestra el resumen, los servicios y el formulario de pago de una reserva pendiente.
    POST: agrega los servicios elegidos y paga con POST /reservas/<id>/pago; si sale bien va al perfil."""
    reserva_id = request.args.get("reserva_id", type=int)
    if not reserva_id:
        return redirect(url_for("peliculas.inicio"))

    if request.method == "POST":
        # Se consultan las entradas porque el tope de servicios depende de cuántas entradas tiene la reserva
        status_entradas, datos_entradas = listar_entradas(reserva_id)

        if status_entradas != 200:
            flash("No se pudieron verificar las entradas.", "error")
            return redirect(url_for(
                "purchases.checkout",
                reserva_id=reserva_id
            ))

        cantidad_entradas = len(datos_entradas.get("entradas", []))

        if cantidad_entradas == 0:
            flash("La reserva no tiene entradas.", "error")
            return redirect(url_for(
                "purchases.checkout",
                reserva_id=reserva_id
            ))
        # las cantidades se validan en logica/validaciones.py
        cantidades, error = validar_cantidades_servicios(request.form, cantidad_entradas)
        if error:
            flash(error, "error")
            return redirect(url_for(
                "purchases.checkout",
                reserva_id=reserva_id
            ))

        # Agrega los servicios uno por uno (solo los de cantidad > 0) antes de pagar
        for servicio_id, cantidad in cantidades.items():

            if cantidad > 0:

                status_servicio, _ = agregar_servicio(reserva_id, servicio_id, cantidad)

                if status_servicio != 201:
                    flash("No se pudo agregar un servicio adicional.", "error")
                    return redirect(url_for(
                        "purchases.checkout",
                        reserva_id=reserva_id
                    ))

        # Body del pago con los campos de la tarjeta del formulario
        datos_pago = {
            campo: request.form.get(campo, "")
            for campo in ("titular", "numero_tarjeta", "mes_vencimiento", "anio_vencimiento", "cvv")
        }
        status, cuerpo = pagar_reserva(reserva_id, datos_pago)
        if status == 200:
            flash("Pago confirmado. La reserva quedó creada.", "exito")
            if not cuerpo.get("mail_enviado", True):
                flash("Tus entradas están en tu perfil.", "exito")
            return redirect(url_for("users.profile"))
        # El pago falló: se consulta la reserva para saber si fue porque expiró (y entonces volver a butacas)
        status_reserva, reserva_actual = obtener_reserva(reserva_id)
        if status_reserva == 200 and reserva_actual["estado"] == "expirada":
            flash("Venció el plazo de pago de 8 minutos. Elegí nuevamente tus butacas.", "error")
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

    # GET: solo se puede pagar una reserva pendiente; si expiró se vuelve a elegir butacas, si no al perfil
    status_reserva, reserva = obtener_reserva(reserva_id)
    if status_reserva != 200:
        abortar_por_status(status_reserva)
    if reserva["estado"] == "expirada":
        flash("Venció el plazo de pago de 8 minutos. Elegí nuevamente tus butacas.", "error")
        return redirect(url_for(
            "purchases.seleccion_butacas",
            funcion_id=reserva["funcion_id"],
        ))
    if reserva["estado"] != "pendiente":
        flash("La reserva ya no está pendiente de pago.", "error")
        return redirect(url_for("users.profile"))

    # Datos para la página: la función (precio), cuántas entradas tiene y los servicios activos con precio formateado
    status_funcion, funcion = obtener_funcion(reserva["funcion_id"])
    if status_funcion != 200:
        abortar_por_status(status_funcion)

    status_entradas, entradas_data = listar_entradas(reserva_id)
    entradas = entradas_data.get("entradas", []) if status_entradas == 200 else []

    status_servicios, servicios_data = listar_servicios("&activo=true")
    servicios = servicios_data.get("servicios", []) if status_servicios == 200 else []
    for servicio in servicios:
        servicio["precio_formateado"] = formatear_numero(servicio["precio"])

    return render_template(
        "checkout.html",
        reserva=reserva,
        funcion=funcion,
        entradas=len(entradas),
        precio_entrada=float(funcion["precio"]),
        servicios=servicios,
        servicios_por_entrada=SERVICIOS_POR_ENTRADA,
    )
