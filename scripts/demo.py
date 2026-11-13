"""Run a small end-to-end local demo without external services."""
from app.main import approve_task, create_task, task_events
from app.models import ApprovalRequest, TaskRequest


def main() -> None:
    task = create_task(TaskRequest(description="Research competitors and summarize the differences"))
    print(f"Created: {task.task_id}")
    print(f"Status: {task.status}")
    if task.status == "awaiting_approval":
        task = approve_task(task.task_id, ApprovalRequest(approved=True))
    print(f"Final status: {task.status}")
    print(f"Result: {task.result}")
    print("Timeline:")
    for event in task_events(task.task_id):
        print(f"  - {event.event_type}: {event.message}")

if __name__ == "__main__":
    main()
