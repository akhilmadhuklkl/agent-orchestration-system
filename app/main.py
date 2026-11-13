from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse

from .agents import list_agents
from .config import settings
from .database import (
    TaskRecord,
    add_event,
    add_tool_run,
    get_events,
    get_tasks,
    get_tool_runs,
    init_db,
    save_task,
)
from .database import get_task as load_task
from .graph import build_graph
from .models import (
    ApprovalRequest,
    TaskEvent,
    TaskRequest,
    TaskState,
    ToolExecutionRequest,
    ToolRun,
)
from .observability import (
    RequestObservabilityMiddleware,
    metrics,
    record_task,
    record_tool,
)
from .queue import enqueue
from .security import require_api_key
from .tools import execute_tool, list_tools


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Agent Orchestration System", version="0.1.0", lifespan=lifespan)
app.add_middleware(RequestObservabilityMiddleware)
graph = build_graph()
init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics_endpoint():
    return dict(metrics)

@app.get("/")
def dashboard():
    return FileResponse("app/static/index.html")

@app.get("/agents", dependencies=[Depends(require_api_key)])
def agents():
    return [{"name": agent.name, "role": agent.role, "capabilities": agent.capabilities} for agent in list_agents()]

@app.get("/tools", dependencies=[Depends(require_api_key)])
def tools():
    return [{"name": tool.name, "description": tool.description, "allowed_agents": tool.allowed_agents, "risk": tool.risk} for tool in list_tools()]

@app.post("/tools/{tool_name}/execute", dependencies=[Depends(require_api_key)])
def run_tool(tool_name: str, request: ToolExecutionRequest):
    try:
        tool = next((item for item in list_tools() if item.name == tool_name), None)
        if tool and tool.risk == "high" and not request.approved:
            add_tool_run(tool_name, request.agent, "approval_required", request.arguments, error="High-risk tool requires human approval")
            record_tool("approval_required")
            raise HTTPException(409, "Human approval is required for this high-risk tool")
        result = execute_tool(tool_name, request.agent, request.arguments)
        add_tool_run(tool_name, request.agent, "completed", request.arguments, result=result)
        record_tool("completed")
        return {"tool": tool_name, "agent": request.agent, "result": result}
    except KeyError as error:
        add_tool_run(tool_name, request.agent, "failed", request.arguments, error=str(error))
        record_tool("failed")
        raise HTTPException(404, str(error)) from error
    except PermissionError as error:
        add_tool_run(tool_name, request.agent, "denied", request.arguments, error=str(error))
        record_tool("denied")
        raise HTTPException(403, str(error)) from error
    except ValueError as error:
        add_tool_run(tool_name, request.agent, "failed", request.arguments, error=str(error))
        record_tool("failed")
        raise HTTPException(422, str(error)) from error

@app.get("/tool-runs", response_model=list[ToolRun], dependencies=[Depends(require_api_key)])
def tool_runs():
    return [ToolRun(**run.__dict__) for run in get_tool_runs()]

@app.post("/tasks", response_model=TaskState, status_code=201, dependencies=[Depends(require_api_key)])
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
    record_task(task.status)
    return task_state(task)

@app.get("/tasks", response_model=list[TaskState], dependencies=[Depends(require_api_key)])
def tasks(status: str | None = None):
    items = [task_state(task) for task in get_tasks()]
    return [task for task in items if status is None or task.status == status]

@app.post("/tasks/{task_id}/cancel", response_model=TaskState, dependencies=[Depends(require_api_key)])
def cancel_task(task_id: str):
    task = load_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.status in {"completed", "rejected", "cancelled"}:
        raise HTTPException(409, "Task cannot be cancelled in its current state")
    task.status = "cancelled"
    save_task(task)
    add_event(task_id, "task.cancelled", "Task was cancelled by a user")
    return task_state(task)

@app.post("/tasks/{task_id}/retry", response_model=TaskState, dependencies=[Depends(require_api_key)])
def retry_task(task_id: str):
    task = load_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.status not in {"failed", "rejected", "cancelled"}:
        raise HTTPException(409, "Only failed, rejected, or cancelled tasks can be retried")
    task.status = "awaiting_approval" if task.require_approval else "running"
    task.result = None
    save_task(task)
    add_event(task_id, "task.retried", "Task was sent back through the workflow")
    return task_state(task)

@app.get("/tasks/{task_id}", response_model=TaskState, dependencies=[Depends(require_api_key)])
def get_task(task_id: str):
    task = load_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task_state(task)

@app.post("/tasks/{task_id}/approval", response_model=TaskState, dependencies=[Depends(require_api_key)])
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

@app.get("/tasks/{task_id}/events", response_model=list[TaskEvent], dependencies=[Depends(require_api_key)])
def task_events(task_id: str):
    if not load_task(task_id):
        raise HTTPException(404, "Task not found")
    return [TaskEvent(event_type=event.event_type, message=event.message, created_at=event.created_at) for event in get_events(task_id)]

def task_state(task: TaskRecord) -> TaskState:
    return TaskState(task_id=task.id, description=task.description, require_approval=task.require_approval, status=task.status, plan=task.plan, result=task.result, error=task.error)
