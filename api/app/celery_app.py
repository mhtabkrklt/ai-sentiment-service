# Асинхронная очередь задач
from celery import Celery

from app.config import settings

celery = Celery(
    "sentiment_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    worker_hijack_root_logger=False,
)
