from celery import Celery
from core.config.env_config import sttgs

celery_app = Celery(
    "consumer",
    broker=sttgs.get("CELERY_BROKER_URL"),
    backend="redis://127.0.0.1:6379",
)
