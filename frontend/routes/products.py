from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from api_cliente import llamar_api, mensaje_error
from datos_perfil import parsear_fecha
from sucursales import contexto_sucursales
from routes.roles import esta_logueado, es_cliente


peliculas_bp = Blueprint("peliculas", __name__)

# Filtro de sucursal para el backend (vacío si no hay sucursales disponibles).
def filtro_sucursal():
    _, actual = contexto_sucursales()
    if actual is None:
        return ""
    return f"&sucursal_id={actual['id']}"

# Obtener listados del backend
def obtener_listado(endpoint, clave, filtros=""):
    status, datos = llamar_api("GET", f"/{endpoint}?_limit=100{filtros}")

    if status not in (200, 204):
        return [], mensaje_error(status, datos, "No se pudieron obtener los datos.")

    # Con 204 el cuerpo viene vacío, así que devuelve una lista vacía.
    return datos.get(clave, []), None


# Página principal
@peliculas_bp.route("/")
def inicio():

    # Obtener películas del backend
    peliculas, error_peliculas = obtener_listado(
        "peliculas",
        "peliculas",
        filtro_sucursal()
    )

    # Primeras cinco películas para el carrusel
    peliculas_destacadas = peliculas[:5]

    return render_template(
        "index.html",
        peliculas=peliculas,
        peliculas_destacadas=peliculas_destacadas,
        error_cartelera=error_peliculas
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
        "peliculas",
        filtro_sucursal()
    )

    return render_template(
        "peliculas.html",
        peliculas=peliculas,
        error_peliculas=error_peliculas
    )
    
# Detalle de una película con sus funciones disponibles
@peliculas_bp.route("/peliculas/<int:pelicula_id>")
def detalle_pelicula(pelicula_id):
    status, pelicula = llamar_api("GET", f"/peliculas/{pelicula_id}")
    if status == 404:
        abort(404)
    if status is None:
        abort(503)  # el backend no responde
    if status != 200:
        abort(500)

    status, datos = llamar_api("GET", f"/funciones?pelicula_id={pelicula_id}&activa=true{filtro_sucursal()}")
    funciones = datos.get("funciones", []) if status == 200 else []
    for f in funciones:
        fecha = parsear_fecha(f.get("fecha_hora"))
        f["dia"] = fecha.strftime("%d/%m") if fecha else ""
        f["hora"] = fecha.strftime("%H:%M") if fecha else ""

    # Reseñas de la película (públicas) con su promedio
    resenas = {"resenas": [], "total": 0, "promedio": None}
    status, datos = llamar_api("GET", f"/peliculas/{pelicula_id}/resenas?_limit=50")
    if status == 200:
        resenas = datos
    for r in resenas["resenas"]:
        fecha = parsear_fecha(r.get("fecha"))
        r["fecha_texto"] = fecha.strftime("%d/%m/%Y") if fecha else ""

    # Solo los clientes consultan si pueden reseñar (entrada ya validada)
    estado_resena = None
    if es_cliente():
        status, datos = llamar_api("GET", f"/peliculas/{pelicula_id}/resenas/estado")
        if status == 200:
            estado_resena = datos
    return render_template("pelicula_detalle.html", pelicula=pelicula, funciones=funciones, resenas=resenas, estado_resena=estado_resena)


# Publicar una reseña: el backend valida que la entrada haya sido usada
@peliculas_bp.route("/peliculas/<int:pelicula_id>/resenas", methods=["POST"])
def crear_resena(pelicula_id):
    if not esta_logueado():
        return redirect(url_for("users.login"))

    calificacion = request.form.get("calificacion", type=int)
    comentario = request.form.get("comentario", "").strip()

    status, cuerpo = llamar_api(
        "POST",
        f"/peliculas/{pelicula_id}/resenas",
        {"calificacion": calificacion, "comentario": comentario or None},
    )
    if status == 201:
        flash("¡Gracias por tu reseña!", "exito")
    else:
        flash(mensaje_error(status, cuerpo, "No se pudo guardar la reseña."), "error")

    return redirect(url_for("peliculas.detalle_pelicula", pelicula_id=pelicula_id, _anchor="resenas"))