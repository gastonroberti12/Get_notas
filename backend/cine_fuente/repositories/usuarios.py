from cine_fuente.db import ejecutar_consulta
from cine_fuente.db import ejecutar_consulta, ejecutar_escritura

CARACTER_ESCAPE_LIKE = "!"

# Condiciones de búsqueda parcial e insensible a mayúsculas, una por filtro de texto.
CONDICIONES_BUSQUEDA = {
    "nombre": (
        "(LOWER(nombre) LIKE LOWER(%(nombre)s) ESCAPE '!' "
        "OR LOWER(apellido) LIKE LOWER(%(nombre)s) ESCAPE '!')"
    ),
    "email": "LOWER(email) LIKE LOWER(%(email)s) ESCAPE '!'",
}


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