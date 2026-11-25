from flask import flash, redirect, render_template, request, session, url_for
from services.api_cliente import mensaje_error
from services.peliculas import (listar_peliculas, obtener_pelicula, crear_pelicula, actualizar_pelicula,
                                actualizar_estado_pelicula, buscar_en_omdb, obtener_datos_omdb)
from routes.backoffice.backoffice import backoffice_bp, cambiar_estado, ver_inactivos
from routes.errores import abortar_por_status
from logica.roles import solo_admin
from logica.formato import FORMATO_INPUT_FECHA, a_iso_gmt3, formatear_fecha
from logica.validaciones import validar_entero, validar_imdb_id


CAMPOS = ("titulo", "sinopsis", "poster_url", "duracion_min", "clasificacion", "genero")
CAMPOS_FECHA = ("fecha_inicio_cartelera", "fecha_fin_cartelera")


def url_listado():
    return url_for("backoffice.peliculas_admin")


def peliculas_locales():
    activas_status, activas = listar_peliculas("&activa=true")
    inactivas_status, inactivas = listar_peliculas("&activa=false")
    if activas_status not in (200, 204) or inactivas_status not in (200, 204):
        return None
    activas = activas.get("peliculas", []) if activas_status == 200 else []
    inactivas = inactivas.get("peliculas", []) if inactivas_status == 200 else []
    return sorted(activas + inactivas, key=lambda pelicula: pelicula["id"])


@backoffice_bp.route("/backoffice/peliculas")
@solo_admin
def peliculas_admin():
    inactivos = ver_inactivos()
    status, datos = listar_peliculas("&activa=false" if inactivos else "&activa=true")
    peliculas = datos.get("peliculas", [])
    error = None
    if status not in (200, 204):
        error = mensaje_error(status, datos, "No se pudieron obtener los datos.")
    return render_template("backadmin/peliculas_listado.html", peliculas=peliculas, error=error, ver_inactivos=inactivos)


@backoffice_bp.route("/backoffice/peliculas/buscar")
@solo_admin
def pelicula_buscar():
    """Busca películas en OMDb a través del backend y marca cuáles ya están cargadas en el cine."""
    q = request.args.get("q", "").strip()
    pagina = request.args.get("pagina", 1, type=int)
    resultados, total, error = [], 0, None

    if q:
        status, datos = buscar_en_omdb(q, pagina)
        if status == 200:
            resultados = datos.get("resultados", [])
            total = datos.get("total_resultados", 0)
            locales = peliculas_locales()
            if locales is not None:
                # id_externo -> activa: para marcar en los resultados las que ya están cargadas y si están de baja
                estado_por_imdb = {
                    pelicula["id_externo"]: pelicula["activa"]
                    for pelicula in locales
                }
                for resultado in resultados:
                    if resultado["id_externo"] in estado_por_imdb:
                        resultado["cargada"] = True
                        resultado["activa"] = estado_por_imdb[resultado["id_externo"]]
        else:
            error = mensaje_error(status, datos, "No se pudo consultar OMDb.")

    return render_template(
        "backadmin/subirpelicula.html",
        q=q,
        pagina=pagina,
        resultados=resultados,
        total=total,
        error=error,
        buscado=bool(q),
    )


@backoffice_bp.route("/backoffice/peliculas/nueva", methods=["GET", "POST"])
@solo_admin
def pelicula_nueva():
    """GET: si viene ?id= precarga el formulario con los datos de OMDb.
    POST: crea la película con POST /peliculas y vuelve al listado."""
    if request.method == "POST":
        valores = {campo: request.form.get(campo, "").strip() for campo in CAMPOS}
        valores["id_externo"] = request.form.get("id_externo", "").strip()
        inicio = request.form.get("fecha_inicio_cartelera", "")
        fin = request.form.get("fecha_fin_cartelera", "")
        # a_iso_gmt3: pasa el valor del input datetime-local al ISO con zona horaria que pide el backend
        datos = {
            "id_externo": valores["id_externo"],
            "fecha_inicio_cartelera": a_iso_gmt3(inicio),
            "fecha_fin_cartelera": a_iso_gmt3(fin),
        }

        status, cuerpo = crear_pelicula(datos)
        if status == 201:
            flash("Película agregada correctamente.", "exito")
            return redirect(url_listado())
        # 401: la sesión venció; se limpia para que vuelva a loguearse
        if status == 401:
            session.clear()
            return redirect(url_for("users.login"))
        valores.update(fecha_inicio_cartelera=inicio, fecha_fin_cartelera=fin)
        return render_template(
            "backadmin/pelicula_form.html",
            v=valores,
            error=mensaje_error(status, cuerpo, "No se pudo guardar la película."),
        )

    valores, aviso = {}, None
    if request.args.get("id"):
        imdb_id, error = validar_imdb_id(request.args.get("id"))
        if error:
            return redirect(url_for("backoffice.pelicula_buscar"))
        status, detalle = obtener_datos_omdb(imdb_id)
        if status == 200:
            valores = {campo: detalle.get(campo) or "" for campo in CAMPOS}
            # OMDb manda varios géneros ("Action, Drama"); se queda solo con el primero
            valores["genero"] = valores["genero"].split(",")[0].strip()
        else:
            aviso = (
                mensaje_error(status, detalle, "No se pudieron traer los datos.")
            )
            valores = {}
        if valores:
            valores["id_externo"] = imdb_id
    return render_template("backadmin/pelicula_form.html", v=valores, aviso=aviso)


