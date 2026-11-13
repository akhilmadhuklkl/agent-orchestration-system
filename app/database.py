"""Small persistence adapter for the local portfolio demo."""
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from .config import settings

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


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

@dataclass
class ToolRunRecord:
    tool: str
    agent: str
    status: str
    arguments: dict
    result: object | None
    error: str | None
    created_at: str

@dataclass
class MemoryRecord:
    scope: str
    key: str
    value: object
    created_at: str

@dataclass
class UserRecord:
    user_id: str
    workspace_id: str
    role: str
    created_at: str

def _path() -> str:
    return settings.database_url.removeprefix("sqlite:///") if settings.database_url.startswith("sqlite:///") else "orchestrator.db"

def connect():
    if settings.database_url.startswith(("postgresql://", "postgres://")):
        if psycopg is None:
            raise RuntimeError("psycopg is required for PostgreSQL DATABASE_URL")
        return _PostgresConnection(psycopg.connect(settings.database_url))
    return sqlite3.connect(_path())

class _PostgresConnection:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, *args):
        return self.connection.__exit__(*args)

    def execute(self, query, params=()):
        return self.connection.execute(query.replace("?", "%s").replace("rowid", "created_at"), params)

def init_db() -> None:
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, description TEXT NOT NULL, require_approval INTEGER NOT NULL, status TEXT NOT NULL, plan TEXT NOT NULL, result TEXT, error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS task_events (task_id TEXT NOT NULL, event_type TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS tool_runs (tool TEXT NOT NULL, agent TEXT NOT NULL, status TEXT NOT NULL, arguments TEXT NOT NULL, result TEXT, error TEXT, created_at TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS memories (scope TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(scope, key))")
        db.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, role TEXT NOT NULL, created_at TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS api_keys (key_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)")

def save_task(task: TaskRecord) -> None:
    now = datetime.now(UTC).isoformat()
    with connect() as db:
        if settings.database_url.startswith(("postgresql://", "postgres://")):
            db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET description=EXCLUDED.description, require_approval=EXCLUDED.require_approval, status=EXCLUDED.status, plan=EXCLUDED.plan, result=EXCLUDED.result, error=EXCLUDED.error, updated_at=EXCLUDED.updated_at", (task.id, task.description, int(task.require_approval), task.status, json.dumps(task.plan), task.result, task.error, now, now))
        else:
            db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (task.id, task.description, int(task.require_approval), task.status, json.dumps(task.plan), task.result, task.error, now, now))

def get_task(task_id: str) -> TaskRecord | None:
    with connect() as db:
        row = db.execute("SELECT id, description, require_approval, status, plan, result, error FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return TaskRecord(row[0], row[1], bool(row[2]), row[3], json.loads(row[4]), row[5], row[6]) if row else None

def get_tasks() -> list[TaskRecord]:
    with connect() as db:
        rows = db.execute("SELECT id, description, require_approval, status, plan, result, error FROM tasks ORDER BY rowid DESC").fetchall()
    return [TaskRecord(row[0], row[1], bool(row[2]), row[3], json.loads(row[4]), row[5], row[6]) for row in rows]

def add_event(task_id: str, event_type: str, message: str) -> None:
    with connect() as db:
        db.execute("INSERT INTO task_events VALUES (?, ?, ?, ?)", (task_id, event_type, message, datetime.now(UTC).isoformat()))

def get_events(task_id: str) -> list[EventRecord]:
    with connect() as db:
        rows = db.execute("SELECT task_id, event_type, message, created_at FROM task_events WHERE task_id = ? ORDER BY rowid", (task_id,)).fetchall()
    return [EventRecord(*row) for row in rows]

def add_tool_run(tool: str, agent: str, status: str, arguments: dict, result: object | None = None, error: str | None = None) -> None:
    with connect() as db:
        db.execute("INSERT INTO tool_runs VALUES (?, ?, ?, ?, ?, ?, ?)", (tool, agent, status, json.dumps(arguments), json.dumps(result), error, datetime.now(UTC).isoformat()))

def get_tool_runs() -> list[ToolRunRecord]:
    with connect() as db:
        rows = db.execute("SELECT tool, agent, status, arguments, result, error, created_at FROM tool_runs ORDER BY rowid DESC").fetchall()
    return [ToolRunRecord(row[0], row[1], row[2], json.loads(row[3]), json.loads(row[4]) if row[4] else None, row[5], row[6]) for row in rows]

def save_memory(scope: str, key: str, value: object) -> MemoryRecord:
    now = datetime.now(UTC).isoformat()
    with connect() as db:
        if settings.database_url.startswith(("postgresql://", "postgres://")):
            db.execute("INSERT INTO memories VALUES (?, ?, ?, ?) ON CONFLICT (scope, key) DO UPDATE SET value=EXCLUDED.value, created_at=EXCLUDED.created_at", (scope, key, json.dumps(value), now))
        else:
            db.execute("INSERT OR REPLACE INTO memories VALUES (?, ?, ?, ?)", (scope, key, json.dumps(value), now))
    return MemoryRecord(scope, key, value, now)

def get_memories(scope: str) -> list[MemoryRecord]:
    with connect() as db:
        rows = db.execute("SELECT scope, key, value, created_at FROM memories WHERE scope = ? ORDER BY created_at", (scope,)).fetchall()
    return [MemoryRecord(row[0], row[1], json.loads(row[2]), row[3]) for row in rows]

def save_user(user_id: str, workspace_id: str, role: str) -> UserRecord:
    now = datetime.now(UTC).isoformat()
    with connect() as db:
        query = "INSERT INTO users VALUES (?, ?, ?, ?) ON CONFLICT (user_id) DO UPDATE SET workspace_id=EXCLUDED.workspace_id, role=EXCLUDED.role" if settings.database_url.startswith(("postgresql://", "postgres://")) else "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)"
        db.execute(query, (user_id, workspace_id, role, now))
    return UserRecord(user_id, workspace_id, role, now)

def save_api_key(raw_key: str, user_id: str) -> None:
    digest = hashlib.sha256(raw_key.encode()).hexdigest()
    with connect() as db:
        db.execute("INSERT INTO api_keys VALUES (?, ?, 0, ?)", (digest, user_id, datetime.now(UTC).isoformat()))

def api_key_user(raw_key: str) -> str | None:
    digest = hashlib.sha256(raw_key.encode()).hexdigest()
    with connect() as db:
        row = db.execute("SELECT user_id FROM api_keys WHERE key_hash = ? AND revoked = 0", (digest,)).fetchone()
    return row[0] if row else None

def revoke_api_key(raw_key: str) -> None:
    digest = hashlib.sha256(raw_key.encode()).hexdigest()
    with connect() as db:
        db.execute("UPDATE api_keys SET revoked = 1 WHERE key_hash = ?", (digest,))
