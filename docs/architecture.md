# Architecture

## Runtime flow

```text
Dashboard / API client
        |
        v
     FastAPI
        |
        +--> LangGraph planner
        |       |
        |       +--> Agent registry
        |       +--> Tool registry
        |       +--> Reviewer
        |
        +--> PostgreSQL task/event/memory history
        |
        +--> Redis queue --> Background worker
```

## Main components

- `app/main.py`: HTTP API and dashboard routes.
- `app/graph.py`: LangGraph orchestration workflow.
- `app/agents.py`: capability-based agent registry.
- `app/tools.py`: permissioned tool registry.
- `app/database.py`: SQLite/PostgreSQL persistence adapter.
- `app/worker.py`: Redis-backed background worker.
- `app/llm.py`: deterministic/OpenAI model adapter.
- `app/observability.py`: request IDs, structured logs, and metrics.
- `app/security.py`: API-key and workspace checks.

## Workflow states

```text
created -> planned -> awaiting_approval -> queued -> running
                                               |
                                   reviewing -> completed/failed
```

Every important transition is written to the task event history.
