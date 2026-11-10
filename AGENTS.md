# PortfolioPilot: Agent Instructions

PortfolioPilot is an agentic AI platform that turns an updated resume into an evolving developer portfolio. Backend: FastAPI + PostgreSQL. Frontend: React + TypeScript.

## Before you do anything
1. Read `.agents/skills/portfoliopilot-dev/SKILL.md` fully. It is the source of truth for architecture, domain model, API, and quality rules.
2. Read `.agents/PROGRESS.md` to see which step is current.
3. Work on ONE step at a time, using the matching file in `.agents/prompts/`.

## Working rules
- Follow the step order in SKILL.md Section 9. Do not start a step until the previous one passes its acceptance checks.
- Backend first (models, migration, schemas, service, router, tests), then frontend.
- Output complete files, no placeholder TODOs for core logic.
- Run the checks listed in the step file before declaring done. Never claim tests pass without running them.
- When finished, update `.agents/PROGRESS.md` (status, date, notes, known limitations).
- If a design decision changes, update SKILL.md in the same change and record it in the Decisions log in PROGRESS.md.

## Commands (update as the project grows)
- Backend: `cd backend && ruff check . && mypy --strict app && pytest`
- Frontend: `cd frontend && npm run typecheck && npm run lint && npm test`
- Stack: `docker compose up -d`
