from flask import Blueprint, request

from cine_fuente.services import usuarios as usuarios_service
from cine_fuente.utils import (
    requiere_token,
    respuesta_error_excepcion,
    respuesta_error_interno,
    respuesta_paginada,
    validar_paginacion,
)
from cine_fuente.validators.validadorUsuario import validar_filtros_usuarios

usuarios_bp = Blueprint("usuarios", __name__)


# Endpoint GET /usuarios: listado paginado para el administrador, filtrable por rol, nombre y email.
@usuarios_bp.route("/usuarios", methods=["GET"])
@requiere_token(("administrador",))
def get_usuarios():
    try:
        filtros = validar_filtros_usuarios(request.args)
        limit, offset = validar_paginacion(request.args)
        usuarios, total = usuarios_service.listar_usuarios(filtros, limit, offset)
        return respuesta_paginada("usuarios", usuarios, total, limit, offset)
    except ValueError as error:
        return respuesta_error_excepcion(error)
    except Exception as error:
        return respuesta_error_interno(error)