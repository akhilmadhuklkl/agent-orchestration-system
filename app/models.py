from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    description: str = Field(min_length=1)
    require_approval: bool = True

class ApprovalRequest(BaseModel):
    approved: bool

class ToolExecutionRequest(BaseModel):
    agent: str
    arguments: dict[str, Any] = {}

class ToolRun(BaseModel):
    tool: str
    agent: str
    status: str
    arguments: dict[str, Any]
    result: Any | None = None
    error: str | None = None
    created_at: str

class TaskEvent(BaseModel):
    event_type: str
    message: str
    created_at: str

class TaskState(BaseModel):
    task_id: str
    description: str
    require_approval: bool
    status: Literal["planned", "awaiting_approval", "running", "completed", "rejected", "failed"]
    plan: list[str] = []
    result: Any | None = None
    error: str | None = None
