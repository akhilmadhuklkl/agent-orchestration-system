from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    description: str = Field(min_length=1)
    require_approval: bool = True

class ApprovalRequest(BaseModel):
    approved: bool

class TaskState(BaseModel):
    task_id: str
    description: str
    require_approval: bool
    status: Literal["planned", "awaiting_approval", "running", "completed", "rejected", "failed"]
    plan: list[str] = []
    result: Any | None = None
    error: str | None = None
