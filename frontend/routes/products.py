from flask import Blueprint, render_template, request, redirect, url_for, flash
from services.api_cliente import mensaje_error
from services.peliculas import listar_peliculas, obtener_pelicula, obtener_resenas, obtener_estado_resena, publicar_resena
from services.funciones import listar_funciones
from logica.formato import formatear_fecha
from logica.sucursales import filtro_sucursal
from logica.roles import es_cliente, solo_logueado
from logica.validaciones import validar_entero
from routes.errores import abortar_por_status


peliculas_bp = Blueprint("peliculas", __name__)


@peliculas_bp.route("/")
def inicio():

    status, datos = listar_peliculas(filtro_sucursal())
    peliculas = datos.get("peliculas", [])
    error_peliculas = None
    if status not in (200, 204):
        error_peliculas = mensaje_error(status, datos, "No se pudieron obtener los datos.")

    peliculas_destacadas = peliculas[:5]

    return render_template(
        "index.html",
        peliculas=peliculas,
        peliculas_destacadas=peliculas_destacadas,
        error_cartelera=error_peliculas
    )

@peliculas_bp.route("/cartelera")
def cartelera():

    return redirect(
        url_for("peliculas.inicio", _anchor="cartelera")
    )

@peliculas_bp.route("/peliculas")
def listado_peliculas():

    status, datos = listar_peliculas(filtro_sucursal())
    peliculas = datos.get("peliculas", [])
    error_peliculas = None
    if status not in (200, 204):
        error_peliculas = mensaje_error(status, datos, "No se pudieron obtener los datos.")

    return render_template(
        "peliculas.html",
        peliculas=peliculas,
        error_peliculas=error_peliculas
    )

@peliculas_bp.route("/peliculas/<int:pelicula_id>")
def detalle_pelicula(pelicula_id):
    status, pelicula = obtener_pelicula(pelicula_id)
    if status != 200:
        abortar_por_status(status)

    status, datos = listar_funciones(f"&pelicula_id={pelicula_id}&activa=true{filtro_sucursal()}")
    funciones = datos.get("funciones", []) if status == 200 else []
    for f in funciones:
        f["dia"] = formatear_fecha(f.get("fecha_hora"), "%d/%m", "")
        f["hora"] = formatear_fecha(f.get("fecha_hora"), "%H:%M", "")

    # reseñas de la película con su promedio
    resenas = {"resenas": [], "total": 0, "promedio": None}
    status, datos = obtener_resenas(pelicula_id)
    if status == 200:
        resenas = datos
    for r in resenas["resenas"]:
        r["fecha_texto"] = formatear_fecha(r.get("fecha"), "%d/%m/%Y", "")

    # Solo los clientes consultan si pueden reseñar
    estado_resena = None
    if es_cliente():
        status, datos = obtener_estado_resena(pelicula_id)
        if status == 200:
            estado_resena = datos
    return render_template("pelicula_detalle.html", pelicula=pelicula, funciones=funciones, resenas=resenas, estado_resena=estado_resena)


# para ubicar una reseña el backend valida que la entrada haya sido usada
@peliculas_bp.route("/peliculas/<int:pelicula_id>/resenas", methods=["POST"])
@solo_logueado
def crear_resena(pelicula_id):
    calificacion, error = validar_entero(request.form.get("calificacion"), "Elegí una calificación de 1 a 5.")
    if error:
        flash(error, "error")
        return redirect(url_for("peliculas.detalle_pelicula", pelicula_id=pelicula_id, _anchor="resenas"))

    comentario = request.form.get("comentario", "").strip()

    status, cuerpo = publicar_resena(pelicula_id, calificacion, comentario)
    if status == 201:
        flash("¡Gracias por tu reseña!", "exito")
    else:
        flash(mensaje_error(status, cuerpo, "No se pudo guardar la reseña."), "error")

    return redirect(url_for("peliculas.detalle_pelicula", pelicula_id=pelicula_id, _anchor="resenas"))