---
name: Fix Run and Review Button Latency
description: Diagnosed and fixed the delayed UI response when clicking Run and Review with Tutor buttons — saveToBackend was awaited before loading state was set
type: red
stage: red
date: 2026-05-11
feature: 014-interactive-code-editor
branch: 014-interactive-code-editor
surface: agent
model: claude-sonnet-4-6
labels: ["bug", "performance", "ux", "frontend"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
---

## Prompt

> the run button and the review with tutor button respond very late to the click. i mean we get to see the runner after a very long time after clicking it. it should be instantaneous

## Root Cause

In `frontend/src/components/editor/CodeEditorPanel.tsx`, both `handleRun` and `handleReview` were `await`ing `saveToBackend(code)` — a full backend network round-trip — **before** calling `runCode`/`reviewCode` which set the loading states (`isRunning`/`isReviewing`). The button label change ("Running…") and loading UI were invisible to the user until the save completed.

`saveToBackend` is fire-and-forget by design: it already has silent failure handling, and code is sent directly to the execution/review APIs regardless of save success.

## Fix

Removed `await` from `saveToBackend` calls in `handleRun`, `handleReview`, and `handleSubmit` so the main action starts immediately on click.

**Files modified:**
- `frontend/src/components/editor/CodeEditorPanel.tsx` — lines 92–95, 121–124, 102

## Outcome

Run and Review with Tutor buttons now respond instantaneously — loading state appears immediately on click while the save happens in the background in parallel.
