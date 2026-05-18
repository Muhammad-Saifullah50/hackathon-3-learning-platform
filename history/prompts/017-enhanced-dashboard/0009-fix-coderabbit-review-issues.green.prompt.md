---
id: "0009"
title: Fix CodeRabbit Review Issues (F017)
stage: green
date: 2026-05-18
surface: agent
model: claude-sonnet-4-6
feature: 017-enhanced-dashboard
branch: 017-enhanced-dashboard
user: Muhammad
command: correct these issues found by coderabbit step by step
labels: ["code-review", "refactor", "security", "dashboard", "service-extraction"]
links:
  spec: specs/017-enhanced-dashboard/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/api/v1/agents.py
  - backend/src/api/v1/dashboard.py
  - backend/src/services/dashboard_service.py
  - backend/src/repositories/progress_repository.py
  - specs/017-enhanced-dashboard/quickstart.md
  - specs/017-enhanced-dashboard/research.md
  - history/prompts/017-enhanced-dashboard/0005-implement-enhanced-dashboard.green.prompt.md
tests:
  - python3 ast.parse syntax check: dashboard.py OK
  - python3 ast.parse syntax check: dashboard_service.py OK
---

## Prompt

correct these issues found by coderabbit step by step

(Full CodeRabbit review for PR on branch 017-enhanced-dashboard — actionable comments on agents.py, dashboard.py, progress_repository.py, quickstart.md, research.md, spec.md, and PHR 0005.)

## Response snapshot

Fixed 8 of 9 actionable issues. One change (spec.md FR-011 table name) rejected as it would create spec/implementation inconsistency.

**agents.py** — Capped quiz history window to last 10 turns and applied 500-char truncation to all roles (not just assistant), bounding prompt size.

**progress_repository.py** — Replaced bare `except Exception` with `except SQLAlchemyError as snap_exc` + `logger.warning(...)` so snapshot insert failures are observable without masking non-DB errors.

**dashboard.py** — Extracted all agent orchestration and output-parsing logic out of route handler closures into a dedicated `src/services/dashboard_service.py`. Route handlers are now thin wrappers. Also: raw `str(exc)` in SSE error payloads replaced with a generic client-safe message; `except Exception: pass` on topic parse replaced with specific `(json.JSONDecodeError, KeyError, TypeError, ValueError)` + `logger.debug`; explicit `description=` added to all three route decorators.

**quickstart.md** — Updated migration filename from placeholder `YYYYMMDD_add_mastery_snapshots.py` to actual `20260518_add_mastery_snapshots.py`.

**research.md** — Clarified that `MODULE_SLUG_MAP` integer values are unused (URL validation only) and that DB module_id resolution must use a title/slug query, not hardcoded integers.

**PHR 0005** — Corrected task count from "34" to "33" (T001–T033).

**spec.md FR-011** — Not changed. The spec says `mastery_records` and the implementation uses `MasteryRepository.get_user_mastery_records()` which queries the `MasteryRecord` model (the `mastery_records` table from F07). Changing to `user_module_mastery` would create a spec/implementation inconsistency.

## Outcome

- ✅ Impact: Security improved (no internal exception details in SSE payloads); business logic correctly separated from route handlers; parse failures are now logged; snapshot errors are type-specific and observable.
- 🧪 Tests: Syntax validated via ast.parse on modified Python files.
- 📁 Files: 1 new file (dashboard_service.py), 4 modified Python files, 3 modified doc/spec files.
- 🔁 Next prompts: Run pytest to verify no regressions from dashboard.py refactor.
- 🧠 Reflection: The service extraction was the largest change — closures capturing route-handler deps became top-level async generator functions taking deps as params.

## Evaluation notes (flywheel)

- Failure modes observed: None during this session.
- Graders run and results (PASS/FAIL): ast.parse PASS
- Prompt variant (if applicable): null
- Next experiment: Add integration tests for the SSE endpoints to confirm streaming behavior post-refactor.
