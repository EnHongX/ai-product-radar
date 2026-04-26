from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ai_product_radar",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_time_limit=settings.CRAWL_TIMEOUT_SECONDS + 60,
    task_soft_time_limit=settings.CRAWL_TIMEOUT_SECONDS,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
