from flask import g

from cine_fuente.repositories import usuarios as usuarios_repo
from cine_fuente.utils import formatear_fecha_hora, construir_error_api
from cine_fuente.services.seguridad import es_titular_o_admin, hashear_contrasenia, verificar_contrasenia


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
    fila = usuarios_repo.obtener_usuario_por_id(usuario_id)
    if fila is None:
        raise _error_usuario_no_encontrado()
    return usuario_api(fila)


def _error_email_duplicado():
    return ValueError(construir_error_api(
        "EMAIL_DUPLICADO", "Email ya registrado", "Ya existe otro usuario con ese email.",
    ), 409)


def _error_usuario_no_encontrado():
    return ValueError(construir_error_api(
        "USUARIO_NO_ENCONTRADO", "Usuario no encontrado", "El usuario solicitado no existe.",
    ), 404)


def _guardar_sin_duplicar_email(accion):
    """Ejecuta una escritura y traduce un email duplicado a un 409."""
    resultado = accion()
    if resultado is None:
        raise _error_email_duplicado()
    return resultado


def crear_usuario(datos):
    """Registra un cliente nuevo y devuelve su id."""
    contrasenia = hashear_contrasenia(datos["contrasenia"])
    return int(_guardar_sin_duplicar_email(lambda: usuarios_repo.crear_usuario(
        datos["nombre"], datos["apellido"], datos["email"], contrasenia
    )))


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


def verificar_permisos_edicion(id_usuario, body):
    """403 si no es titular ni admin, o si un no-administrador intenta enviar 'rol'."""
    es_titular_o_admin(id_usuario)
    if isinstance(body, dict) and "rol" in body and g.usuario["rol"] != "administrador":
        raise ValueError(construir_error_api(
            "ROL_NO_AUTORIZADO",
            "Acceso denegado",
            "Solo un administrador puede modificar el rol de un usuario.",
        ), 403)
    # Un cliente cambia su contraseña, que exige la actual.
    if isinstance(body, dict) and "contrasenia" in body and g.usuario["rol"] != "administrador":
        raise ValueError(construir_error_api(
            "CONTRASENIA_NO_AUTORIZADA",
            "Acceso denegado",
            "Para cambiar su contraseña debe ingresar la contraseña actual.",
        ), 403)


def actualizar_usuario(id_usuario, cambios):
    """Aplica los cambios ya validados. 404 si no existe, 409 si el email ya está en uso."""
    if usuarios_repo.obtener_usuario_por_id(id_usuario) is None:
        raise _error_usuario_no_encontrado()

    cambios = dict(cambios)
    if "contrasenia" in cambios:
        cambios["contrasena"] = hashear_contrasenia(cambios.pop("contrasenia"))

    if "email" in cambios and usuarios_repo.email_en_uso(cambios["email"], id_usuario):
        raise _error_email_duplicado()

    _guardar_sin_duplicar_email(lambda: usuarios_repo.actualizar_usuario(id_usuario, cambios))


def cambiar_contrasenia(id_usuario, contrasenia_actual, contrasenia_nueva):
    """Cambia la contraseña del titular. 403 si la actual no coincide, 400 si la nueva es igual."""
    hash_guardado = usuarios_repo.obtener_hash_contrasenia(id_usuario)
    if hash_guardado is None:
        raise _error_usuario_no_encontrado()

    if not verificar_contrasenia(hash_guardado, contrasenia_actual):
        raise ValueError(construir_error_api(
            "CONTRASENIA_ACTUAL_INCORRECTA",
            "Contraseña actual incorrecta",
            "La contraseña actual no es correcta.",
        ), 403)

    if contrasenia_actual == contrasenia_nueva:
        raise ValueError(construir_error_api(
            "CONTRASENIA_REPETIDA",
            "Contraseña inválida",
            "La nueva contraseña tiene que ser distinta de la actual.",
        ), 400)

    # También registra el logout, los tokens emitidos hasta ahora dejan de valer.
    usuarios_repo.cambiar_contrasenia(id_usuario, hashear_contrasenia(contrasenia_nueva))

