# Step 3: Profile diffing

**Prerequisite:** Step 2 done.

```text
Using the portfoliopilot-dev skill, implement Step 3: Profile diffing (SKILL.md Section 5.2).

Backend:
- services/profile_diff.py as PURE functions (no DB, no LLM):
  - diff_profiles(old, new) -> list[ProfileChange] with added / removed / updated per section and field-level before/after for updates.
  - Match items by stable id first, then fuzzy match (e.g. company + role similarity, project name similarity) to distinguish "updated" from "removed + added".
  - affected_sections(diff) -> set[str].
  - Handle: first profile (old is None => everything added), identical profiles (empty diff), reordered lists (no change), renamed skills via alias table.
- Endpoint: GET /profiles/{id}/diff?against={other_id}.
- Tests: heavy parametrized unit tests plus property-style tests (diff(a, a) is empty; applying diff semantics is consistent). Aim for >95% coverage of this module.

Frontend:
- ProfileDiff component: grouped by section, chips for added (+), updated (~), removed (-), expandable field-level before/after.
- Integrate into the Profile review page: "Compare with previous version" selector.
- Component tests including empty-diff and large-diff cases, keyboard accessible.

Run all checks, then update .agents/PROGRESS.md.
```

**Acceptance checks**
- Uploading a second, updated resume shows an accurate diff.
- Pure-function tests cover add/remove/update/reorder/identical/first-profile.
