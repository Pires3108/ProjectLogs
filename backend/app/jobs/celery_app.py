from celery import Celery

from app.config import get_settings

settings = get_settings()
celery_app = Celery("ataviva", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)
celery_app.autodiscover_tasks(["app.jobs"])
