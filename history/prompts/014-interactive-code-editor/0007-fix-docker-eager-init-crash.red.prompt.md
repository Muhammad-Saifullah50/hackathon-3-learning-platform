---
id: "0007"
title: Fix Docker Eager Init Crash on Code Execution
stage: red
date: 2026-05-10
surface: agent
model: claude-sonnet-4-6
feature: 014-interactive-code-editor
branch: 014-interactive-code-editor
user: Muhammad
command: chat
labels: ["debugging","docker","sandbox","code-execution","wsl2"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/services/sandbox/docker_sandbox.py
tests:
  - null
---

## Prompt

[User pasted full FastAPI 500 stack trace showing:]
```
docker.errors.DockerException: Error while fetching server API version: ('Connection aborted.', FileNotFoundError(2, 'No such file or directory'))
```
Originating from `DockerSandbox.__init__` → `docker.from_env()` during a POST to `/api/v1/code-execution`.

## Response snapshot

Root cause: `DockerSandbox.__init__` (docker_sandbox.py:25) calls `docker.from_env()` eagerly at construction time. WSL2 distro does not have Docker Desktop integration enabled, so Docker socket (`/var/run/docker.sock`) does not exist. This causes the exception to propagate through `CodeExecutionService.__init__` and crash the entire endpoint with a 500 before any error handling fires.

Fix applied: Made `docker.from_env()` lazy by replacing `self.client = docker.from_env()` with a `_client` backing field and a `client` property that initializes on first access. The `DockerException` now surfaces inside `execute_code` where the existing `except Exception` handler returns a proper JSON error response instead of a 500.

Environment fix needed: User must enable Docker Desktop → Settings → Resources → WSL Integration for their distro, then restart terminal.

## Outcome

- ✅ Impact: Backend server can start and respond to /code-execution with a proper error message even when Docker is unavailable; 500 crash on service construction eliminated
- 🧪 Tests: None added (environmental/infra bug; lazy init is straightforward property)
- 📁 Files: backend/src/services/sandbox/docker_sandbox.py (lazy client initialization)
- 🔁 Next prompts: Enable Docker Desktop WSL2 integration to restore actual execution
- 🧠 Reflection: Eager resource acquisition in __init__ is a footgun for optional/external dependencies — lazy initialization should be default for external socket connections

## Evaluation notes (flywheel)

- Failure modes observed: DockerException propagating through service constructor before any error handling
- Graders run and results (PASS/FAIL): manual trace only
- Prompt variant (if applicable): null
- Next experiment: Consider adding a health-check endpoint that reports sandbox availability status
