# Step 6: Versioning

**Prerequisite:** Step 5 done.

```text
Using the portfoliopilot-dev skill, implement Step 6: Versioning (SKILL.md Section 5.7, 1 rule 3).

Backend:
- Finalize PortfolioVersion: workspace_key (S3 snapshot), file_manifest (path -> sha256), parent_version_id, label, created_by, status.
- services/version_service.py: create_version, compare(a, b) (changed files with unified diffs + data diffs), rollback (creates a NEW version pointing at the old snapshot; history is append-only), publish (sets published_version_id), delete (never the published version).
- Content-addressed storage for files so unchanged files are not duplicated between versions.
- Endpoints: GET /portfolios/{id}/versions, GET /versions/{id}, GET /versions/{a}/compare/{b}, POST /versions/{id}/rollback, POST /versions/{id}/publish, DELETE /versions/{id}.
- Importing an existing portfolio: POST /portfolios supports uploading a repo ZIP (reject path traversal, symlinks, oversized archives) and creates version 1 from it.
- Tests: manifest correctness, compare symmetry, rollback creates a new version and leaves history intact, cannot delete published version, zip-slip attack rejected, cross-user access denied.

Frontend:
- Version history page: timeline, labels, created_by badge (user/ai), published marker.
- Compare view for any two versions (file list + diff viewer + data diff).
- Actions with confirmation dialogs: rollback, publish, delete.
- Tests for timeline, compare, and destructive-action dialogs.

Run all checks, then update .agents/PROGRESS.md.
```

**Acceptance checks**
- Upload a repo ZIP, see v1; apply a sync, see v2; roll back and see v3 equal to v1.
- Malicious ZIP is rejected in a test.
