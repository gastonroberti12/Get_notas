import os
import unittest
from unittest.mock import Mock, patch

from app import app
from cine_fuente.services.omdb_service import (
    buscar_peliculas,
    obtener_detalle_pelicula,
)


class OmdbIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.api_key_patch = patch.dict(os.environ, {"OMDB_API_KEY": "test-key"})
        self.api_key_patch.start()
        self.addCleanup(self.api_key_patch.stop)

    @patch("cine_fuente.services.omdb_service.requests.get")
    def test_busqueda_mapea_resultados_omdb(self, solicitud_mock):
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

        result = buscar_peliculas("Batman")

        self.assertEqual(result["total_resultados"], 1)
        self.assertEqual(result["resultados"][0]["id_externo"], "tt0372784")
        self.assertEqual(solicitud_mock.call_args.kwargs["params"]["apikey"], "test-key")
        self.assertEqual(solicitud_mock.call_args.kwargs["timeout"], 8)

    @patch("cine_fuente.services.omdb_service.requests.get")
    def test_detalle_pelicula_normaliza_campos(self, solicitud_mock):
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

        result = obtener_detalle_pelicula("tt0372784")

        self.assertEqual(result["duracion_min"], 140)
        self.assertIsNone(result["poster_url"])
        self.assertEqual(result["sinopsis"], "A synopsis.")

    @patch("cine_fuente.services.omdb_service.requests.get")
    def test_busqueda_sin_resultados_devuelve_lista_vacia(self, solicitud_mock):
        response = Mock()
        response.json.return_value = {
            "Response": "False",
            "Error": "Pelicula no encontrada! ",
        }
        solicitud_mock.return_value = response

        result = self.client.get("/api/peliculas/buscar?q=NoExiste")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_json()["resultados"], [])
        self.assertEqual(result.get_json()["total_resultados"], 0)

    def test_busqueda_requiere_consulta(self):
        response = self.client.get("/api/peliculas/buscar")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_busqueda_informa_clave_api_ausente(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.get("/api/peliculas/buscar?q=Batman")

        self.assertEqual(response.status_code, 503)
        self.assertIn("OMDB_API_KEY", response.get_json()["error"])

    def test_detalle_rechaza_id_imdb_invalido(self):
        response = self.client.get("/api/peliculas/invalid")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
