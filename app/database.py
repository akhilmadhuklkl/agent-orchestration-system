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

@dataclass
class EventRecord:
    task_id: str
    event_type: str
    message: str
    created_at: str

def _path() -> str:
    return settings.database_url.removeprefix("sqlite:///") if settings.database_url.startswith("sqlite:///") else "orchestrator.db"

def connect():
    return sqlite3.connect(_path())

def init_db() -> None:
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, description TEXT NOT NULL, require_approval INTEGER NOT NULL, status TEXT NOT NULL, plan TEXT NOT NULL, result TEXT, error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS task_events (task_id TEXT NOT NULL, event_type TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL)")

def save_task(task: TaskRecord) -> None:
    now = datetime.now(UTC).isoformat()
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (task.id, task.description, int(task.require_approval), task.status, json.dumps(task.plan), task.result, task.error, now, now))

def get_task(task_id: str) -> TaskRecord | None:
    with connect() as db:
        row = db.execute("SELECT id, description, require_approval, status, plan, result, error FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return TaskRecord(row[0], row[1], bool(row[2]), row[3], json.loads(row[4]), row[5], row[6]) if row else None

def add_event(task_id: str, event_type: str, message: str) -> None:
    with connect() as db:
        db.execute("INSERT INTO task_events VALUES (?, ?, ?, ?)", (task_id, event_type, message, datetime.now(UTC).isoformat()))

def get_events(task_id: str) -> list[EventRecord]:
    with connect() as db:
        rows = db.execute("SELECT task_id, event_type, message, created_at FROM task_events WHERE task_id = ? ORDER BY rowid", (task_id,)).fetchall()
    return [EventRecord(*row) for row in rows]
