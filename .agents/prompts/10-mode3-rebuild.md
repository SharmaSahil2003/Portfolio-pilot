# Step 10: Mode 3 Rebuild

**Prerequisite:** Step 9 done.

```text
Using the portfoliopilot-dev skill, implement Step 10: Mode 3 Rebuild (SKILL.md Section 5.5).

Backend:
- agents/workspace_agent.py: tool-using agent loop with ONLY these tools: list_files, read_file, search_code, propose_patch, run_check (typecheck/lint/build via the sandbox), finish. No shell, no network tool.
- Phase 1 PLAN: the agent analyzes the repo and the profile diff and returns a human-readable plan (stored on the ChangeSet, status awaiting_plan_approval). No patches before the user approves the plan.
- Phase 2 IMPLEMENT: after plan approval, run the loop with budgets (max steps, max tokens, max wall-clock). On budget exceeded, stop cleanly and return partial patches with a clear status.
- All patches go through policy.py; run_check feeds the Step 7 pipeline and Step 9 repair loop.
- User design preferences and instructions are passed as data; resume/file contents remain untrusted data.
- Endpoints: POST /portfolios/{id}/changesets (mode=rebuild), POST /changesets/{id}/plan/approve, POST /changesets/{id}/plan/reject (with feedback that triggers a re-plan).
- Tests with a scripted FakeLLMClient: tool whitelist enforced (unknown tool rejected), budget enforcement, plan gate cannot be skipped, injection in repo file cannot grant new tools, full path from plan to preview.

Frontend:
- Mode selector: enable Rebuild with a clear "high autonomy" warning and cost estimate.
- Plan review screen: render the plan, approve or reject with feedback.
- Progress view showing agent steps (read/search/patch/check) in a log, with a cancel button.
- Then the standard diff review, build, preview flow.
- Tests for plan approval and cancellation.

Run all checks, then update .agents/PROGRESS.md.
```

**Acceptance checks**
- You cannot reach implementation without approving the plan.
- Budget exhaustion produces a clean, explained partial result.
