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
    approved: bool = False

class ToolRun(BaseModel):
    tool: str
    agent: str
    status: str
    arguments: dict[str, Any]
    result: Any | None = None
    error: str | None = None
    created_at: str

class MemoryRequest(BaseModel):
    scope: str
    key: str
    value: Any

class MemoryItem(BaseModel):
    scope: str
    key: str
    value: Any
    created_at: str

class UserCreateRequest(BaseModel):
    user_id: str
    workspace_id: str
    role: str = "member"

class UserCreateResponse(BaseModel):
    user_id: str
    workspace_id: str
    role: str
    api_key: str

class UserItem(BaseModel):
    user_id: str
    workspace_id: str
    role: str
    created_at: str

class ApiKeyRevokeRequest(BaseModel):
    api_key: str

class TaskEvent(BaseModel):
    event_type: str
    message: str
    created_at: str

class TaskState(BaseModel):
    task_id: str
    description: str
    require_approval: bool
    status: Literal["planned", "awaiting_approval", "queued", "running", "completed", "rejected", "failed", "cancelled"]
    plan: list[str] = []
    result: Any | None = None
    error: str | None = None
