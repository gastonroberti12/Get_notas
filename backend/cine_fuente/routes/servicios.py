
from flask import Blueprint, jsonify, request, g
from cine_fuente.repositories import servicios as servicios_repo
from cine_fuente.services.seguridad import requiere_rol

from cine_fuente.services.servicios import (
    verificar_servicio,
    verificar_reserva,
    verificar_servicio_reservado
)

from cine_fuente.validators.servicios import (
    validar_creacion_servicio,
    validar_campos_servicio,
    validar_cantidad,
    validar_modificacion_servicio_reserva
)
from cine_fuente.validators.comunes import validar_booleano_query

from cine_fuente.utils import (
    validar_paginacion,
    respuesta_paginada,
    respuesta_error as error,
)

servicios_bp = Blueprint("servicios", __name__)


# 1. GET /servicios
@servicios_bp.route("/servicios", methods=["GET"])
def listar_servicios():

    limit, offset = validar_paginacion(request.args)

    nombre = request.args.get("nombre")
    activo = validar_booleano_query(
        request.args, "activo", "ERROR_VALIDACION", "Filtro activo inválido", "Filtro activo inválido"
    )

    total = servicios_repo.contar_servicios(nombre, activo)
    servicios = servicios_repo.consultar_servicios(nombre, activo, limit, offset)

    return respuesta_paginada(
        "servicios", servicios, total, limit, offset
    )


# 2. GET /servicios/{id}
@servicios_bp.route("/servicios/<int:servicio_id>", methods=["GET"])
def obtener_servicio_por_id(servicio_id):

    if servicio_id <= 0:
        return error("ERROR_VALIDACION", "ID inválido", "ID inválido", 400)

    servicio = servicios_repo.consultar_servicio_por_id(servicio_id)

    if servicio is None:
        return error("SERVICIO_NO_ENCONTRADO", "Servicio no encontrado", "Servicio no encontrado", 404)

    return jsonify(servicio), 200


# 3. POST /servicios
@servicios_bp.route("/servicios", methods=["POST"])
@requiere_rol("administrador")
def crear_servicio():

    campos = validar_creacion_servicio(request.get_json(silent=True))

    id_creado = servicios_repo.insertar_servicio(
        campos["nombre"],
        campos["descripcion"],
        campos["precio"],
        campos["activo"]
    )

    return jsonify({"id": id_creado}), 201, {
        "Location": f"/servicios/{id_creado}"} #location es un header para indicar dónde se encuentra el recurso recién creado.


# 4. PATCH /servicios/{id}
@servicios_bp.route("/servicios/<int:servicio_id>", methods=["PATCH"])
@requiere_rol("administrador")
def modificar_servicio(servicio_id):

    fallo = verificar_servicio(servicio_id)
    if fallo is not None:
        return jsonify(fallo[0]), fallo[1]

    campos = validar_campos_servicio(request.get_json(silent=True))

    servicios_repo.actualizar_servicio(servicio_id, campos)

    return "", 204


# 5. DELETE /servicios/{id}
@servicios_bp.route("/servicios/<int:servicio_id>", methods=["DELETE"])
@requiere_rol("administrador")
def eliminar_servicio_endpoint(servicio_id):

    fallo = verificar_servicio(servicio_id)
    if fallo is not None:
        return jsonify(fallo[0]), fallo[1]

    if servicios_repo.servicio_tiene_reservas(servicio_id):
        return error("SERVICIO_CON_RESERVAS", "El servicio tiene reservas asociadas", "El servicio tiene reservas asociadas", 409)

    servicios_repo.eliminar_servicio(servicio_id)

    return "", 204


# 6. GET /reservas/{id}/servicios
@servicios_bp.route("/reservas/<int:reserva_id>/servicios", methods=["POST"])
@requiere_rol("cliente")
def agregar_servicio_reserva(reserva_id):
    fallo = verificar_reserva(reserva_id, g.usuario, modificar=True)
    if fallo is not None:
        return jsonify(fallo[0]), fallo[1]

    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return error("ERROR_VALIDACION", "Cuerpo JSON inválido", "Cuerpo JSON inválido", 400)

    try:
        servicio_id = int(datos["servicio_id"])
        cantidad = validar_cantidad(datos["cantidad"])
    except (KeyError, TypeError, ValueError):
        return error("ERROR_VALIDACION", "Se requieren servicio_id y una cantidad válida", "Se requieren servicio_id y una cantidad válida", 400)

    fallo = verificar_servicio(servicio_id)
    if fallo is not None:
        return jsonify(fallo[0]), fallo[1]

    if servicios_repo.insertar_servicio_reserva(reserva_id, servicio_id, cantidad) == 0:
        return error("SERVICIO_INACTIVO", "El servicio seleccionado no está activo", "El servicio seleccionado no está activo", 409)

    return "", 201


@servicios_bp.route("/reservas/<int:reserva_id>/servicios", methods=["GET"])
@requiere_rol("cliente", "administrador")
def listar_servicios_reserva(reserva_id):

    fallo = verificar_reserva(reserva_id, g.usuario)
    if fallo is not None:
        return jsonify(fallo[0]), fallo[1]

    servicios = servicios_repo.consultar_servicios_reserva(reserva_id)

    if not servicios:
        return "", 204

    return jsonify({"servicios": servicios}), 200


# 7. PATCH /reservas/{id_reserva}/servicios/{id_servicio}
@servicios_bp.route("/reservas/<int:reserva_id>/servicios/<int:servicio_reserva_id>", methods=["PATCH"])
@requiere_rol("cliente")
def modificar_servicio_reserva(reserva_id, servicio_reserva_id):

    fallo = verificar_servicio_reservado(
        reserva_id, servicio_reserva_id, g.usuario
    )
    if fallo is not None:
        return jsonify(fallo[0]), fallo[1]

    cantidad = validar_modificacion_servicio_reserva(
        request.get_json(silent=True)
    )

    servicios_repo.actualizar_cantidad_servicio_reserva(
        reserva_id, servicio_reserva_id, cantidad
    )

    return "", 204


# 8. DELETE /reservas/{id_reserva}/servicios/{id_servicio}
@servicios_bp.route(
    "/reservas/<int:reserva_id>/servicios/<int:servicio_reserva_id>",
    methods=["DELETE"]
)
@requiere_rol("cliente")
def eliminar_servicio_de_reserva(reserva_id, servicio_reserva_id):

    fallo = verificar_servicio_reservado(
        reserva_id, servicio_reserva_id, g.usuario
    )
    if fallo is not None:
        return jsonify(fallo[0]), fallo[1]

    servicios_repo.eliminar_servicio_reserva(reserva_id, servicio_reserva_id)
    return "", 204
