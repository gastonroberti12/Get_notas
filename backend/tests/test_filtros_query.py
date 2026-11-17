import unittest

from werkzeug.datastructures import MultiDict

from cine_fuente.validators.funciones import (
    validar_eliminacion,
    validar_filtros as validar_filtros_funciones,
    validar_modificacion,
)
from cine_fuente.validators.peliculas import validar_filtros as validar_filtros_peliculas
from cine_fuente.validators.entradas import (
    validar_body as validar_body_entrada,
)


class FiltrosQueryTest(unittest.TestCase):
    def test_codigo_qr_acepta_formatos_normalizables(self):
        for valor, esperado in (
            ("K7M2-9QXP", "K7M2-9QXP"),
            ("k7m2-9qxp", "K7M2-9QXP"),
            ("k7m2 9qxp", "K7M2-9QXP"),
            ("K7M29QXP", "K7M2-9QXP"),
        ):
            with self.subTest(valor=valor):
                self.assertEqual(
                    validar_body_entrada({"codigo_qr": valor}),
                    esperado,
                )

    def test_codigo_qr_rechaza_formato_invalido(self):
        for valor in ("ABC", "K7M2_9QXP", "K0M2-9QXP", "I7M2-9QXP"):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError) as error:
                    validar_body_entrada({"codigo_qr": valor})
                self.assertEqual(error.exception.args[1], 400)

    def test_funciones_rechaza_ids_no_numericos_o_no_positivos(self):
        for valor in ("abc", "0", "-2"):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError) as error:
                    validar_filtros_funciones(MultiDict([("sala_id", valor)]))
                self.assertEqual(error.exception.args[1], 400)

    def test_funciones_acepta_fecha_iso(self):
        filtros = validar_filtros_funciones(MultiDict([("fecha", "2026-11-20")]))
        self.assertEqual(filtros["fecha"].isoformat(), "2026-11-20")

    def test_funciones_rechaza_fecha_invalida(self):
        for valor in ("20-11-2026", "2026-2-20", "2026-02-30"):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError) as error:
                    validar_filtros_funciones(MultiDict([("fecha", valor)]))
                self.assertEqual(error.exception.args[1], 400)

    def test_peliculas_rechaza_sucursal_no_numerica(self):
        with self.assertRaises(ValueError) as error:
            validar_filtros_peliculas(MultiDict([("sucursal_id", "abc")]))
        self.assertEqual(error.exception.args[1], 400)

    def test_peliculas_acepta_y_normaliza_filtros_de_texto(self):
        filtros = validar_filtros_peliculas(MultiDict([
            ("titulo", "  Incep  "),
            ("genero", " Sci-Fi "),
        ]))
        self.assertEqual(filtros["titulo"], "Incep")
        self.assertEqual(filtros["genero"], "Sci-Fi")

    def test_peliculas_rechaza_filtros_de_texto_vacios_o_largos(self):
        for campo, valor in (("titulo", " "), ("genero", "x" * 101)):
            with self.subTest(campo=campo):
                with self.assertRaises(ValueError) as error:
                    validar_filtros_peliculas(MultiDict([(campo, valor)]))
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
