from cine_fuente.repositories import estadisticas as estadisticas_repo


# Funciones auxiliares
def entero(valor):
    return int(valor or 0)


def porcentaje(parte, total):
    return round((parte * 100 / total), 1) if total else 0.0


# GET /admin/estadisticas/ocupacion/general: agrega el porcentaje de ocupación a los totales del repositorio.
def obtener_ocupacion_general(filtros):
    datos = estadisticas_repo.consultar_ocupacion_general(filtros)
    entradas = entero(datos.get("entradas_vendidas"))
    capacidad = entero(datos.get("capacidad_total"))
    return {
        "entradas_vendidas": entradas,
        "capacidad_total": capacidad,
        "porcentaje_ocupacion": porcentaje(entradas, capacidad),
    }