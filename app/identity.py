from fastapi import Header, HTTPException

from .config import settings


def current_identity(x_user_id: str | None = Header(default=None), x_user_role: str | None = Header(default=None)) -> dict[str, str]:
    return {"user_id": x_user_id or settings.user_id, "role": x_user_role or settings.user_role, "workspace_id": settings.workspace_id}

def require_admin(identity: dict[str, str] | None = None, x_user_role: str | None = Header(default=None)) -> None:
    role = x_user_role or settings.user_role
    if role != "admin":
        raise HTTPException(status_code=403, detail="Administrator role required")
