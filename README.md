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

Set `DATABASE_URL=postgresql://orchestration:orchestration@localhost:5432/orchestration` to use PostgreSQL. The application creates its tables on startup; SQLite remains the default for a zero-setup demo.

For the full local stack, run `docker compose up --build`. The API is then available at `http://localhost:8002`, with PostgreSQL, Redis, and a background worker running as separate services.

Observability endpoints include `/health` and `/metrics`. API responses also include an `X-Request-ID` header, and structured request logs contain method, path, status, request ID, and duration.

Workers use bounded exponential retries for transient failures. Reliability and routing evaluation cases are covered in `tests/test_reliability.py` and `tests/test_evaluation.py`.

LLM planning is configurable with `MODEL_MODE=deterministic` (default) or `MODEL_MODE=openai` plus `OPENAI_API_KEY`. Model failures automatically fall back to deterministic planning.

Agents can select registered tools for supported task patterns. Tool calls pass through the same allow-list, risk, approval, and audit controls as direct API calls.

Memory is scoped by a caller-provided namespace through `POST /memory` and `GET /memory/{scope}`. This prevents unrelated task or workspace context from being mixed accidentally.

Set `WORKSPACE_ID` to enable workspace enforcement. Protected memory routes then require a matching `X-Workspace-ID` header; `default` keeps the local demo open.

Identity metadata is available at `/identity`. Configure `USER_ID` and `USER_ROLE`; administrator-only routes use the role dependency and return `403` for non-admin users.

Administrators can create database-backed users and one-time-visible API keys through `POST /admin/users`. Keys are stored as SHA-256 hashes and can be revoked at the repository layer.

Security hardening includes configurable CORS, security headers, request rate limiting, and `POST /admin/api-keys/revoke` for administrator-controlled key revocation.

Tools also declare risk levels. High-risk tools require `approved: true` in the execution request; the notification tool is simulated and never sends an external message.

## API examples

```powershell
$task = Invoke-RestMethod -Method Post http://localhost:8000/tasks -ContentType 'application/json' -Body '{"description":"Prepare a launch checklist"}'
Invoke-RestMethod -Method Post "http://localhost:8000/tasks/$($task.task_id)/approval" -ContentType 'application/json' -Body '{"approved":true}'
```
