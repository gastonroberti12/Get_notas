from datetime import datetime
from urllib.parse import urlencode

from flask import render_template, redirect, url_for, flash, request
from api_cliente import llamar_api, mensaje_error
from routes.roles import es_admin, solo_admin
from routes.backoffice.backoffice import backoffice_bp, cambiar_estado


def fecha_para_api(valor):
    if not valor:
        return ""
    try:
        return datetime.fromisoformat(valor).isoformat(timespec="microseconds") + "-03:00"
    except ValueError:
        return valor


def pagina_para_vista(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return 1


@backoffice_bp.route("/backoffice/peliculas")
def peliculas_admin():
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))
    status, datos = llamar_api("GET", "/peliculas?_limit=100")
    if status not in (200, 204):
        error = mensaje_error(status, datos, "No se pudieron obtener las películas.")
        return render_template("backadmin/peliculas_listado.html", peliculas=[], error=error)
    return render_template("backadmin/peliculas_listado.html",
                           peliculas=datos.get("peliculas", []), error=None)


@backoffice_bp.route("/backoffice/peliculas/nueva", methods=["GET", "POST"])
def nueva_pelicula():
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))

    if request.method == "GET":
        imdb_id = request.args.get("id", "").strip()
        if not imdb_id:
            return redirect(url_for("backoffice.pelicula_buscar"))

        status, datos = llamar_api("GET", f"/peliculas/{imdb_id}")
        if status != 200:
            return render_template(
                "backadmin/pelicula_form.html",
                v={"id_externo": imdb_id},
                error=mensaje_error(status, datos, "No se pudo obtener la película desde OMDb."),
            )
        return render_template("backadmin/pelicula_form.html", v=datos)

    datos = {
        "id_externo": request.form.get("id_externo", "").strip(),
        "fecha_inicio_cartelera": fecha_para_api(request.form.get("fecha_inicio_cartelera")),
        "fecha_fin_cartelera": fecha_para_api(request.form.get("fecha_fin_cartelera")),
    }
    if not datos["id_externo"]:
        return redirect(url_for("backoffice.pelicula_buscar"))

    status, respuesta = llamar_api("POST", "/peliculas", datos)
    if status == 201:
        flash("Película agregada correctamente.", "ok")
        return redirect(url_for("backoffice.peliculas_admin"))

    return render_template(
        "backadmin/pelicula_form.html",
        v={**datos, **request.form},
        error=mensaje_error(status, respuesta, "No se pudo agregar la película."),
    )


@backoffice_bp.route("/backoffice/peliculas/<int:pelicula_id>/editar", methods=["GET", "POST"])
@solo_admin
def editar_pelicula(pelicula_id):
    if request.method == "GET":
        status, datos = llamar_api("GET", f"/peliculas/{pelicula_id}")
        if status != 200:
            flash(mensaje_error(status, datos, "No se pudo obtener la película."), "error")
            return redirect(url_for("backoffice.peliculas_admin"))
        for campo in ("fecha_inicio_cartelera", "fecha_fin_cartelera"):
            if datos.get(campo):
                datos[campo] = datos[campo][:16]
        return render_template("backadmin/pelicula_form.html", v=datos, editando=True)

    datos = {
        campo: request.form.get(campo, "").strip()
        for campo in (
            "titulo", "sinopsis", "poster_url", "duracion_min",
            "clasificacion", "genero",
        )
    }
    datos.update({
        "fecha_inicio_cartelera": fecha_para_api(request.form.get("fecha_inicio_cartelera")),
        "fecha_fin_cartelera": fecha_para_api(request.form.get("fecha_fin_cartelera")),
    })
    if datos["duracion_min"].isdigit():
        datos["duracion_min"] = int(datos["duracion_min"])

    status, respuesta = llamar_api("PATCH", f"/peliculas/{pelicula_id}", datos)
    if status == 204:
        flash("Película actualizada.", "ok")
        return redirect(url_for("backoffice.peliculas_admin"))
    return render_template(
        "backadmin/pelicula_form.html",
        v={**datos, "id": pelicula_id},
        editando=True,
        error=mensaje_error(status, respuesta, "No se pudo actualizar la película."),
    )


@backoffice_bp.route("/backoffice/peliculas/buscar")
def pelicula_buscar():
    if not es_admin():
        return redirect(url_for("peliculas.inicio"))

    query = request.args.get("q", "").strip()
    pagina = request.args.get("pagina", "1")
    if not query:
        return render_template(
            "backadmin/subirpelicula.html",
            q="",
            resultados=[],
            total=0,
            pagina=1,
            buscado=False,
        )

    status, datos = llamar_api(
        "GET", f"/peliculas/buscar?{urlencode({'q': query, 'pagina': pagina})}"
    )
    if status != 200:
        return render_template(
            "backadmin/subirpelicula.html",
            q=query,
            resultados=[],
            total=0,
            pagina=pagina_para_vista(pagina),
            buscado=True,
            error=mensaje_error(status, datos, "No se pudo buscar en OMDb."),
        )

    status_local, datos_locales = llamar_api("GET", "/peliculas?_limit=100")
    if status_local not in (200, 204):
        return render_template(
            "backadmin/subirpelicula.html",
            q=query,
            resultados=[],
            total=0,
            pagina=pagina_para_vista(pagina),
            buscado=True,
            error=mensaje_error(
                status_local, datos_locales, "No se pudieron verificar las películas cargadas."
            ),
        )
    ids_cargados = {
        pelicula["id_externo"]
        for pelicula in datos_locales.get("peliculas", [])
    }
    for resultado in datos.get("resultados", []):
        resultado["cargada"] = resultado["id_externo"] in ids_cargados

    return render_template(
        "backadmin/subirpelicula.html",
        q=query,
        resultados=datos.get("resultados", []),
        total=datos.get("total_resultados", 0),
        pagina=datos.get("pagina", pagina_para_vista(pagina)),
        buscado=True,
    )


@backoffice_bp.route("/backoffice/peliculas/<int:pelicula_id>/estado", methods=["POST"])
@solo_admin
def cambiar_estado_pelicula(pelicula_id):
    return cambiar_estado(f"/peliculas/{pelicula_id}", "Película", "backoffice.peliculas_admin")