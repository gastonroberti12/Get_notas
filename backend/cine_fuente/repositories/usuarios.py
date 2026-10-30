"""Consultas SQL de usuarios (GET /usuarios)."""

from cine_fuente.db import ejecutar_consulta

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