from fastapi import HTTPException

from app.database import api_key_user, revoke_api_key, save_api_key
from app.identity import require_admin
from app.main import (
    approve_task,
    cancel_task,
    create_task,
    dashboard,
    get_task,
    read_memory,
    retry_task,
    run_tool,
    task_events,
    tasks,
    tool_runs,
    users,
    write_memory,
)
from app.models import ApprovalRequest, TaskRequest, ToolExecutionRequest
from app.observability import metrics
from app.main import model_status
from app.security import require_api_key, require_workspace
from app.tools import execute_tool


def test_task_pauses_for_approval():
    task = create_task(TaskRequest(description="Draft a project plan"))
    assert task.status == "awaiting_approval"
    approved = approve_task(task.task_id, ApprovalRequest(approved=True))
    assert approved.status == "completed"
    assert get_task(task.task_id).result.startswith("Writing Agent completed")
    event_types = [event.event_type for event in task_events(task.task_id)]
    assert event_types == ["task.created", "task.planned", "agent.assigned", "approval.requested", "approval.granted", "worker.completed", "task.completed"]

def test_task_can_run_without_approval():
    task = create_task(TaskRequest(description="Run a health check", require_approval=False))
    assert task.status == "completed"

def test_task_can_be_rejected():
    task = create_task(TaskRequest(description="Delete an account"))
    rejected = approve_task(task.task_id, ApprovalRequest(approved=False))
    assert rejected.status == "rejected"

def test_planner_selects_specialized_agent():
    task = create_task(TaskRequest(description="Research competitors"))
    assert "Research Agent" in task.plan[1]

def test_worker_processes_queued_task():
    task = create_task(TaskRequest(description="Run a queued health check"))
    approved = approve_task(task.task_id, ApprovalRequest(approved=True))
    assert approved.status == "completed"

def test_tool_permissions_are_enforced():
    assert execute_tool("word_count", "writer", {"text": "one two three"}) == {"words": 3}
    try:
        execute_tool("word_count", "researcher", {"text": "one"})
    except PermissionError:
        pass
    else:
        raise AssertionError("unauthorized tool call was accepted")

def test_tool_run_history_records_success():
    request = type("Request", (), {"agent": "writer", "arguments": {"text": "one two"}})()
    response = run_tool("word_count", request)
    assert response["result"] == {"words": 2}
    assert tool_runs()[0].status == "completed"

def test_high_risk_tool_requires_approval():
    try:
        run_tool("send_notification", ToolExecutionRequest(agent="executor", arguments={"recipient": "demo", "message": "hello"}))
    except HTTPException as error:
        assert error.status_code == 409
    else:
        raise AssertionError("high-risk tool ran without approval")
    response = run_tool("send_notification", ToolExecutionRequest(agent="executor", approved=True, arguments={"recipient": "demo", "message": "hello"}))
    assert response["result"]["status"] == "simulated"

def test_dashboard_is_available():
    assert dashboard().path.endswith("app/static/index.html")

def test_api_key_policy_rejects_invalid_key(monkeypatch):
    monkeypatch.setattr("app.security.settings.api_key", "secret")
    try:
        require_api_key("wrong")
    except HTTPException as error:
        assert error.status_code == 401
    else:
        raise AssertionError("invalid API key was accepted")

def test_workspace_policy_rejects_wrong_workspace(monkeypatch):
    monkeypatch.setattr("app.security.settings.workspace_id", "team-a")
    try:
        require_workspace("team-b")
    except HTTPException as error:
        assert error.status_code == 403
    else:
        raise AssertionError("wrong workspace was accepted")

def test_role_policy_rejects_non_admin(monkeypatch):
    monkeypatch.setattr("app.config.settings.user_role", "member")
    try:
        require_admin()
    except HTTPException as error:
        assert error.status_code == 403
    else:
        raise AssertionError("member role was accepted for admin operation")

def test_database_api_key_can_be_revoked():
    raw_key = "test-key"
    save_api_key(raw_key, "local-user")
    assert api_key_user(raw_key) == "local-user"
    revoke_api_key(raw_key)
    assert api_key_user(raw_key) is None

def test_security_headers_middleware_is_available():
    from app.security_middleware import RateLimitMiddleware, SecurityHeadersMiddleware
    assert RateLimitMiddleware is not None
    assert SecurityHeadersMiddleware is not None

def test_user_list_endpoint_returns_users():
    from app.database import save_user
    save_user("dashboard-user", "default", "member")
    assert any(user.user_id == "dashboard-user" for user in users())

def test_task_list_includes_created_tasks():
    task = create_task(TaskRequest(description="List this task"))
    assert any(item.task_id == task.task_id for item in tasks())

def test_task_can_be_cancelled_and_retried():
    task = create_task(TaskRequest(description="Cancel me"))
    cancelled = cancel_task(task.task_id)
    assert cancelled.status == "cancelled"
    retried = retry_task(task.task_id)
    assert retried.status == "awaiting_approval"

def test_sqlite_repository_is_default():
    from app.config import settings
    assert settings.database_url.startswith("sqlite:///")

def test_observability_records_task_and_tool_metrics():
    task = create_task(TaskRequest(description="Measure this task", require_approval=False))
    run_tool("word_count", ToolExecutionRequest(agent="writer", arguments={"text": "one two"}))
    assert metrics["tasks_total"] >= 1
    assert metrics["tool_runs_status_completed"] >= 1
    assert task.status == "completed"

def test_model_status_reports_local_fallback():
    status = model_status()
    assert status["mode"] == "deterministic"
    assert status["available"] is True

def test_scoped_memory_is_persisted():
    request = type("Request", (), {"scope": "demo", "key": "preference", "value": {"style": "concise"}})()
    write_memory(request)
    memories = read_memory("demo")
    assert memories[0].value == {"style": "concise"}
