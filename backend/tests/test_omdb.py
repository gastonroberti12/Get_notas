import os
import pytest
import pymysql
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from app import app
from cine_fuente.services.omdb_service import (
    buscar_peliculas,
    obtener_detalle_pelicula,
)
from cine_fuente.validators.peliculas import validar_rango_cartelera
from cine_fuente.utils import ahora_gmt3
from cine_fuente.services.peliculas_service import insertar_pelicula_segura


def fecha_relativa(dias):
    return (
        ahora_gmt3().replace(second=0, microsecond=0) + timedelta(days=dias)
    )


def fecha_iso(fecha):
    return fecha.astimezone(timezone(timedelta(hours=-3))).isoformat(
        timespec="microseconds"
    )


def pelicula_con_fechas(inicio, fin, activa=True):
    return {
        "id": 1,
        "activa": activa,
        "fecha_inicio_cartelera": inicio,
        "fecha_fin_cartelera": fin,
    }


@patch("cine_fuente.services.omdb_service.requests.get")
def test_busqueda_mapea_resultados_omdb(solicitud_mock):
    response = Mock()
    response.json.return_value = {
        "Response": "True",
        "Search": [
            {
                "Title": "Batman Begins",
                "Year": "2005",
                "imdbID": "tt0372784",
                "Type": "movie",
                "Poster": "https://example.test/poster.jpg",
            }
        ],
        "totalResults": "1",
    }
    solicitud_mock.return_value = response

    with patch.dict(os.environ, {"OMDB_API_KEY": "test-key"}):
        result = buscar_peliculas("Batman")

    assert result["total_resultados"] == 1
    assert result["resultados"][0]["id_externo"] == "tt0372784"
    assert solicitud_mock.call_args.kwargs["params"]["apikey"] == "test-key"
    assert solicitud_mock.call_args.kwargs["timeout"] == 8


@patch("cine_fuente.services.omdb_service.requests.get")
def test_detalle_pelicula_normaliza_campos(solicitud_mock):
    response = Mock()
    response.json.return_value = {
        "Response": "True",
        "Title": "Batman Begins",
        "Year": "2005",
        "imdbID": "tt0372784",
        "Plot": "A synopsis.",
        "Poster": "N/A",
        "Runtime": "140 min",
        "Rated": "PG-13",
        "Genre": "Action, Drama",
    }
    solicitud_mock.return_value = response

    with patch.dict(os.environ, {"OMDB_API_KEY": "test-key"}):
        result = obtener_detalle_pelicula("tt0372784")

    assert result["duracion_min"] == 140
    assert result["poster_url"] is None
    assert result["sinopsis"] == "A synopsis."
    assert result["genero"] == "Action"


@patch("cine_fuente.services.omdb_service.requests.get")
def test_busqueda_sin_resultados_devuelve_lista_vacia(solicitud_mock):
    response = Mock()
    response.json.return_value = {
        "Response": "False",
        "Error": "Pelicula no encontrada!",
    }
    solicitud_mock.return_value = response

    with patch.dict(os.environ, {"OMDB_API_KEY": "test-key"}):
        result = app.test_client().get("/peliculas/buscar?q=NoExiste")

    assert result.status_code == 200
    assert result.get_json()["resultados"] == []
    assert result.get_json()["total_resultados"] == 0


def test_busqueda_requiere_consulta():
    response = app.test_client().get("/peliculas/buscar")

    assert response.status_code == 400
    assert response.get_json()["errors"][0]["codigo"] == "pelicula.query.required"


def test_busqueda_informa_clave_api_ausente():
    with patch.dict(os.environ, {}, clear=True):
        response = app.test_client().get("/peliculas/buscar?q=Batman")

    assert response.status_code == 503
    assert "OMDB_API_KEY" in response.get_json()["errors"][0]["mensaje"]


def test_detalle_rechaza_id_imdb_invalido():
    response = app.test_client().get("/peliculas/invalid")

    assert response.status_code == 400
    assert response.get_json()["errors"][0]["codigo"] == "pelicula.invalid"


def test_rango_cartelera_rechaza_formato_invalido():
    try:
        validar_rango_cartelera(
            fecha_relativa(2).strftime("%Y-%m-%d"),
            fecha_iso(fecha_relativa(3)),
        )
    except ValueError as error:
        assert error.args[1] == 400
    else:
        raise AssertionError("Se esperaba un error de validación")


def test_rango_cartelera_rechaza_fin_anterior():
    inicio = fecha_iso(fecha_relativa(2))
    try:
        validar_rango_cartelera(
            inicio,
            fecha_iso(fecha_relativa(1)),
        )
    except ValueError as error:
        assert error.args[1] == 400
    else:
        raise AssertionError("Se esperaba un error de validación")


