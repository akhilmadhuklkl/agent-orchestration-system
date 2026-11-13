"""Run with: python -m app.worker"""
from .database import add_event, get_task, save_task
from .graph import build_graph
from .queue import dequeue
from .reliability import run_with_retries


def process_task(task_id: str) -> None:
    task = get_task(task_id)
    if not task:
        return
    task.status = "running"
    save_task(task)
    add_event(task_id, "worker.started", "Background worker started the task")
    state = run_with_retries(lambda: build_graph().invoke({"task_id": task.id, "description": task.description, "require_approval": False, "plan": task.plan}))
    task.status = state["status"]
    task.result = state.get("result")
    save_task(task)
    add_event(task_id, "worker.completed", "Background worker completed the task")
    add_event(task_id, "task.completed", "Task completed successfully")

def run() -> None:
    print("Worker listening for tasks...")
    while True:
        task_id = dequeue()
        if task_id:
            process_task(task_id)

if __name__ == "__main__":
    run()
