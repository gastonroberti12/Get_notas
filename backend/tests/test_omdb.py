import os
from unittest.mock import Mock, patch

from app import app
from cine_fuente.services.omdb_service import (
    buscar_peliculas,
    obtener_detalle_pelicula,
)


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


@patch("cine_fuente.services.omdb_service.requests.get")
def test_busqueda_sin_resultados_devuelve_lista_vacia(solicitud_mock):
    response = Mock()
    response.json.return_value = {
        "Response": "False",
        "Error": "Pelicula no encontrada! ",
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
    assert "error" in response.get_json()


def test_busqueda_informa_clave_api_ausente():
    with patch.dict(os.environ, {}, clear=True):
        response = app.test_client().get("/peliculas/buscar?q=Batman")

    assert response.status_code == 503
    assert "OMDB_API_KEY" in response.get_json()["error"]


def test_detalle_rechaza_id_imdb_invalido():
    response = app.test_client().get("/peliculas/invalid")

    assert response.status_code == 400
    assert "error" in response.get_json()