def test_rango_cartelera_rechaza_fin_igual_al_inicio():
    inicio = fecha_iso(fecha_relativa(2))
    try:
        validar_rango_cartelera(
            inicio,
            inicio,
        )
    except ValueError as error:
        assert error.args[1] == 400
    else:
        raise AssertionError("Se esperaba un error de validación")


def test_rango_cartelera_permite_una_semana():
    inicio = fecha_iso(fecha_relativa(2))
    fin = fecha_iso(fecha_relativa(9))
    assert validar_rango_cartelera(inicio, fin) == (inicio, fin)


@patch("cine_fuente.services.seguridad.decodificar_token", return_value={"sub": "1", "rol": "administrador"})
@patch("cine_fuente.routes.peliculas.actualizar_pelicula")
@patch("cine_fuente.routes.peliculas.obtener_pelicula")
def test_patch_fechas_conserva_las_no_enviadas(obtener_mock, actualizar_mock, _token_mock):
    inicio = fecha_relativa(2)
    fin = fecha_relativa(5)
    nuevo_fin = fecha_relativa(6)
    obtener_mock.return_value = {
        **pelicula_con_fechas(inicio.replace(tzinfo=None), fin.replace(tzinfo=None)),
    }

    client = app.test_client()
    respuesta = client.patch(
        "/peliculas/1",
        json={"fecha_fin_cartelera": fecha_iso(nuevo_fin)},
        headers={"Authorization": "Bearer token"},
    )

    assert respuesta.status_code == 204
    actualizar_mock.assert_called_once_with(1, {
        "fecha_fin_cartelera": nuevo_fin.replace(tzinfo=None),
    })


@pytest.mark.parametrize("payload, esperado", [
    ({"fecha_inicio_cartelera": "inicio"}, {"fecha_inicio_cartelera": "inicio"}),
    (
        {"fecha_inicio_cartelera": "inicio", "fecha_fin_cartelera": "fin"},
        {"fecha_inicio_cartelera": "inicio", "fecha_fin_cartelera": "fin"},
    ),
    ({"titulo": "Título sin tocar fechas"}, {"titulo": "Título sin tocar fechas"}),
])
@patch("cine_fuente.services.seguridad.decodificar_token", return_value={"sub": "1", "rol": "administrador"})
@patch("cine_fuente.routes.peliculas.actualizar_pelicula")
@patch("cine_fuente.routes.peliculas.obtener_pelicula")
def test_patch_fechas_usa_solo_los_campos_enviados(
    obtener_mock, actualizar_mock, _token_mock, payload, esperado
):
    inicio = fecha_relativa(2)
    fin = fecha_relativa(5)
    payload = {
        campo: (
            fecha_iso(fecha_relativa(3 if campo == "fecha_inicio_cartelera" else 6))
            if valor in ("inicio", "fin") else valor
        )
        for campo, valor in payload.items()
    }
    esperado = {
        campo: (
            fecha_relativa(3 if campo == "fecha_inicio_cartelera" else 6).replace(tzinfo=None)
            if valor in ("inicio", "fin") else valor
        )
        for campo, valor in esperado.items()
    }
    obtener_mock.return_value = {
        **pelicula_con_fechas(inicio.replace(tzinfo=None), fin.replace(tzinfo=None)),
    }

    respuesta = app.test_client().patch(
        "/peliculas/1",
        json=payload,
        headers={"Authorization": "Bearer token"},
    )

    assert respuesta.status_code == 204
    actualizar_mock.assert_called_once_with(1, esperado)


@patch("cine_fuente.services.seguridad.decodificar_token", return_value={"sub": "1", "rol": "administrador"})
@patch("cine_fuente.routes.peliculas.actualizar_pelicula")
@patch("cine_fuente.routes.peliculas.obtener_pelicula")
def test_patch_solo_fin_pelicula_en_curso(obtener_mock, actualizar_mock, _token_mock):
    inicio = fecha_relativa(-2).replace(tzinfo=None)
    fin = fecha_relativa(3).replace(tzinfo=None)
    nuevo_fin = fecha_relativa(4)
    obtener_mock.return_value = pelicula_con_fechas(inicio, fin)

    respuesta = app.test_client().patch(
        "/peliculas/1",
        json={"fecha_fin_cartelera": fecha_iso(nuevo_fin)},
        headers={"Authorization": "Bearer token"},
    )

    assert respuesta.status_code == 204
    actualizar_mock.assert_called_once_with(1, {"fecha_fin_cartelera": nuevo_fin.replace(tzinfo=None)})


@patch("cine_fuente.services.seguridad.decodificar_token", return_value={"sub": "1", "rol": "administrador"})
@patch("cine_fuente.routes.peliculas.obtener_pelicula")
def test_patch_inicio_pasado_distinto_rechaza(obtener_mock, _token_mock):
    obtener_mock.return_value = pelicula_con_fechas(
        fecha_relativa(2).replace(tzinfo=None), fecha_relativa(5).replace(tzinfo=None)
    )
    respuesta = app.test_client().patch(
        "/peliculas/1",
        json={"fecha_inicio_cartelera": fecha_iso(fecha_relativa(-1))},
        headers={"Authorization": "Bearer token"},
    )
    assert respuesta.status_code == 400
    assert respuesta.get_json()["errors"][0]["codigo"] == "pelicula.fecha.pasada"


