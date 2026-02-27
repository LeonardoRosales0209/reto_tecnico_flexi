import os
from celery import Celery

from celery.schedules import crontab

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery_app = Celery(
    "hookshot",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
    include=["app.tasks.webhook_tasks"],  # auto-discover tasks
)

celery_app.conf.beat_schedule = {
    "health-check-every-5-minutes": {
        "task": "health_check_subscriptions",
        "schedule": 300.0,  # cada 5 minutos
    },
}