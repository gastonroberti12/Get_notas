from datetime import datetime
import re
from urllib.parse import urlencode
from flask import abort, flash, redirect, render_template, request, session, url_for
from api_cliente import llamar_api, mensaje_error
from routes.backoffice.backoffice import backoffice_bp, cambiar_estado, ver_inactivos
from routes.roles import es_admin, solo_admin
from routes.products import obtener_listado


CAMPOS = ("titulo", "sinopsis", "poster_url", "duracion_min", "clasificacion", "genero")
CAMPOS_FECHA = ("fecha_inicio_cartelera", "fecha_fin_cartelera")


def url_listado():
    return url_for("backoffice.peliculas_admin")


def peliculas_locales():
    activas_status, activas = llamar_api("GET", "/peliculas?_limit=100&activa=true")
    inactivas_status, inactivas = llamar_api("GET", "/peliculas?_limit=100&activa=false")
    if activas_status not in (200, 204) or inactivas_status not in (200, 204):
        return None
    activas = activas.get("peliculas", []) if activas_status == 200 else []
    inactivas = inactivas.get("peliculas", []) if inactivas_status == 200 else []
    return sorted(activas + inactivas, key=lambda pelicula: pelicula["id"])


def a_iso_gmt3(valor):
    if not valor:
        return ""
    try:
        return datetime.fromisoformat(valor).strftime("%Y-%m-%dT%H:%M:%S.%f") + "-03:00"
    except ValueError:
        return valor


@backoffice_bp.route("/backoffice/peliculas")
@backoffice_bp.route("/backoffice/peliculas")
def peliculas_admin():
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))
    inactivos = ver_inactivos()
    peliculas, error = obtener_listado("peliculas", "peliculas", "&activa=false" if inactivos else "&activa=true")
    return render_template("backadmin/peliculas_listado.html", peliculas=peliculas, error=error, ver_inactivos=inactivos)


@backoffice_bp.route("/backoffice/peliculas/buscar")
def pelicula_buscar():
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))

    q = request.args.get("q", "").strip()
    pagina = request.args.get("pagina", 1, type=int)
    resultados, total, error = [], 0, None

    if q:
        status, datos = llamar_api(
            "GET", "/peliculas/buscar?" + urlencode({"q": q, "pagina": pagina})
        )
        if status == 200:
            resultados = datos.get("resultados", [])
            total = datos.get("total_resultados", 0)
            locales = peliculas_locales()
            if locales is not None:
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
def pelicula_nueva():
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))

    if request.method == "POST":
        valores = {campo: request.form.get(campo, "").strip() for campo in CAMPOS}
        valores["id_externo"] = request.form.get("id_externo", "").strip()
        inicio = request.form.get("fecha_inicio_cartelera", "")
        fin = request.form.get("fecha_fin_cartelera", "")
        datos = {
            "id_externo": valores["id_externo"],
            "fecha_inicio_cartelera": a_iso_gmt3(inicio),
            "fecha_fin_cartelera": a_iso_gmt3(fin),
        }

        status, cuerpo = llamar_api("POST", "/peliculas", datos)
        if status == 201:
            flash("Película agregada correctamente.", "ok")
            return redirect(url_listado())
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
    imdb_id = request.args.get("id", "").strip()
    if imdb_id:
        if not re.fullmatch(r"tt\d+", imdb_id):
            return redirect(url_for("backoffice.pelicula_buscar"))
        status, detalle = llamar_api("GET", f"/peliculas/{imdb_id}")
        if status == 200:
            valores = {campo: detalle.get(campo) or "" for campo in CAMPOS}
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
    status, pelicula = llamar_api("GET", f"/peliculas/{pelicula_id}")
    if status == 404:
        abort(404)
    if status != 200:
        abort(503 if status is None else 500)
    return pelicula


@backoffice_bp.route("/backoffice/peliculas/<int:pelicula_id>/editar", methods=["GET", "POST"])
def pelicula_editar(pelicula_id):
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))

    actual = traer_pelicula(pelicula_id)
    accion = url_for("backoffice.pelicula_editar", pelicula_id=pelicula_id)
    valores = {campo: actual.get(campo) or "" for campo in CAMPOS}
    valores["activa"] = bool(actual.get("activa"))
    for campo in CAMPOS_FECHA:
        valores[campo] = (actual.get(campo) or "")[:16]

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
    for campo, nuevo in enviados.items():
        if nuevo == str(valores[campo]):
            continue
        if campo in CAMPOS_FECHA:
            cambios[campo] = a_iso_gmt3(nuevo)
        else:
            cambios[campo] = (
                int(nuevo) if campo == "duracion_min" and nuevo.isdigit() else nuevo
            ) or None
    if not valores["activa"] and request.form.get("reactivar") == "true":
        cambios["activa"] = True
        cambios["fecha_inicio_cartelera"] = a_iso_gmt3(
            enviados["fecha_inicio_cartelera"]
        )
        cambios["fecha_fin_cartelera"] = a_iso_gmt3(
            enviados["fecha_fin_cartelera"]
        )

    valores_formulario = {**enviados, "id": pelicula_id, "activa": valores["activa"]}
    if not cambios:
        return render_template(
            "backadmin/pelicula_form.html",
            v=valores_formulario,
            editando=True,
            accion=accion,
            volver=url_listado(),
            aviso="No hay cambios para guardar.",
        )

    status, cuerpo = llamar_api("PATCH", f"/peliculas/{pelicula_id}", cambios)
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
    return cambiar_estado(
        f"/peliculas/{pelicula_id}", "Película", "backoffice.peliculas_admin"
    )
