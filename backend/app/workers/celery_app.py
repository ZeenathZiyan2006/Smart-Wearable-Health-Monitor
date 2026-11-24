from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "pulseguardian_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

conf_dict = {
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_track_started": True,
    "broker_connection_retry_on_startup": False
}

# In test environment, execute Celery tasks eagerly in-process without requiring external Redis
if settings.ENVIRONMENT == "testing":
    conf_dict["task_always_eager"] = True
    conf_dict["task_eager_propagates"] = True

celery_app.conf.update(**conf_dict)
