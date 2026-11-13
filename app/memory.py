import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from .config import settings


@dataclass
class MemoryRecord:
    scope: str
    key: str
    value: object
    created_at: str

def _path():
    return settings.database_url.removeprefix("sqlite:///") if settings.database_url.startswith("sqlite:///") else "orchestrator.db"

def _connect():
    return sqlite3.connect(_path())

def init_memory() -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    with _connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS memories (scope TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(scope, key))")

def save_memory(scope: str, key: str, value: object) -> MemoryRecord:
    record = MemoryRecord(scope, key, value, datetime.now(UTC).isoformat())
    with _connect() as db:
        db.execute("INSERT OR REPLACE INTO memories VALUES (?, ?, ?, ?)", (scope, key, json.dumps(value), record.created_at))
    return record

def get_memories(scope: str) -> list[MemoryRecord]:
    with _connect() as db:
        rows = db.execute("SELECT scope, key, value, created_at FROM memories WHERE scope = ? ORDER BY rowid", (scope,)).fetchall()
    return [MemoryRecord(row[0], row[1], json.loads(row[2]), row[3]) for row in rows]
