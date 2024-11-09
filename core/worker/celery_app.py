from celery import Celery
from core.config import sttgs

print(sttgs.get("RABBITMQ_URI", "pyamqp://"))
celery_app = Celery(
    "celery_worker",
    broker="pyamqp://",
)

celery_app.autodiscover_tasks(["core.worker"])
