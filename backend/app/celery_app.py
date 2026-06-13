import ssl

from celery import Celery

from app.core.config import settings

_broker = settings.CELERY_BROKER_URL or settings.REDIS_URL or "redis://localhost:6379/0"
_backend = settings.CELERY_RESULT_BACKEND or settings.REDIS_URL or "redis://localhost:6379/0"

celery_app = Celery("agentops_hub", broker=_broker, backend=_backend)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="agentops",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=2,
    task_queues={
        "agentops": {"exchange": "agentops", "routing_key": "agentops"},
        "agentops.dlq": {"exchange": "agentops.dlq", "routing_key": "agentops.dlq"},
    },
    task_routes={
        "ingest.dlq": {"queue": "agentops.dlq"},
    },
)

if _broker.startswith("rediss://"):
    _ssl = {"ssl_cert_reqs": ssl.CERT_NONE}
    celery_app.conf.broker_use_ssl = _ssl
    celery_app.conf.redis_backend_use_ssl = _ssl

celery_app.autodiscover_tasks(["app.tasks"])
