import os
import requests

from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for


peliculas_bp = Blueprint("peliculas", __name__)

API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5001")


# Obtener listados del backend
def obtener_listado(endpoint, clave):

    resultados = []
    offset = 0
    limite = 100

    try:
        while True:

            respuesta = requests.get(
                f"{API_URL}/{endpoint}",
                params={"_limit": limite, "_offset": offset},
                timeout=5
            )

            if respuesta.status_code == 204:
                break

            if respuesta.status_code != 200:
                return [], "No se pudieron obtener los datos."

            datos = respuesta.json()

            resultados.extend(datos.get(clave, []))

            if "_next" not in datos.get("_links", {}):
                break

            offset += limite

    except (requests.RequestException, ValueError, TypeError):
        return [], "No se pudo conectar con el servidor."

    return resultados, None


# Página principal
@peliculas_bp.route("/")
def inicio():

    # Obtener películas del backend
    peliculas, error_peliculas = obtener_listado(
        "peliculas",
        "peliculas"
    )

    # Obtener funciones del backend
    funciones, error_funciones = obtener_listado(
        "funciones",
        "funciones"
    )

    # Películas destacadas para el carrusel
    peliculas_destacadas = peliculas[:5]

    # Catálogo completo de películas 
    peliculas_catalogo = peliculas

    # Obtener fecha actual
    hoy = date.today()

    nombres_dias = [
        "LUN", "MAR", "MIÉ", "JUE",
        "VIE", "SÁB", "DOM"
    ]

    # Crear los próximos siete días
    dias = []

    for i in range(7):

        dia = hoy + timedelta(days=i)

        dias.append({
            "fecha": dia.isoformat(),
            "nombre": "HOY" if i == 0 else nombres_dias[dia.weekday()],
            "numero": dia.day
        })

    # Fecha seleccionada por el usuario
    fecha_seleccionada = request.args.get(
        "fecha",
        hoy.isoformat()
    )

    fechas_validas = [dia["fecha"] for dia in dias]

    if fecha_seleccionada not in fechas_validas:
        fecha_seleccionada = hoy.isoformat()

    # Filtrar películas con funciones en el día seleccionado
    peliculas_dia = []
    ids_agregados = set()

    for funcion in funciones:

        if not funcion.get("activa", True):
            continue

        fecha_funcion = str(funcion.get("fecha_hora", ""))[:10]

        if fecha_funcion != fecha_seleccionada:
            continue

        pelicula_id = funcion.get("pelicula_id")

        if pelicula_id in ids_agregados:
            continue

        for pelicula in peliculas_catalogo:

            if pelicula["id"] == pelicula_id:

                peliculas_dia.append(pelicula)
                ids_agregados.add(pelicula_id)

                break

    # Manejo de errores
    error_cartelera = error_peliculas or error_funciones

    return render_template(
        "index.html",
        peliculas=peliculas_dia,
        peliculas_catalogo=peliculas_catalogo,
        peliculas_destacadas=peliculas_destacadas,
        dias=dias,
        fecha_seleccionada=fecha_seleccionada,
        error_cartelera=error_cartelera
    )


# Redirección a la cartelera
@peliculas_bp.route("/cartelera")
def cartelera():

    return redirect(
        url_for("peliculas.inicio", _anchor="cartelera")
    )


# Página con el catálogo completo
@peliculas_bp.route("/peliculas")
def listado_peliculas():

    peliculas, error_peliculas = obtener_listado(
        "peliculas",
        "peliculas"
    )

    return render_template(
        "peliculas.html",
        peliculas=peliculas,
        error_peliculas=error_peliculas
    )