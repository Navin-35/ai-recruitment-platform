import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class ObservabilityTracer:
    """
    Observability and telemetry layer supporting Langfuse tracing with
    graceful local performance metrics fallback.
    """

    def __init__(self):
        self._langfuse_client = None
        if settings.enable_langfuse and settings.langfuse_public_key and settings.langfuse_secret_key:
            try:
                from langfuse import Langfuse
                self._langfuse_client = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
                logger.info("Langfuse observability client initialized.")
            except Exception as e:
                logger.warning(f"Could not initialize Langfuse: {e}")

    @property
    def is_enabled(self) -> bool:
        return self._langfuse_client is not None

    @contextmanager
    def trace_span(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager to track duration, inputs, outputs, and errors for pipeline steps:
        (e.g., resume_extraction, hybrid_retrieval, reranking, scoring, explanation).
        """
        start_time = time.time()
        span_data = {"name": name, "metadata": metadata or {}, "status": "running"}
        span_obj = None

        if self._langfuse_client:
            try:
                span_obj = self._langfuse_client.span(name=name, metadata=metadata)
            except Exception as e:
                logger.debug(f"Langfuse span error: {e}")

        try:
            yield span_data
            elapsed_ms = (time.time() - start_time) * 1000
            span_data["duration_ms"] = round(elapsed_ms, 2)
            span_data["status"] = "success"
            if span_obj:
                try:
                    span_obj.end(output=span_data.get("output"))
                except Exception:
                    pass
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            span_data["duration_ms"] = round(elapsed_ms, 2)
            span_data["status"] = "error"
            span_data["error"] = str(e)
            if span_obj:
                try:
                    span_obj.end(level="ERROR", status_message=str(e))
                except Exception:
                    pass
            raise


tracer = ObservabilityTracer()
