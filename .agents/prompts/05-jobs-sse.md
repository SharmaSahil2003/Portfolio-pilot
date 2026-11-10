# Step 5: Jobs and SSE

**Prerequisite:** Step 4 done.

```text
Using the portfoliopilot-dev skill, implement Step 5: Jobs and SSE (SKILL.md Sections 4 Job entity, 5, 6, 7.2).

Backend:
- Job model + migration (status, progress 0-100, stage, result, error, attempts).
- Real JobQueue implementation behind the existing interface (arq or Celery with Redis) plus a worker service in docker-compose.
- Move resume parsing and changeset generation/apply onto jobs. Jobs must be idempotent, have timeouts, bounded retries with backoff, and support cancellation.
- GET /jobs/{id} and GET /jobs/{id}/events (SSE) streaming stage/progress updates via Redis pub/sub; heartbeat every 15s; auth required; users can only see their own jobs.
- Make endpoints that start work return {job_id}.
- Tests: job lifecycle, retry then success, retry exhausted -> failed, cancellation, SSE stream emits ordered events, cross-user access denied.

Frontend:
- useJob(jobId) hook: SSE subscription with polling fallback, reconnect with backoff, cleanup on unmount.
- JobProgress component with stepper, ARIA live region, error state with retry action.
- Wire resume parsing and changeset apply flows to use it.
- Tests: SSE success, SSE drop -> polling fallback, failure state.

Run all checks, then update .agents/PROGRESS.md.
```

**Acceptance checks**
- Kill the worker mid-job and confirm the job surfaces a clear failure or resumes per design.
- Progress updates appear live in the UI.
