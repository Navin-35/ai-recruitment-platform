import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory status store for background tasks
task_status_store: Dict[str, Dict[str, Any]] = {}
thread_pool = ThreadPoolExecutor(max_workers=4)


class AsyncWorkerQueue:
    """
    Asynchronous task queue supporting Redis queue workers and
    in-memory ThreadPool background workers for development.
    """

    def __init__(self):
        self.redis_client = None
        if settings.enable_redis_queue:
            try:
                import redis
                self.redis_client = redis.from_url(settings.redis_url)
                logger.info(f"Connected to Redis queue at {settings.redis_url}")
            except Exception as e:
                logger.warning(f"Could not connect to Redis, falling back to ThreadPool worker: {e}")

    def enqueue_task(self, task_type: str, payload: Dict[str, Any]) -> str:
        """
        Enqueues an async background task (e.g., process_resume, match_candidate).
        Returns a unique task_id.
        """
        import uuid
        task_id = str(uuid.uuid4())
        task_status_store[task_id] = {
            "task_id": task_id,
            "task_type": task_type,
            "status": "queued",
            "progress": 0,
            "payload": payload,
        }

        if self.redis_client:
            try:
                queue_item = json.dumps({"task_id": task_id, "task_type": task_type, "payload": payload})
                self.redis_client.rpush("recruitment_tasks", queue_item)
                logger.info(f"Task {task_id} pushed to Redis queue")
                return task_id
            except Exception as e:
                logger.warning(f"Redis enqueue failed: {e}. Executing in threadpool.")

        # Local background thread execution
        thread_pool.submit(self._execute_task, task_id, task_type, payload)
        return task_id

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        return task_status_store.get(task_id)

    def _execute_task(self, task_id: str, task_type: str, payload: Dict[str, Any]):
        """Executes task with status tracking."""
        from app.core.database import SessionLocal

        task_status_store[task_id]["status"] = "processing"
        task_status_store[task_id]["progress"] = 25

        db = SessionLocal()
        try:
            if task_type == "process_resume":
                from app.workflows.matching_pipeline import MatchingPipeline
                resume_id = payload["resume_id"]
                task_status_store[task_id]["progress"] = 50
                candidate = MatchingPipeline.process_and_index_resume(resume_id=resume_id, db=db)
                task_status_store[task_id]["status"] = "completed"
                task_status_store[task_id]["progress"] = 100
                task_status_store[task_id]["result"] = {"candidate_id": candidate.id, "candidate_name": candidate.name}

            elif task_type == "match_candidate":
                from app.workflows.matching_pipeline import MatchingPipeline
                job_id = payload["job_id"]
                candidate_id = payload["candidate_id"]
                task_status_store[task_id]["progress"] = 60
                res = MatchingPipeline.match_candidate_to_job(job_id=job_id, candidate_id=candidate_id, db=db)
                task_status_store[task_id]["status"] = "completed"
                task_status_store[task_id]["progress"] = 100
                task_status_store[task_id]["result"] = res

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            task_status_store[task_id]["status"] = "failed"
            task_status_store[task_id]["error"] = str(e)
        finally:
            db.close()


async_worker = AsyncWorkerQueue()
