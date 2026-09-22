# Operating model: Local AI, Archicad, GitHub and Arena

## Purpose

This repository uses a split-responsibility workflow. Local tools retain control
of Archicad and the local model; GitHub is the reviewable hand-off boundary; Arena
is a cloud reviewer and patch author, never a controller of a real BIM project.

```text
Local Qwen planner
  -> high-level contract only (for example: create_room)
  -> Safe BIM Layer
  -> schema validation + fail-closed checks + read-back
  -> Tapir bridge on 127.0.0.1
  -> Archicad copy / test project

GitHub private repository
  <- source, schema, sanitized tests, review documents
  -> Arena Agent: audit or patch in arena/* branch
  -> pull request
  -> local Codex review, tests and optional real-copy validation
```

## Responsibilities

| Component | May do | Must not do |
| --- | --- | --- |
| Local Qwen | Produce high-level, schema-bound intent | Call Tapir or receive raw GUIDs |
| Safe BIM Layer | Construct payloads, validate schema, serialize writes, read back results | Guess unsupported Tapir fields or silently repair a mismatch |
| Local Codex | Run local tests, inspect diffs, validate a copy of a project after review | Push secrets, models, logs, or real projects |
| GitHub | Hold the sanitized source of record and PR review trail | Store GGUFs, credentials, Archicad project files or sensitive logs |
| Arena | Audit code, research documented patterns, propose small patches in a branch/PR | Access local Archicad, operate real projects, merge to `main`, or handle secrets |

## Branch and review policy

1. Keep `main` deployable and protected by local review.
2. Create a focused branch for every Arena task: `arena/<topic>`.
3. Arena returns a PR or unified diff; it never writes directly to `main`.
4. Local Codex checks the diff, runs offline/unit tests, and validates a copy of an
   Archicad project only when the task expressly requires it.
5. A human decides whether to merge. No agent creates, saves, closes, or changes
   a production `.pln` / `.pla` project.

## What may be shared with Arena

- Tracked source, tests, pinned Tapir schema and high-level design documents.
- Sanitized, reproducible test fixtures without real-project identifiers.
- A precise task statement plus expected outputs and acceptance criteria.

Never share API keys, `.env` files, model weights, GGUF files, personal data,
Archicad project files, raw local logs, or machine-specific integration results.

## Normal task loop

1. Local Codex writes a task brief under `docs/tasks/` or updates the existing
   Arena hand-off brief.
2. Arena audits or implements only the scoped code change in `arena/<topic>`.
3. Arena opens a PR with rationale, tests, and known limitations.
4. Local Codex reviews the PR and runs local validation.
5. If approved, a human merges the PR; then local Codex may perform a controlled
   validation against an explicitly selected copy of an Archicad project.

