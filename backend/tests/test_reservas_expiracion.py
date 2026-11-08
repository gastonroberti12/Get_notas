from datetime import datetime

from cine_fuente.services.reservas import reserva_api

#define el tiempo de expiración de una reserva en minutos
RESERVA_EXPIRACION_MINUTOS = 8
def test_reserva_expiracion():
    reserva = reserva_api({
        "id": 12,
        "usuario_id": 4,
        "funcion_id": 8,
        "fecha_compra": datetime(2026, 11, 6, 10, 0),
        "estado": "pendiente",
        "fecha_cancelacion": None,
        "total": 7500,
    })
#la fecha de expiración esperada sumando 8 minutos a la fecha de compra
    assert reserva["fecha_expiracion"] == "2026-11-06T10:08:00.000000-03:00"
