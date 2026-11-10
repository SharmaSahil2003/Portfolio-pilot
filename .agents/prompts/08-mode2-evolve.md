# Step 8: Mode 2 Evolve

**Prerequisite:** Step 7 done.

```text
Using the portfoliopilot-dev skill, implement Step 8: Mode 2 Evolve (SKILL.md Sections 5.4, 1 rules 2, 5, 6, and Section 12 agent prompt scaffold).

Backend:
- Embedding model + migration (pgvector). Index the portfolio's files and design tokens per version (chunking by component/function).
- Section-to-file mapping (configurable per portfolio, with sensible default and auto-detection hints).
- agents/page_agent.py: for ONLY the affected sections/files (from affected_sections), build context = profile diff + full new profile for those sections + the target files + top-k retrieved snippets (components, tokens, conventions) + allowed libs + design prefs. Use the agent prompt scaffold from SKILL.md Section 12. Return strict JSON patches {path, operation, new_content | unified_diff, rationale}; validate with Pydantic.
- Reject patches that touch unaffected files unless justified and approved; run every patch through workspace/policy.py.
- Convert patches to Change(kind=file) with generated unified diffs; wire into the ChangeSet flow so approved file changes go through the Step 7 pipeline and produce a preview version.
- Mode selector: Evolve now enabled; unchanged files must never be sent to the LLM (assert in tests via the FakeLLMClient request log).
- Token usage recorded on the ChangeSet.
- Tests: only affected files in prompt; malformed patch JSON retried; forbidden path/dependency rejected; prompt-injection text in resume cannot widen the allowlist; end-to-end with FakeLLMClient producing a valid patch that builds.

Frontend:
- Mode selector: enable Evolve with cost/speed/risk hints.
- Change review: file changes shown in side-by-side/unified diff viewer with per-file approve/reject and rationale; "Approve selected -> Build preview" starts the pipeline and navigates to build progress then preview.
- Token usage summary on the changeset.
- Tests for the diff viewer and per-file approval.

Run all checks, then update .agents/PROGRESS.md.
```

**Acceptance checks**
- Changing only skills on the resume results in a diff touching only the skills-related files.
- Rejecting a file change excludes it from the build.