def traer_pelicula(pelicula_id):
    status, pelicula = obtener_pelicula(pelicula_id)
    if status != 200:
        abortar_por_status(status)
    return pelicula


@backoffice_bp.route("/backoffice/peliculas/<int:pelicula_id>/editar", methods=["GET", "POST"])
@solo_admin
def pelicula_editar(pelicula_id):
    """GET: muestra el formulario con los datos actuales.
    POST: manda SOLO los campos que cambiaron con PATCH /peliculas/<id>."""
    actual = traer_pelicula(pelicula_id)
    accion = url_for("backoffice.pelicula_editar", pelicula_id=pelicula_id)
    valores = {campo: actual.get(campo) or "" for campo in CAMPOS}
    valores["activa"] = bool(actual.get("activa"))
    for campo in CAMPOS_FECHA:
        valores[campo] = formatear_fecha(actual.get(campo), FORMATO_INPUT_FECHA, "")

    if request.method == "GET":
        return render_template(
            "backadmin/pelicula_form.html",
            v={**valores, "id": pelicula_id},
            editando=True,
            accion=accion,
            volver=url_listado(),
        )

    enviados = {
        campo: request.form.get(campo, "").strip()
        for campo in CAMPOS + CAMPOS_FECHA
    }
    cambios = {}
    error = None
    # Compara cada campo enviado con el actual: solo los distintos van en "cambios"
    for campo, nuevo in enviados.items():
        if nuevo == str(valores[campo]):
            continue
        if campo in CAMPOS_FECHA:
            cambios[campo] = a_iso_gmt3(nuevo)
        elif campo == "duracion_min" and nuevo:
            duracion, error = validar_entero(nuevo, "La duración debe ser un número entero de minutos.")
            cambios[campo] = duracion
        else:
            cambios[campo] = nuevo or None
    # Reactivar: el backend exige un período de cartelera nuevo, así que siempre se mandan las dos fechas
    if not valores["activa"] and request.form.get("reactivar") == "true":
        cambios["activa"] = True
        cambios["fecha_inicio_cartelera"] = a_iso_gmt3(
            enviados["fecha_inicio_cartelera"]
        )
        cambios["fecha_fin_cartelera"] = a_iso_gmt3(
            enviados["fecha_fin_cartelera"]
        )

    valores_formulario = {**enviados, "id": pelicula_id, "activa": valores["activa"]}
    if error:
        return render_template(
            "backadmin/pelicula_form.html",
            v=valores_formulario,
            editando=True,
            accion=accion,
            volver=url_listado(),
            error=error,
        )
    # Nada distinto: no se llama al backend, se avisa en el formulario
    if not cambios:
        return render_template(
            "backadmin/pelicula_form.html",
            v=valores_formulario,
            editando=True,
            accion=accion,
            volver=url_listado(),
            aviso="No hay cambios para guardar.",
        )

    status, cuerpo = actualizar_pelicula(pelicula_id, cambios)
    # 204 = guardado OK (el PATCH no devuelve cuerpo)
    if status == 204:
        return redirect(url_listado())
    if status == 401:
        session.clear()
        return redirect(url_for("users.login"))
    return render_template(
        "backadmin/pelicula_form.html",
        v=valores_formulario,
        editando=True,
        accion=accion,
        volver=url_listado(),
        error=mensaje_error(status, cuerpo, "No se pudo guardar la película."),
    )


@backoffice_bp.route("/backoffice/peliculas/<int:pelicula_id>/estado", methods=["POST"])
@solo_admin
def cambiar_estado_pelicula(pelicula_id):
    return cambiar_estado(actualizar_estado_pelicula, pelicula_id, "Película dada", "backoffice.peliculas_admin")