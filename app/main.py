from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from .agents import list_agents
from .database import TaskRecord, init_db, save_task
from .database import get_task as load_task
from .graph import build_graph
from .models import ApprovalRequest, TaskRequest, TaskState


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

@app.post("/tasks", response_model=TaskState, status_code=201)
def create_task(request: TaskRequest):
    task_id = str(uuid4())
    state = graph.invoke({"task_id": task_id, **request.model_dump()})
    task = TaskRecord(id=task_id, description=request.description, require_approval=request.require_approval, status=state["status"], plan=state.get("plan", []), result=state.get("result"))
    save_task(task)
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
        return task_state(task)
    state = graph.invoke({"task_id": task.id, "description": task.description, "require_approval": False, "plan": task.plan})
    task.status = state["status"]
    task.result = state.get("result")
    save_task(task)
    return task_state(task)

def task_state(task: TaskRecord) -> TaskState:
    return TaskState(task_id=task.id, description=task.description, require_approval=task.require_approval, status=task.status, plan=task.plan, result=task.result, error=task.error)
