import os
from celery import Celery

celery_app = Celery(
    "hookshot",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)

# Aquí luego agregas beat_schedule para health checks