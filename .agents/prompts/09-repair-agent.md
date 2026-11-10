# Step 9: Repair agent

**Prerequisite:** Step 8 done.

```text
Using the portfoliopilot-dev skill, implement Step 9: Repair agent (SKILL.md Section 5.6).

Backend:
- agents/repair_agent.py: input = failing step, trimmed log (first error blocks, max ~4k tokens), ONLY the offending files; output = patches in the same strict JSON format, validated and policy-checked.
- Log trimmer utility (pure function, tested): extracts the first TS/ESLint/Vite error blocks with file:line references.
- Bounded loop in the pipeline: MAX_REPAIR attempts (default 3, configurable). Each attempt records a BuildReport with attempt_no and the repair patches as Changes marked created_by=repair.
- Stop conditions: success, attempts exhausted, repeated identical error (no progress), token budget exceeded. On failure mark the version failed, keep logs, never publish.
- Repair patches are shown to the user in the diff (clearly labelled) before publish.
- Tests: fixable type error repaired within N attempts; unfixable error stops with a clear status; identical-error loop detected; repair cannot touch files outside the allowlist.

Frontend:
- Build progress shows "Repair attempt k/3" with what failed and what the repair changed.
- Failure view: clear message, logs, options (retry, edit instructions, discard).
- Tests for the repair states.

Run all checks, then update .agents/PROGRESS.md.
```

**Acceptance checks**
- A seeded type error is auto-repaired and the final preview builds.
- A seeded unfixable error ends cleanly after the attempt limit with no published version.
