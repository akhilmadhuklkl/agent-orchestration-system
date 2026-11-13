import json

from redis import Redis

from .config import settings

QUEUE_NAME = "orchestrator:tasks"

def enqueue(task_id: str) -> None:
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    client.rpush(QUEUE_NAME, json.dumps({"task_id": task_id}))

def dequeue(timeout: int = 5) -> str | None:
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    item = client.blpop(QUEUE_NAME, timeout=timeout)
    if not item:
        return None
    return json.loads(item[1])["task_id"]
