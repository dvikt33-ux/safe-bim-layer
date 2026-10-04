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

## Working-first development rule (mandatory)

This rule applies to every development task, not only Archicad integration.

1. **Make the smallest useful end-to-end path work first.** The first milestone may be crude, slow, narrow, or inconvenient, but it must perform the core user-visible function against a real test scenario.
2. **One area at a time.** A scope is opened, implemented, validated, and explicitly marked DONE before unrelated areas are started.
3. **No breadth without a closed vertical slice.** Do not spread effort across safety hardening, UI, performance, advanced geometry, broader reading, audits, orchestration, or future infrastructure while the core path of the current area is still non-working.
4. **Optimisation follows functionality.** Performance, elegance, abstractions, refactoring, caching, richer algorithms, and wider coverage are layered on only after the basic path works reliably.
5. **Safety and quality are layered deliberately, not ignored.** After the working skeleton exists, improve reliability, safety, validation, read/write completeness, algorithms, performance, UX, and deeper audits in controlled stages.
6. **The final quality target remains high.** The staged approach does not lower the end goal: the finished product should be robust, maintainable, precise, and where applicable compliant with relevant GOST/SP/SNiP and project requirements.
7. **DONE must be testable.** Every area needs an explicit acceptance criterion and a reproducible real-world check. "Partly implemented", "infrastructure prepared", or "tests exist" is not DONE if the user-visible function still does not work.
8. **Do not let future infrastructure displace the current minimum function.** If a foundational feature is still unfinished, speculative architecture, auxiliary audits, and unrelated improvements must wait unless the user explicitly reprioritizes them.
9. **Prefer a working vertical slice over many partial horizontal layers.** Complete one chain from input to useful output, then expand it.
10. **Preserve the working baseline.** Once a slice works, keep it reproducible and avoid destabilizing it while adding the next layer; use focused branches/tests and keep a rollback path.

Default development order:

```text
working skeleton
-> reliability
-> safety/validation
-> completeness of reading/writing
-> algorithms/domain logic
-> performance
-> interface/UX
-> deeper audits and advanced capabilities
```

If a task proposes a different order, that deviation must be explicit and justified by the user or by a hard dependency.

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

