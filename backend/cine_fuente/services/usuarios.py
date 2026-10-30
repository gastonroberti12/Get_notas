from cine_fuente.repositories import usuarios as usuarios_repo
from cine_fuente.utils import formatear_fecha_hora


def usuario_api(fila):
    """Adapta una fila de la BD al esquema Usuario del Swagger."""
    return {
        "id": int(fila["id"]),
        "nombre": fila["nombre"],
        "apellido": fila["apellido"],
        "email": fila["email"],
        "rol": fila["rol"],
        "fecha_registro": formatear_fecha_hora(fila["fecha_registro"]),
    }


def listar_usuarios(filtros, limit, offset):
    """Devuelve los usuarios de la página pedida y el total para la paginación."""
    usuarios = usuarios_repo.listar_usuarios(filtros, limit, offset)
    total = usuarios_repo.contar_usuarios(filtros)
    return [usuario_api(usuario) for usuario in usuarios], total


def obtener_perfil(usuario_id):
    fila = usuarios_repo.obtener_por_id(usuario_id)
    if fila is None:
        raise ValueError(construir_error_api(
            "USUARIO_NO_ENCONTRADO", "No encontrado", "El usuario no existe."), 404)
    return usuario_api(fila)