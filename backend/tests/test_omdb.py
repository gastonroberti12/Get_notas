import os
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from app import app
from cine_fuente.services.omdb_service import (
    buscar_peliculas,
    obtener_detalle_pelicula,
)
from cine_fuente.validators.peliculas import validar_rango_cartelera


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
            "2026-11-20",
            "2026-11-21T00:00:00.000000-03:00",
        )
    except ValueError as error:
        assert error.args[1] == 400
    else:
        raise AssertionError("Se esperaba un error de validación")


def test_rango_cartelera_rechaza_fin_anterior():
    try:
        validar_rango_cartelera(
            "2026-11-20T21:30:00.000000-03:00",
            "2026-11-19T21:30:00.000000-03:00",
        )
    except ValueError as error:
        assert error.args[1] == 400
    else:
        raise AssertionError("Se esperaba un error de validación")


def test_rango_cartelera_rechaza_fin_igual_al_inicio():
    try:
        validar_rango_cartelera(
            "2026-11-20T21:30:00.000000-03:00",
            "2026-11-20T21:30:00.000000-03:00",
        )
    except ValueError as error:
        assert error.args[1] == 400
    else:
        raise AssertionError("Se esperaba un error de validación")


def test_rango_cartelera_permite_una_semana():
    inicio = "2026-11-20T21:30:00.000000-03:00"
    fin = "2026-11-27T21:30:00.000000-03:00"
    assert validar_rango_cartelera(inicio, fin) == (inicio, fin)


@patch("cine_fuente.services.seguridad.decodificar_token", return_value={"sub": "1", "rol": "administrador"})
@patch("cine_fuente.routes.peliculas.actualizar_pelicula")
@patch("cine_fuente.routes.peliculas.obtener_pelicula")
def test_patch_fechas_conserva_las_no_enviadas(obtener_mock, actualizar_mock, _token_mock):
    obtener_mock.return_value = {
        "id": 1,
        "activa": True,
        "fecha_inicio_cartelera": datetime(2026, 11, 20, 10),
        "fecha_fin_cartelera": datetime(2026, 11, 25, 10),
    }

    client = app.test_client()
    respuesta = client.patch(
        "/peliculas/1",
        json={"fecha_fin_cartelera": "2026-11-26T10:00:00.000000-03:00"},
        headers={"Authorization": "Bearer token"},
    )

    assert respuesta.status_code == 204
    actualizar_mock.assert_called_once_with(1, {
        "fecha_fin_cartelera": datetime(2026, 11, 26, 10),
    })


@pytest.mark.parametrize("payload", [
    {"fecha_inicio_cartelera": "2026-11-21T10:00:00.000000-03:00"},
    {
        "fecha_inicio_cartelera": "2026-11-21T10:00:00.000000-03:00",
        "fecha_fin_cartelera": "2026-11-26T10:00:00.000000-03:00",
    },
    {"titulo": "Título sin tocar fechas"},
])
@patch("cine_fuente.services.seguridad.decodificar_token", return_value={"sub": "1", "rol": "administrador"})
@patch("cine_fuente.routes.peliculas.actualizar_pelicula")
@patch("cine_fuente.routes.peliculas.obtener_pelicula")
def test_patch_fechas_usa_solo_los_campos_enviados(
    obtener_mock, actualizar_mock, _token_mock, payload
):
    obtener_mock.return_value = {
        "id": 1,
        "activa": True,
        "fecha_inicio_cartelera": datetime(2026, 11, 20, 10),
        "fecha_fin_cartelera": datetime(2026, 11, 25, 10),
    }

    respuesta = app.test_client().patch(
        "/peliculas/1",
        json=payload,
        headers={"Authorization": "Bearer token"},
    )

    assert respuesta.status_code == 204
    assert actualizar_mock.call_count == 1
    cambios = actualizar_mock.call_args.args[1]
    assert "fecha_inicio_cartelera" not in cambios or "fecha_inicio_cartelera" in payload
    assert "fecha_fin_cartelera" not in cambios or "fecha_fin_cartelera" in payload


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
