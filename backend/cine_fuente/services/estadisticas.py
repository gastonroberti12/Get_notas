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


# GET /admin/estadisticas/ocupacion/salas: prepara los datos y calcula el porcentaje para cada sala.
def obtener_ocupacion_salas(filtros):
    salas = []
    for fila in estadisticas_repo.consultar_ocupacion_salas(filtros):
        entradas = entero(fila.get("entradas_vendidas"))
        capacidad = entero(fila.get("capacidad_total"))
        salas.append({
            "sala_id": int(fila["sala_id"]),
            "sala_nombre": fila["sala_nombre"],
            "entradas_vendidas": entradas,
            "capacidad_total": capacidad,
            "porcentaje_ocupacion": porcentaje(entradas, capacidad),
        })
    return {"salas": salas}