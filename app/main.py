from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from .agents import list_agents
from .config import settings
from .database import TaskRecord, add_event, get_events, init_db, save_task
from .database import get_task as load_task
from .graph import build_graph
from .models import (
    ApprovalRequest,
    TaskEvent,
    TaskRequest,
    TaskState,
    ToolExecutionRequest,
)
from .queue import enqueue
from .tools import execute_tool, list_tools


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Agent Orchestration System", version="0.1.0", lifespan=lifespan)
graph = build_graph()
init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/agents")
def agents():
    return [{"name": agent.name, "role": agent.role, "capabilities": agent.capabilities} for agent in list_agents()]

@app.get("/tools")
def tools():
    return [{"name": tool.name, "description": tool.description, "allowed_agents": tool.allowed_agents} for tool in list_tools()]

@app.post("/tools/{tool_name}/execute")
def run_tool(tool_name: str, request: ToolExecutionRequest):
    try:
        return {"tool": tool_name, "agent": request.agent, "result": execute_tool(tool_name, request.agent, request.arguments)}
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error

@app.post("/tasks", response_model=TaskState, status_code=201)
def create_task(request: TaskRequest):
    task_id = str(uuid4())
    state = graph.invoke({"task_id": task_id, **request.model_dump()})
    task = TaskRecord(id=task_id, description=request.description, require_approval=request.require_approval, status=state["status"], plan=state.get("plan", []), result=state.get("result"))
    save_task(task)
    add_event(task_id, "task.created", "Task was created")
    add_event(task_id, "task.planned", "A plan was generated")
    add_event(task_id, "agent.assigned", f"Delegated to the {state.get('agent_role', 'General Execution Agent')}")
    add_event(task_id, "approval.requested" if request.require_approval else "task.queued", "Waiting for human approval" if request.require_approval else "Ready for execution")
    if task.status == "completed":
        add_event(task_id, "task.completed", "Task completed successfully")
    return task_state(task)

@app.get("/tasks/{task_id}", response_model=TaskState)
def get_task(task_id: str):
    task = load_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task_state(task)

@app.post("/tasks/{task_id}/approval", response_model=TaskState)
def approve_task(task_id: str, request: ApprovalRequest):
    task = load_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.status != "awaiting_approval":
        raise HTTPException(409, "Task is not awaiting approval")
    if not request.approved:
        task.status = "rejected"
        save_task(task)
        add_event(task_id, "approval.rejected", "Human approval was rejected")
        return task_state(task)
    add_event(task_id, "approval.granted", "Human approval was granted")
    if settings.queue_mode == "redis":
        task.status = "queued"
        save_task(task)
        enqueue(task_id)
        add_event(task_id, "task.queued", "Task was placed on the Redis worker queue")
        return task_state(task)
    state = graph.invoke({"task_id": task.id, "description": task.description, "require_approval": False, "plan": task.plan})
    task.status = state["status"]
    task.result = state.get("result")
    save_task(task)
    add_event(task_id, "worker.completed", "Assigned agent completed the task")
    add_event(task_id, "task.completed", "Task completed successfully")
    return task_state(task)

@app.get("/tasks/{task_id}/events", response_model=list[TaskEvent])
def task_events(task_id: str):
    if not load_task(task_id):
        raise HTTPException(404, "Task not found")
    return [TaskEvent(event_type=event.event_type, message=event.message, created_at=event.created_at) for event in get_events(task_id)]

def task_state(task: TaskRecord) -> TaskState:
    return TaskState(task_id=task.id, description=task.description, require_approval=task.require_approval, status=task.status, plan=task.plan, result=task.result, error=task.error)
