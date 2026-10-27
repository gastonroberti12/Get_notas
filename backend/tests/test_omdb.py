import os
import unittest
from unittest.mock import Mock, patch

from app import app
from cine_fuente.services.omdb_service import get_movie_details, search_movies


class OmdbIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.api_key_patch = patch.dict(os.environ, {"OMDB_API_KEY": "test-key"})
        self.api_key_patch.start()
        self.addCleanup(self.api_key_patch.stop)

    @patch("cine_fuente.services.omdb_service.requests.get")
    def test_search_maps_omdb_results(self, get):
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
        get.return_value = response

        result = search_movies("Batman")

        self.assertEqual(result["total_resultados"], 1)
        self.assertEqual(result["resultados"][0]["id_externo"], "tt0372784")
        self.assertEqual(get.call_args.kwargs["params"]["apikey"], "test-key")
        self.assertEqual(get.call_args.kwargs["timeout"], 8)

    @patch("cine_fuente.services.omdb_service.requests.get")
    def test_movie_details_normalize_fields(self, get):
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
        get.return_value = response

        result = get_movie_details("tt0372784")

        self.assertEqual(result["duracion_min"], 140)
        self.assertIsNone(result["poster_url"])
        self.assertEqual(result["sinopsis"], "A synopsis.")

    @patch("cine_fuente.services.omdb_service.requests.get")
    def test_search_with_no_results_returns_empty_list(self, get):
        response = Mock()
        response.json.return_value = {
            "Response": "False",
            "Error": "Movie not found!",
        }
        get.return_value = response

        result = self.client.get("/api/peliculas/buscar?q=NoExiste")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_json()["resultados"], [])
        self.assertEqual(result.get_json()["total_resultados"], 0)

    def test_search_requires_query(self):
        response = self.client.get("/api/peliculas/buscar")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_search_reports_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.get("/api/peliculas/buscar?q=Batman")

        self.assertEqual(response.status_code, 503)
        self.assertIn("OMDB_API_KEY", response.get_json()["error"])

    def test_details_reject_invalid_imdb_id(self):
        response = self.client.get("/api/peliculas/invalid")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
