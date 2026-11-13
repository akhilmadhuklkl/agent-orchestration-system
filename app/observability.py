import json
import logging
import time
from collections import Counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("orchestrator")
logging.basicConfig(level=logging.INFO, format="%(message)s")
metrics = Counter()

class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        metrics["http_requests_total"] += 1
        metrics[f"http_status_{response.status_code}"] += 1
        logger.info(json.dumps({"event": "http_request", "request_id": request_id, "method": request.method, "path": request.url.path, "status": response.status_code, "duration_ms": duration_ms}))
        response.headers["X-Request-ID"] = request_id
        return response

def record_task(status: str) -> None:
    metrics["tasks_total"] += 1
    metrics[f"tasks_status_{status}"] += 1

def record_tool(status: str) -> None:
    metrics["tool_runs_total"] += 1
    metrics[f"tool_runs_status_{status}"] += 1
