# Agent Orchestration System

An MVP orchestration service built with Python and LangGraph, designed for durable task execution, agent delegation, tool boundaries, and human approval.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs`.

The workflow is intentionally small and inspectable. PostgreSQL and Redis are included in `docker-compose.yml` for the production-shaped local setup; Redis is reserved for the worker queue in the next iteration.

Tasks are persisted through SQLAlchemy. SQLite is the default for a zero-setup portfolio demo; set `DATABASE_URL` to PostgreSQL when running the infrastructure locally.

## Workflow

`intake -> plan -> approval -> execute -> complete`

Tasks requiring approval pause before execution and can be resumed through the approval endpoint.

## Background worker mode

The default `QUEUE_MODE=sync` runs locally without Redis. To use the worker architecture, start Redis with Docker Compose, set `QUEUE_MODE=redis`, then run:

```powershell
python -m app.worker
```

Tools also declare risk levels. High-risk tools require `approved: true` in the execution request; the notification tool is simulated and never sends an external message.

## API examples

```powershell
$task = Invoke-RestMethod -Method Post http://localhost:8000/tasks -ContentType 'application/json' -Body '{"description":"Prepare a launch checklist"}'
Invoke-RestMethod -Method Post "http://localhost:8000/tasks/$($task.task_id)/approval" -ContentType 'application/json' -Body '{"approved":true}'
```
