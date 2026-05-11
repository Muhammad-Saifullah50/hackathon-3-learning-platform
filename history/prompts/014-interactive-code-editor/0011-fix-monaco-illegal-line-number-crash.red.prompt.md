---
name: Fix Monaco illegal line number crash on syntax errors
description: Root-cause fix for "Illegal value for lineNumber" crash when submitting syntactically invalid code in the Monaco editor
type: red
stage: red
date: 2026-05-11
surface: agent
model: claude-sonnet-4-6
feature: 014-interactive-code-editor
branch: 014-interactive-code-editor
user: Muhammad
command: chat
labels: ["bug", "monaco", "error-highlighting", "sandbox", "line-number"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files_modified:
  - backend/src/services/sandbox/docker_sandbox.py
  - backend/src/services/sandbox/error_parser.py
  - frontend/src/components/editor/CodeEditorPanel.tsx
tests_run: []
---

## Prompt

> when i submitted synactically wromg code i got an erorr and then this  This page couldn't load
> Reload to try again, or go back.
> [Fast Refresh] done in 328ms
> editor.api-CalNCsUg.js:248 Uncaught Error: Illegal value for lineNumber

## Root Cause (Traced)

The crash had a three-stage data flow bug:

1. **Sandbox wrapper script** (`docker_sandbox.py`) wraps user code in a `wrapper.py` that calls `exec(open('/workspace/code.py').read())` at **line 9** of the wrapper.

2. **`_extract_line_number`** used `re.search(r"line (\d+)", error_str)` on the full Python traceback. The first match is always `line 9` (the wrapper script's own frame), NOT the user's code line (which appears as `File "<string>", line X` since exec'd strings show as `<string>`).

3. `enhance_error_message` embedded this as `"(occurred around line 9)"`. Then `parse_error_line` in the API endpoint re-parsed the enhanced message and extracted 9 again. Frontend received `errorLine: 9`.

4. **Monaco crash**: `CodeEditorPanel.tsx` called `model.getLineMaxColumn(9)` on a document with e.g. 1-3 lines → Monaco threw `"Illegal value for lineNumber"` → uncaught → page crash.

## Response / Fix

**Backend fix** (`docker_sandbox.py` + `error_parser.py`): Changed `_extract_line_number` and `extract_line_number` to first look for `File "<string>", line (\d+)` (the user code's exec'd frame), falling back to the last "line N" match instead of the first. This returns the correct user code line number.

**Frontend guard** (`CodeEditorPanel.tsx`): Added bounds check `if (line < 1 || line > model.getLineCount()) return` before applying Monaco decorations and markers, preventing the crash if an out-of-range line number ever reaches the editor.
