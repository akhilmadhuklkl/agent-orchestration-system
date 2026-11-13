from fastapi import HTTPException

from app.main import (
    approve_task,
    cancel_task,
    create_task,
    dashboard,
    get_task,
    retry_task,
    run_tool,
    task_events,
    tasks,
    tool_runs,
)
from app.models import ApprovalRequest, TaskRequest, ToolExecutionRequest
from app.security import require_api_key
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
