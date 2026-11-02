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


# GET /admin/estadisticas/ocupacion/franjas_horarias: normaliza los resultados agrupados por hora.
def obtener_franjas_horarias(filtros):
    return {"franjas": [
        {
            "hora": int(fila["hora"]),
            "entradas_vendidas": entero(fila.get("entradas_vendidas")),
        }
        for fila in estadisticas_repo.consultar_franjas_horarias(filtros)
    ]}


# GET /admin/estadisticas/ventas/total: combina los importes de entradas y servicios.
def obtener_ventas_total(filtros):
    datos = estadisticas_repo.consultar_ventas_total(filtros)
    monto_entradas = entero(datos.get("monto_entradas"))
    monto_servicios = entero(datos.get("monto_servicios"))
    return {
        "entradas_vendidas": entero(datos.get("entradas_vendidas")),
        "monto_entradas": monto_entradas,
        "monto_servicios": monto_servicios,
        "monto_total": monto_entradas + monto_servicios,
    }


# GET /admin/estadisticas/ventas/generos: normaliza los importes y cantidades por género.
def obtener_ventas_generos(filtros):
    return {"generos": [
        {
            "genero": fila["genero"],
            "entradas_vendidas": entero(fila.get("entradas_vendidas")),
            "monto_total": entero(fila.get("monto_total")),
        }
        for fila in estadisticas_repo.consultar_ventas_generos(filtros)
    ]}