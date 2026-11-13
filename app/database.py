"""Small persistence adapter for the local portfolio demo."""
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from .config import settings


@dataclass
class TaskRecord:
    id: str
    description: str
    require_approval: bool
    status: str
    plan: list[str]
    result: str | None = None
    error: str | None = None

def _path() -> str:
    return settings.database_url.removeprefix("sqlite:///") if settings.database_url.startswith("sqlite:///") else "orchestrator.db"

def connect():
    return sqlite3.connect(_path())

def init_db() -> None:
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, description TEXT NOT NULL, require_approval INTEGER NOT NULL, status TEXT NOT NULL, plan TEXT NOT NULL, result TEXT, error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")

def save_task(task: TaskRecord) -> None:
    now = datetime.now(UTC).isoformat()
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (task.id, task.description, int(task.require_approval), task.status, json.dumps(task.plan), task.result, task.error, now, now))

def get_task(task_id: str) -> TaskRecord | None:
    with connect() as db:
        row = db.execute("SELECT id, description, require_approval, status, plan, result, error FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return TaskRecord(row[0], row[1], bool(row[2]), row[3], json.loads(row[4]), row[5], row[6]) if row else None
