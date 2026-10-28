from flask import Blueprint, jsonify, request, session
from cine_fuente.repositories.servicios import consultar_servicios, consultar_servicio_por_id, insertar_servicio
from cine_fuente.validators.servicios import validar_id_servicio, validar_nombre, validar_descripcion, validar_precio



servicios_bp = Blueprint("servicios", __name__)

@servicios_bp.route("/servicios", methods=["GET"])
def listar_servicios():
    servicios = consultar_servicios()
    return jsonify(servicios), 200

@servicios_bp.route("/servicios/<int:servicio_id>", methods=["GET"])
def obtener_servicio_por_id(servicio_id):

    if not validar_id_servicio(servicio_id):
        return jsonify({"error": "El ID debe ser mayor a cero"}), 400

    servicio = consultar_servicio_por_id(servicio_id)

    if servicio is None:
        return jsonify({"error": "Servicio no encontrado"}), 404

    return jsonify(servicio), 200



from flask import request, jsonify, session
from cine_fuente.validators.servicios import (
    validar_nombre,
    validar_descripcion,
    validar_precio
)
from cine_fuente.repositories.servicios import insertar_servicio


@servicios_bp.route("/servicios", methods=["POST"])
def crear_servicio():

    # Adaptar al sistema de autenticación del grupo
    if session.get("rol") != "admin":
        return jsonify({"error": "Acceso denegado"}), 403

    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({"error": "Se debe enviar un objeto JSON"}), 400

    try:
        nombre = validar_nombre(datos.get("nombre"))
        descripcion = validar_descripcion(datos.get("descripcion"))
        precio = validar_precio(datos.get("precio"))

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    insertar_servicio(nombre, descripcion, precio)

    return jsonify({"mensaje": "Servicio creado correctamente"}), 201
    