from celery import Celery
from core.config.env_config import sttgs

celery_app = Celery(
    "consumer",
    broker=sttgs.get("CELERY_BROKER_URL"),
    backend=sttgs.get("CELERY_BAKCEND_URI"),
)
