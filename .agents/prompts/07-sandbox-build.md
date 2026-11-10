# Step 7: Sandbox build pipeline (no LLM yet)

**Prerequisite:** Step 6 done.

```text
Using the portfoliopilot-dev skill, implement Step 7: Sandbox build pipeline (SKILL.md Sections 5.6, 8, 7.1 screens 7-8).

Backend:
- /sandbox: Dockerfile for the build image (non-root, Node LTS, pre-warmed dependency cache for the allowlisted stack: React, TypeScript, Vite, Tailwind, Framer Motion, Lucide) and a runner script.
- workspace/policy.py: static policy check run BEFORE any build. Reject: paths outside src/** and public/**, dependencies outside the allowlist, eval/new Function, dangerouslySetInnerHTML, document.cookie, Node fs/child_process, fetch to non-allowlisted hosts, postinstall scripts. Return structured violations.
- workspace/runner.py using the Docker SDK: materialize workspace from a version + patches, run install -> tsc --noEmit -> eslint -> vitest (if present) -> vite build. Limits: CPU, memory, wall-clock timeout; read-only root FS except workspace/tmp; no host mounts other than the workspace; no environment secrets; network disabled after install (or allowlisted registry mirror only).
- BuildReport model + migration; record every step with ok, log_excerpt (trimmed), duration, attempt_no.
- On success: upload dist/ as a preview bundle, snapshot the workspace, create a PortfolioVersion.
- GET /versions/{id}/preview (short-lived signed URL, served with strict CSP and sandboxed), GET /versions/{id}/build-reports.
- Pipeline runs as a job emitting stage events (reuse Step 5 SSE).
- Tests (hand-written patches only, no LLM): clean build passes; type error fails at tsc; policy violation blocked before build; timeout kills container; container cannot read host files or env secrets (assert this explicitly).

Frontend:
- Build progress screen: stepper (policy, install, typecheck, lint, test, build), expandable log excerpts, failure state.
- Preview page: iframe of the bundle with desktop/tablet/mobile toggles; Publish / Discard actions.
- Tests for stepper and viewport toggles.

Run all checks, then update .agents/PROGRESS.md.
```

**Acceptance checks**
- A deliberately broken patch fails with a readable report and never produces a version.
- A malicious patch (eval, forbidden dependency) is rejected before any container starts.
- Sandbox escape tests pass.
