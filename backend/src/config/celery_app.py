"""Celery 入口：backend 投递任务，worker 容器消费（beat 写心跳）。"""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from src.config.settings import settings

celery_app = Celery(
    "pricelens",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    worker_hijack_root_logger=False,
)

celery_app.conf.beat_schedule = {
    "pricelens-heartbeat": {"task": "pricelens.heartbeat", "schedule": 20.0},
    "pricelens-site-scan": {"task": "pricelens.scan_all_sites", "schedule": crontab(minute="*/30")},
}

TASK_RUN_EXTRACTION = "pricelens.run_extraction"
TASK_SCAN_SITE = "pricelens.scan_site"
TASK_SCAN_ALL = "pricelens.scan_all_sites"
