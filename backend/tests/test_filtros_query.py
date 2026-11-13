import unittest

from werkzeug.datastructures import MultiDict

from cine_fuente.validators.funciones import (
    validar_eliminacion,
    validar_filtros as validar_filtros_funciones,
    validar_modificacion,
)
from cine_fuente.validators.peliculas import validar_filtros as validar_filtros_peliculas


class FiltrosQueryTest(unittest.TestCase):
    def test_funciones_rechaza_ids_no_numericos_o_no_positivos(self):
        for valor in ("abc", "0", "-2"):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError) as error:
                    validar_filtros_funciones(MultiDict([("sala_id", valor)]))
                self.assertEqual(error.exception.args[1], 400)

    def test_peliculas_rechaza_sucursal_no_numerica(self):
        with self.assertRaises(ValueError) as error:
            validar_filtros_peliculas(MultiDict([("sucursal_id", "abc")]))
        self.assertEqual(error.exception.args[1], 400)

    def test_acepta_ids_validos_y_filtros_omitidos(self):
        self.assertEqual(
            validar_filtros_funciones(MultiDict([("sala_id", "2")]))["sala_id"],
            2,
        )
        self.assertIsNone(validar_filtros_peliculas(MultiDict())["sucursal_id"])

    def test_funciones_rechaza_cuerpos_json_no_objeto(self):
        for validar in (validar_modificacion, validar_eliminacion):
            with self.subTest(validar=validar.__name__):
                with self.assertRaises(ValueError) as error:
                    validar(1)
                self.assertEqual(error.exception.args[1], 400)

    def test_eliminacion_acepta_sin_cuerpo_o_booleano(self):
        self.assertFalse(validar_eliminacion(None))
        self.assertTrue(validar_eliminacion({"fisica": True}))


if __name__ == "__main__":
    unittest.main()
