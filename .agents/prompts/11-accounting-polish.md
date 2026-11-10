# Step 11: Token accounting, budgets, polish

**Prerequisite:** Step 10 done.

```text
Using the portfoliopilot-dev skill, implement Step 11: Token accounting, budgets and polish (SKILL.md Sections 5.8, 7.3, 8, 10).

Backend:
- llm/accounting.py: record prompt/completion tokens, model, latency and estimated cost for EVERY LLM call, attached to Job and ChangeSet.
- Per-user daily token/cost budget with a clear error (HTTP 429 with code BUDGET_EXCEEDED and reset time); admin-configurable limits.
- Expose usage: GET /usage (per day, per mode) and token_usage on changeset responses.
- Security review pass: confirm every query is scoped by user_id (add a test that enumerates routes and checks authorization), rate limits on LLM-triggering endpoints, CORS, logging redaction, signed URL expiry.
- Observability: request ids, job ids in logs, basic metrics endpoint.
- Playwright e2e: register -> upload resume -> review profile -> sync -> evolve -> preview -> publish -> rollback (LLM faked).

Frontend:
- Usage page and per-changeset token summary; budget-exceeded UX.
- Accessibility pass: keyboard navigation through the diff list and dialogs, focus management, ARIA live regions, WCAG AA contrast; run axe in tests.
- Responsive check from 360px; skeletons and empty states audit; error boundary audit.

Run all checks including e2e, then update .agents/PROGRESS.md and write docs/ARCHITECTURE.md summarizing final design and known limitations.
```

**Acceptance checks**
- Exceeding the budget blocks new LLM jobs with a helpful message.
- e2e suite passes; axe reports no critical issues on main screens.
