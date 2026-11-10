# Step 4: Mode 1 Sync (first full vertical slice)

**Prerequisite:** Steps 1-3 done.

```text
Using the portfoliopilot-dev skill, implement Step 4: Mode 1 Sync (SKILL.md Sections 5.3, 6, 7.1 screens 2, 4-6).

Backend:
- Models + migrations: Portfolio, PortfolioVersion (v1 can have no workspace snapshot yet), ChangeSet, Change.
- POST /portfolios (name, slug, default mode), GET /portfolios, GET /portfolios/{id}.
- PUT /portfolios/{id}/mapping: stores the field mapping from ProfileSchema to the portfolio's own data schema (JSONB).
- services/sync_service.py: build a ChangeSet of kind=data changes derived ONLY from diff_profiles. ZERO LLM calls. Apply mapping through PortfolioDataAdapter.
- POST /portfolios/{id}/changesets (mode=sync), GET /changesets/{id}, PATCH /changesets/{id}/changes/{cid} (approve/reject), POST /changesets/{id}/apply (applies approved changes only, writes data, creates a new PortfolioVersion with parent link).
- Public endpoint GET /public/{slug}/data/{section}: no auth, serves the published data, ETag + Cache-Control, rate limited, returns 404 for unpublished.
- Idempotency-Key header on POST /changesets and /apply.
- Tests: partial approval applies only approved changes; apply is idempotent; rejected changes never reach data; public endpoint never leaks unpublished or other users' data; verify no LLM client is invoked in the sync path.

Frontend:
- Dashboard with portfolio list and "Upload new resume" CTA; create-portfolio form including mapping editor.
- Mode selector screen (three cards; Sync recommended and enabled; Evolve/Rebuild shown as "coming soon" for now).
- Change review screen for data changes: grouped list, +/~/- rows, per-change approve/reject with optimistic updates, sticky footer "Approve selected (N) -> Apply".
- Result screen showing the new version number.
- Tests for the change-review screen (approve, reject, partial apply, error rollback).

Run all checks, then update .agents/PROGRESS.md.
```

**Acceptance checks**
- Upload a new resume, review the data diff, approve some changes, and see the public endpoint return the updated data.
- A test proves the sync path makes zero LLM calls.