@patch("cine_fuente.services.seguridad.decodificar_token", return_value={"sub": "1", "rol": "administrador"})
@patch("cine_fuente.routes.peliculas.obtener_pelicula_por_imdb", return_value=None)
def test_post_inicio_pasado_rechaza(_existente_mock, _token_mock):
    respuesta = app.test_client().post(
        "/peliculas",
        json={
            "id_externo": "tt0000001",
            "fecha_inicio_cartelera": fecha_iso(fecha_relativa(-1)),
            "fecha_fin_cartelera": fecha_iso(fecha_relativa(2)),
        },
        headers={"Authorization": "Bearer token"},
    )
    assert respuesta.status_code == 400
    assert respuesta.get_json()["errors"][0]["codigo"] == "pelicula.fecha.pasada"


@pytest.mark.parametrize("payload, status", [
    ({"activa": True}, 400),
    ({"activa": True, "fecha_inicio_cartelera": fecha_iso(fecha_relativa(1)),
      "fecha_fin_cartelera": fecha_iso(fecha_relativa(5))}, 204),
])
@patch("cine_fuente.services.seguridad.decodificar_token", return_value={"sub": "1", "rol": "administrador"})
@patch("cine_fuente.routes.peliculas.actualizar_pelicula")
@patch("cine_fuente.routes.peliculas.obtener_pelicula")
def test_reactivacion_requiere_ambas_fechas(
    obtener_mock, actualizar_mock, _token_mock, payload, status
):
    obtener_mock.return_value = pelicula_con_fechas(
        fecha_relativa(-5).replace(tzinfo=None), fecha_relativa(-1).replace(tzinfo=None), False
    )
    respuesta = app.test_client().patch(
        "/peliculas/1", json=payload, headers={"Authorization": "Bearer token"}
    )
    assert respuesta.status_code == status


@patch("cine_fuente.services.peliculas_service.insertar_pelicula")
def test_integrity_error_duplicado_se_convierte(_insertar_mock):
    _insertar_mock.side_effect = pymysql.err.IntegrityError(1062, "duplicate")
    with pytest.raises(ValueError) as error:
        insertar_pelicula_segura({"id_externo": "tt0000001"})
    assert error.value.args[1] == 409
    assert error.value.args[0]["errors"][0]["codigo"] == "pelicula.already.exists"


@patch("cine_fuente.services.peliculas_service.insertar_pelicula")
def test_integrity_error_no_duplicado_se_propaga(_insertar_mock):
    error = pymysql.err.IntegrityError(1048, "null")
    _insertar_mock.side_effect = error
    with pytest.raises(pymysql.err.IntegrityError) as recibido:
        insertar_pelicula_segura({"id_externo": "tt0000001"})
    assert recibido.value is error


@patch("cine_fuente.repositories.peliculas.ahora_gmt3")
@patch("cine_fuente.repositories.peliculas.ejecutar_consulta")
def test_consultar_peliculas_aplica_vigencia_sin_activa(consulta_mock, ahora_mock):
    ahora = datetime(2026, 11, 5, 10)
    ahora_mock.return_value = ahora.replace(tzinfo=timezone(timedelta(hours=-3)))
    from cine_fuente.repositories.peliculas import consultar_peliculas
    consultar_peliculas()
    sql = consulta_mock.call_args.args[0]
    parametros = consulta_mock.call_args.args[1] if len(consulta_mock.call_args.args) > 1 else ()
    assert "fecha_inicio_cartelera <= %s" in sql
    assert parametros == (ahora, ahora)


@patch("cine_fuente.repositories.peliculas.ejecutar_consulta")
def test_consultar_peliculas_activas_no_aplica_vigencia(consulta_mock):
    from cine_fuente.repositories.peliculas import consultar_peliculas
    consultar_peliculas(True)
    sql = consulta_mock.call_args.args[0]
    parametros = consulta_mock.call_args.args[1] if len(consulta_mock.call_args.args) > 1 else ()
    assert "fecha_inicio_cartelera" not in sql
    assert parametros == ()


def test_post_rechaza_body_no_objeto():
    with patch("cine_fuente.services.seguridad.decodificar_token",
               return_value={"sub": "1", "rol": "administrador"}):
        respuesta = app.test_client().post(
            "/peliculas",
            json=["x"],
            headers={"Authorization": "Bearer token"},
        )

    assert respuesta.status_code == 400
    assert respuesta.get_json()["errors"][0]["codigo"] == "pelicula.invalid"
