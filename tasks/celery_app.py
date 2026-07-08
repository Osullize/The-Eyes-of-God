from __future__ import annotations

import os

from celery import Celery

from config.env import load_project_env


load_project_env()


DEFAULT_BROKER_URL = "redis://127.0.0.1:6379/0"
DEFAULT_RESULT_BACKEND = "redis://127.0.0.1:6379/1"


celery_app = Celery(
    "lead_tasks",
    broker=os.environ.get("CELERY_BROKER_URL", DEFAULT_BROKER_URL),
    backend=os.environ.get("CELERY_RESULT_BACKEND", DEFAULT_RESULT_BACKEND),
    include=["tasks.celery_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
