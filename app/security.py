from fastapi import Header, HTTPException

from .config import settings


def require_api_key(x_api_key: str | None = Header(default=None), x_workspace_id: str | None = Header(default=None)) -> None:
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    require_workspace(x_workspace_id)

def require_workspace(x_workspace_id: str | None = Header(default=None)) -> None:
    if settings.workspace_id != "default" and x_workspace_id != settings.workspace_id:
        raise HTTPException(status_code=403, detail="Workspace access denied")
