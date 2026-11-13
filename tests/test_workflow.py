from app.main import approve_task, create_task, get_task, task_events
from app.models import ApprovalRequest, TaskRequest


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
