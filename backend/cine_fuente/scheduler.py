from apscheduler.schedulers.background import BackgroundScheduler

from constants import EXPIRACION_INTERVALO_SEGUNDOS
from cine_fuente.services.reservas import procesar_expiraciones


def iniciar_scheduler():
    """Arranca el job periódico que expira las reservas pendientes vencidas."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        procesar_expiraciones, "interval", seconds=EXPIRACION_INTERVALO_SEGUNDOS,
        id="expirar_reservas", max_instances=1, coalesce=True,
    )
    scheduler.start()
    return scheduler