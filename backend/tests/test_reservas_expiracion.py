from datetime import datetime

from cine_fuente.services.reservas import reserva_api


def test_reserva_expira_diez_minutos_despues_de_crearse():
    reserva = reserva_api({
        "id": 12,
        "usuario_id": 4,
        "funcion_id": 8,
        "fecha_compra": datetime(2026, 11, 6, 10, 0),
        "estado": "pendiente",
        "fecha_cancelacion": None,
        "total": 7500,
    })

    assert reserva["fecha_expiracion"] == "2026-11-06T10:10:00.000000-03:00"
