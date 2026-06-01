---
id: 004
title: Generate AGENTS.md file
stage: general
date: 2026-03-14
surface: agent
model: claude-sonnet-4.5
feature: none
branch: master
user: saifullah
command: agents-md-gen
labels: ["documentation", "agents-md", "aaif-standard", "project-setup"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - AGENTS.md
tests:
  - none
---

## Prompt

now that you have the clauide.md and constiituion, use the agentsmd gen skill to create an agents.md for this filke

## Response snapshot

Generated comprehensive AGENTS.md file following the AAIF (Agentic AI Foundation) standard for the LearnPyByAI project. The file includes:

- Build & Development Commands (with planned stack notation)
- Code Style (Python: black/isort, TypeScript: prettier/eslint)
- Security (BetterAuth, sandbox constraints, secrets management, code execution safety)
- Architecture (directory structure, Repository pattern, LLM Provider Abstraction, Prompt Template Management)
- Multi-Agent Architecture (6 specialized agents: Triage, Concepts, Code Review, Debug, Exercise, Progress)
- Testing (coverage targets, TDD approach, 5 test types)
- Performance (latency budgets, resource limits, optimization rules)
- Business Logic (mastery calculation formula, struggle detection triggers - marked immutable without ADR)
- Git & PR Conventions (GitHub Flow, Conventional Commits)
- Spec-Driven Development (PHR and ADR workflows)
- Tech Stack (Next.js 16+, FastAPI, PostgreSQL, SQLAlchemy 2.0, BetterAuth, Zustand)

The AGENTS.md extracts all critical conventions from constitution.md and CLAUDE.md, making them actionable for AI coding agents working on this AI-powered Python tutoring platform.

## Outcome

- ✅ Impact: Created AAIF-compliant AGENTS.md that serves as authoritative guide for AI agents working on LearnPyByAI
- 🧪 Tests: No tests required (documentation artifact)
- 📁 Files: Created AGENTS.md (comprehensive agent instructions)
- 🔁 Next prompts: Begin feature development using spec-driven workflow (/sp.specify for first feature)
- 🧠 Reflection: Successfully synthesized constitution and CLAUDE.md into actionable agent instructions following AAIF standard

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A (documentation)
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Validate AGENTS.md against actual development workflow as features are implemented
