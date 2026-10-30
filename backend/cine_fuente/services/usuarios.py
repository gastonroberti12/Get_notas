from cine_fuente.repositories import usuarios as usuarios_repo
from cine_fuente.utils import formatear_fecha_hora, construir_error_api
from cine_fuente.services.seguridad import es_titular_o_admin


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


def crear_usuario(datos):
    """Registra un cliente nuevo y devuelve su id."""
    return int(usuarios_repo.crear_usuario(
        datos["nombre"], datos["apellido"], datos["email"], datos["contrasenia"]
    ))


def obtener_usuario(id_usuario):
    """Devuelve el usuario pedido. Un cliente solo puede ver el suyo (403); 404 si no existe."""
    # Se chequea el permiso antes de consultar para no revelar qué IDs existen.
    es_titular_o_admin(id_usuario)
    fila = usuarios_repo.obtener_usuario_por_id(id_usuario)
    if fila is None:
        raise ValueError(construir_error_api(
            "USUARIO_NO_ENCONTRADO",
            "Usuario no encontrado",
            "El usuario solicitado no existe.",
        ), 404)
    return usuario_api(fila)