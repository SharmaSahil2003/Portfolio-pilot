# Step 12: Extensions (only after Steps 1-11 are done)

Pick ONE extension per session.

## 12a. GitHub integration

```text
Using the portfoliopilot-dev skill, implement the GitHub integration extension.
- OAuth connect (read-only scope), store tokens encrypted, allow disconnect.
- agents/repo_analyzer.py: for selected repos extract languages, frameworks, README summary, recent activity; output a project suggestion matching ProfileSchema.projects.
- Cross-reference resume projects with repos and suggest "Add this project to your portfolio?" as proposed Changes, never auto-applied.
- UI: connect GitHub, repo picker, suggestion cards with approve/reject feeding the normal ChangeSet flow.
- Tests with mocked GitHub API; ensure private repo content is never logged or sent to the LLM without explicit user opt-in.
```

## 12b. LinkedIn export import

```text
Implement import of the LinkedIn data export (CSV/ZIP) into ProfileSchema via deterministic parsers (no LLM for structured fields), merge with the resume profile using the diff machinery, and surface conflicts for the user to resolve in the Profile review UI.
```

## 12c. Visual validation

```text
Add screenshot-based visual validation to the build pipeline: render the preview in headless Chromium at 3 viewports, detect blank pages, console errors, horizontal overflow, and large visual regressions against the previous version (pixel-diff threshold). Surface results in the build report and preview UI; failures feed the repair agent with a textual description only.
```

After finishing, update `.agents/PROGRESS.md` and SKILL.md if the architecture changed.
