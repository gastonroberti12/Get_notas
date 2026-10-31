from datetime import timedelta

from cine_fuente.repositories import entradas as entradas_repo
from cine_fuente.services.reservas import entrada_api, normalizar_fecha_local
from cine_fuente.utils import ahora_gmt3, construir_error_api


def error_entrada(codigo, mensaje, estado):
    raise ValueError(construir_error_api(codigo, mensaje, mensaje), estado)


def listar_entradas(filtros, limit, offset):
    entradas = entradas_repo.listar_entradas(filtros, limit, offset)
    total = entradas_repo.contar_entradas(filtros)
    return [entrada_api(entrada) for entrada in entradas], total
