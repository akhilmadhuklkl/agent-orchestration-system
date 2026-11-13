# Portfolio Readiness Checklist

## Completed

- [x] LangGraph planning, approval, execution, and review workflow
- [x] Capability-based agents and risk-aware tools
- [x] Human approval, cancellation, rejection, and retry controls
- [x] Durable task, event, memory, and tool-run persistence
- [x] SQLite local mode with PostgreSQL support
- [x] Redis worker mode with retry handling
- [x] Local control-room dashboard
- [x] Identity, roles, workspaces, API keys, security headers, and rate limiting
- [x] Deterministic default mode with optional Ollama/OpenAI adapters
- [x] Docker Compose stack for API, worker, PostgreSQL, and Redis
- [x] GitHub Actions lint, unit test, Docker health, and end-to-end workflow checks
- [x] Portfolio README, architecture guide, demo script, and status badges

## Recommended next improvements

### Priority 1 — Product polish

- Add dashboard pagination and search for large task histories.
- Add a dedicated task detail view with plan, result, events, and tool runs together.
- Add confirmation dialogs for cancellation and rejection actions.
- Add a small set of dashboard screenshots to the README.

### Priority 2 — Reliability and operations

- Add structured JSON logging with configurable log levels.
- Add Redis queue depth and worker heartbeat metrics.
- Add database migration tooling instead of startup table creation.
- Add integration coverage for PostgreSQL and Redis failure/recovery paths.

### Priority 3 — Extensibility

- Add a plugin registration interface for custom agents and tools.
- Add configurable per-tool approval policies and audit exports.
- Add streaming task progress updates through Server-Sent Events or WebSockets.
- Add a local Ollama setup guide and a model-backed smoke test when Ollama is installed.

## Explicitly out of scope for now

- Paid model subscriptions.
- Hosted deployment and production infrastructure.
- External notification delivery.
- Multi-tenant production isolation and compliance certification.
