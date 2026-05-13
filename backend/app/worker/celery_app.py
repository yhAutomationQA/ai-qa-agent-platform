from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ai_qa_platform",
    broker=settings.REDIS_URL.replace("redis://", "redis://", 1),
    backend=settings.REDIS_URL.replace("redis://", "redis://", 1),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "run_test_case": {"queue": "test_runs"},
        "execute_agent": {"queue": "agents"},
        "process_result": {"queue": "results"},
    },
)


@celery_app.task(bind=True, max_retries=3)
def run_test_case(self, test_case_id: str, run_id: str) -> dict:
    return {"status": "completed", "test_case_id": test_case_id, "run_id": run_id}


@celery_app.task(bind=True, max_retries=3)
def execute_agent(self, agent_id: str, task: dict) -> dict:
    return {"status": "completed", "agent_id": agent_id}


@celery_app.task(bind=True)
def process_result(self, run_id: str, result: dict) -> dict:
    return {"status": "processed", "run_id": run_id}
