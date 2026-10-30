import pymysql

from cine_fuente.db import ejecutar_consulta, ejecutar_escritura

CARACTER_ESCAPE_LIKE = "!"

MYSQL_ERROR_DUPLICADO = 1062
CARACTER_ESCAPE_LIKE = "!"
# Columnas que PATCH /usuarios/{id} puede modificar (los valores siempre van enlazados).
COLUMNAS_ACTUALIZABLES = {"nombre", "apellido", "email", "contrasena", "rol"}


# Condiciones de búsqueda parcial e insensible a mayúsculas, una por filtro de texto.
CONDICIONES_BUSQUEDA = {
    "nombre": (
        "(LOWER(nombre) LIKE LOWER(%(nombre)s) ESCAPE '!' "
        "OR LOWER(apellido) LIKE LOWER(%(nombre)s) ESCAPE '!')"
    ),
    "email": "LOWER(email) LIKE LOWER(%(email)s) ESCAPE '!'",
}


class EmailDuplicadoError(Exception):
    """El email ya pertenece a otro usuario (violación del UNIQUE de la tabla)."""


def _escribir_usuario(sql, parametros):
    """Ejecuta una escritura sobre usuarios y traduce el error de email duplicado de MySQL."""
    try:
        return ejecutar_escritura(sql, parametros)
    except pymysql.err.IntegrityError as error:
        if error.args and error.args[0] == MYSQL_ERROR_DUPLICADO:
            raise EmailDuplicadoError() from error
        raise


def _patron_contiene(texto):
    """Arma el patrón '%texto%' escapando los comodines de LIKE ingresados por el usuario."""
    for caracter in (CARACTER_ESCAPE_LIKE, "%", "_"):
        texto = texto.replace(caracter, f"{CARACTER_ESCAPE_LIKE}{caracter}")
    return f"%{texto}%"


def _construir_filtros(filtros):
    """Devuelve (WHERE, parámetros) con todos los valores enlazados, nunca concatenados."""
    condiciones = []
    parametros = {}

    if filtros.get("rol") is not None:
        condiciones.append("rol = %(rol)s")
        parametros["rol"] = filtros["rol"]

    for campo, condicion in CONDICIONES_BUSQUEDA.items():
        valor = filtros.get(campo)
        if valor is not None:
            condiciones.append(condicion)
            parametros[campo] = _patron_contiene(valor)

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    return where, parametros

def listar_usuarios(filtros, limit, offset):
    """Lista usuarios con filtros y paginación. Nunca expone contrasena ni token."""
    where, parametros = _construir_filtros(filtros)
    parametros.update({"limit": limit, "offset": offset})
    sql = f"""
        SELECT id, nombre, apellido, email, rol, fecha_registro
        FROM usuarios
        {where}
        ORDER BY id ASC
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return ejecutar_consulta(sql, parametros)


def contar_usuarios(filtros):
    """Cuenta los usuarios que cumplen los filtros, para la paginación."""
    where, parametros = _construir_filtros(filtros)
    filas = ejecutar_consulta(f"SELECT COUNT(*) AS total FROM usuarios {where}", parametros)
    return int(filas[0]["total"]) if filas else 0

def obtener_por_id(usuario_id):
    filas = ejecutar_consulta(
        "SELECT id, nombre, apellido, email, rol, fecha_registro FROM usuarios WHERE id = %s",
        (usuario_id,),
    )
    return filas[0] if filas else None

def crear_usuario(nombre, apellido, email, contrasenia):
    """Inserta un usuario con rol 'cliente' y devuelve su id."""
    sql = """
        INSERT INTO usuarios (nombre, apellido, email, contrasena, rol)
        VALUES (%(nombre)s, %(apellido)s, %(email)s, %(contrasena)s, 'cliente')
    """
    return ejecutar_escritura(sql, {
        "nombre": nombre,
        "apellido": apellido,
        "email": email,
        "contrasena": contrasenia,
    })


def obtener_usuario_por_id(id_usuario):
    """Devuelve la fila del usuario o None. Nunca expone contrasena ni token."""
    sql = """
        SELECT id, nombre, apellido, email, rol, fecha_registro
        FROM usuarios
        WHERE id = %(id)s
        LIMIT 1
    """
    filas = ejecutar_consulta(sql, {"id": id_usuario})
    return filas[0] if filas else None


def email_en_uso(email, excluir_id=None):
    """True si algún usuario (distinto de excluir_id) ya tiene ese email."""
    sql = "SELECT id FROM usuarios WHERE email = %(email)s AND id <> %(id)s LIMIT 1"
    return bool(ejecutar_consulta(sql, {"email": email, "id": excluir_id or 0}))


def actualizar_usuario(id_usuario, cambios):
    """UPDATE parcial: solo las columnas presentes en 'cambios'."""
    if not cambios or not set(cambios) <= COLUMNAS_ACTUALIZABLES:
        raise ValueError("Columnas a actualizar inválidas.")
    asignaciones = ", ".join(f"{columna} = %({columna})s" for columna in cambios)
    _escribir_usuario(
        f"UPDATE usuarios SET {asignaciones} WHERE id = %(id)s",
        {**cambios, "id": id_usuario},
    )
