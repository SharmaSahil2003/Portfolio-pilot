# Step 1: Foundation

**Prerequisite:** none.

```text
Using the portfoliopilot-dev skill (read SKILL.md and PROGRESS.md first), implement Step 1: Foundation.

Backend (/backend):
- FastAPI app skeleton following the layout in SKILL.md Section 3 (core, db, models, schemas, api/v1, services, agents, llm, workspace, storage, jobs, utils).
- Config via pydantic-settings, reading from environment; provide .env.example.
- Structured JSON logging with request ids and PII redaction.
- Global error handling returning {error: {code, message, details?}}.
- Async SQLAlchemy session, Alembic configured, first migration creating User.
- Auth: register, login, refresh; argon2 password hashing; JWT access + refresh tokens; get_current_user dependency.
- Rate limiting on auth endpoints.
- GET /health (checks DB and Redis).
- pyproject.toml with ruff, mypy --strict, pytest, pytest-asyncio, httpx, testcontainers.
- Tests: auth success/failure, token refresh, unauthorized access, health check.

Infra:
- docker-compose.yml with Postgres (with pgvector), Redis, MinIO, backend, frontend.
- backend/Dockerfile (non-root user), frontend Dockerfile.
- GitHub Actions CI: backend (ruff, mypy, pytest) and frontend (typecheck, lint, test).
- Makefile or scripts for common commands.

Frontend (/frontend):
- Vite + React 18 + TypeScript strict, Tailwind, shadcn/ui, React Router, TanStack Query, Zustand, Zod, Vitest, RTL, MSW.
- lib/api.ts fetch wrapper per SKILL.md 7.2 (auth header, refresh, typed errors, Zod validation).
- Auth feature: login and register pages, protected route wrapper, logout.
- App layout shell, error boundary, loading and empty-state components.
- Script to generate API types from backend OpenAPI (openapi-typescript).
- Tests for the login form and protected route.

Follow SKILL.md Section 11 for how to respond. Run all checks, then update .agents/PROGRESS.md.
```

**Acceptance checks**
- `docker compose up -d` brings everything up; `GET /health` returns OK.
- You can register, log in, and reach a protected page in the browser.
- Backend and frontend check commands all pass.
