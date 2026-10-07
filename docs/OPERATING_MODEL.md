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


## Native BIM minimality rule

The Safe BIM Layer must optimize for **semantic fidelity with the fewest native Archicad elements**, not for convenience of script generation.

1. A continuous physical wall with unchanged relevant properties is one Wall.
2. Doors and windows are hosted Door / Window elements in that Wall; they are not produced by splitting the Wall around the opening.
3. A Wall may be split only for a real construction/geometry reason: end, corner, true open gap, change of thickness, structure/material, elevation/story behavior, or another property that cannot be represented by a single Wall.
4. Use the dedicated Archicad element type for the modeled object whenever available. Do not substitute Lines, Polylines, Arcs, Hatches, Morphs, or helper Wall fragments for native BIM elements.
5. Do not create duplicate/overlapping hosts or helper BIM elements only for dimensions, selection, or scripting convenience when the real elements can serve as references.
6. Before every write, simplify the element graph by merging compatible collinear/continuous runs. Every remaining split must have an explicit semantic or construction reason.
7. Read-back validation must check not only geometry but also **unnecessary fragmentation**. If adjacent elements can be merged without changing geometry, semantics, hosted relationships, or required properties, the write is not accepted.

Canonical rule: **minimum BIM element count, maximum native Archicad semantics**.
