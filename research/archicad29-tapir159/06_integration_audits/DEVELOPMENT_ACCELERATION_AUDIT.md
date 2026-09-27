# Development acceleration audit — 20 passes

Goal: shorten the cycle `source evidence -> safe implementation -> offline audit -> controlled live probe` without weakening fail-closed guarantees. This document recommends workflow/tooling only; product code is unchanged.

## Pass 01 — make Tapir version/schema sync automatic

Current bottleneck: Safe BIM pins 1.5.8 while installed Tapir is 1.5.9. Manual schema copying guarantees future drift.

Build a small offline sync tool that takes an explicit Tapir tag/commit and extracts:

- command definitions,
- common schema definitions,
- tag commit SHA,
- normalized command/field catalog,
- SHA-256 of source snapshots.

Output should be committed, reviewable generated data. Runtime must never download schemas dynamically.

Immediate payoff: every future Tapir upgrade becomes a deterministic diff rather than another broad archaeology exercise.

## Pass 02 — add schema-drift CI

For a certified Tapir version, CI should verify:

- pinned schema hashes are unchanged,
- generated catalog matches the source snapshot,
- operation verifiers reference fields that exist in that version,
- `GetAddOnVersion` compatibility table is internally consistent.

This catches accidental edits and makes version upgrades explicit.

## Pass 03 — generate strict Python models instead of hand dictionaries

Tapir-Archicad-MCP and `multiconn_archicad` demonstrate that the command schemas can drive Pydantic/type generation. `multiconn_archicad` even exposes `ForbidExtrasMixin`, `StrictMixin` and frozen-model options specifically useful for MCP/LLM validation.

Sources:
- https://github.com/SzamosiMate/tapir-archicad-MCP
- https://github.com/SzamosiMate/multiconn_archicad

Safe BIM does not need to adopt their transport. It can generate its own small strict models for certified operations only. Benefits:

- hallucinated/extra keys rejected centrally,
- IDE completion,
- less hand-written field validation,
- schema version visible in types.

## Pass 04 — one machine-readable capability registry

Create a single source of truth such as `capabilities.json` with per operation:

- operation ID/version,
- Tapir minimum/exact certified version,
- risk class,
- write command,
- read-back command/fields,
- fingerprint schema,
- capability state (`SCHEMA_ONLY`, `LIVE_VERIFIED`, etc.),
- required probes/evidence IDs,
- whether user confirmation is mandatory.

Generate human docs and AI-visible tools from this registry. Do not maintain three divergent lists in code, README and prompts.

## Pass 05 — operation scaffolder

Most new Safe BIM operations repeat the same safety pattern. Generate a skeleton from the capability registry:

`normalize -> prepare -> preflight -> checkpoint -> dispatch-start marker -> one physical write -> response GUID -> unverified receipt -> exact GUID reread -> verifier -> verified receipt -> DONE/reconcile`

The generator should create stub tests that fail until every required safety hook is filled. This accelerates expansion without copy/paste omissions.

## Pass 06 — golden read-back fixtures

Every successful controlled live probe should write a sanitized JSON fixture containing:

- Tapir version,
- Archicad version/build,
- input payload,
- returned GUID,
- exact raw read-back,
- normalized fingerprint,
- project-story context,
- provenance/time.

Future verifier work can replay these offline. One expensive live observation then supports hundreds of cheap regression tests.

## Pass 07 — trace/replay fake backend

Extend the fake backend so a recorded Tapir response trace can be replayed with injected faults:

- timeout before dispatch,
- timeout after dispatch,
- malformed response,
- wrong project,
- stale/changed element,
- partial per-item results,
- disconnect during read-back.

This turns real API quirks into deterministic tests and reduces repeated Archicad experiments.

## Pass 08 — split tests into speed tiers

Recommended test groups:

1. **unit** — pure geometry/schema/normalization, no sockets/files except temp; target seconds.
2. **safety** — runtime/state machine/unknown-outcome invariants.
3. **contract** — pinned Tapir schemas/source fixtures.
4. **integration-offline** — IPC + SQLite + fake backend.
5. **live-probe** — explicit manual/opt-in only, one write where defined.

Default developer loop runs 1+affected part of 2. Full gate runs 1–4. Live tests never run automatically just because `pytest` was invoked.

## Pass 09 — parallelize only isolated offline tests

`pytest-xdist` can run tests over multiple CPU workers and offers `loadscope`, `loadfile`, groups and work-stealing distribution.

Source:
https://pytest-xdist.readthedocs.io/en/stable/distribution.html

Use parallelism only for hermetic unit/contract tests. Keep runtime lock tests, shared-port tests and anything touching a common SQLite file explicitly serialized/grouped. Live Archicad tests remain single-worker by policy.

On a development machine, start with a small fixed worker count (for example 4), not `-n logical`, to avoid stealing all CPU from Archicad/Twinmotion during interactive work.

## Pass 10 — property/state-machine fuzzing

Hypothesis rule-based state machines generate sequences of actions and shrink failures to small repros. This maps almost perfectly to Safe BIM's executor states.

Source:
https://hypothesis.readthedocs.io/en/latest/stateful.html

Model actions such as:

- start/resume/pause/cancel,
- dispatch starts/completes/times out,
- reconciliation returns applied/not-applied/ambiguous/error,
- project identity changes,
- stale worker completes after cancellation.

Invariants:

- terminal `CANCELLED` stays terminal,
- at most one physical dispatch per attempt,
- no blind retry after possible write,
- `DONE` requires verified receipt,
- wrong PLN never writes.

This is a high-leverage way to discover sequence bugs faster than adding one anecdotal test at a time.

## Pass 11 — fast lint/static checks

Ruff is a cached Rust-based linter/formatter and is designed to replace several slower Python lint tools.

Source:
https://docs.astral.sh/ruff/

Recommended gate initially: correctness-focused rules only (`E`, `F`, selected `B`, `UP`, `RUF`) and formatting check. Do not enable hundreds of style rules at once; that creates churn without improving safety.

## Pass 12 — deterministic environment with uv

`uv` aggressively caches registry, URL and Git dependencies by resolved identity and is already a good fit for disposable tool environments.

Source:
https://docs.astral.sh/uv/concepts/cache/

The repo currently has no canonical `pyproject.toml` in the inspected `c6ab474` tree. A future tooling pass should create a minimal locked development environment for tests/research helpers while keeping runtime dependencies small.

Do not make the local AI stack a mandatory Safe BIM dependency; keep it in an optional extra/tool environment.

## Pass 13 — no resident vector database for source research

Use SQLite FTS5 for the local source/evidence index before adding embeddings. FTS5 provides full-text search, BM25 ranking and trigram substring search inside SQLite.

Source:
https://www.sqlite.org/fts5.html

Index fields:

- repo/tag/SHA/path,
- symbol/command,
- source excerpt,
- evidence classification,
- Safe BIM capability ID.

This gives fast offline source lookup with negligible idle memory and directly supports the AI progressive-discovery design.

## Pass 14 — one evidence ledger

Every claim that promotes a capability should point to evidence IDs in a machine-readable ledger:

- `SOURCE`: code/docs at exact SHA/line,
- `OFFLINE_TEST`: deterministic test ID,
- `LIVE_READ`: read-only observation,
- `LIVE_WRITE_PROBE`: controlled write GUID + raw read-back,
- `INDEPENDENT_AUDIT`: audit commit/report.

Capability promotion becomes a rule evaluated from ledger evidence rather than a prose judgment. This drastically simplifies future audits.

## Pass 15 — probe harness as a productized developer tool

The current repository already contains extensive historical `bimexec/probes`. Do not keep creating ad-hoc PowerShell snippets for every primitive.

Create a generic controlled-probe runner that accepts a signed/strict probe spec:

- exact project path/identity,
- exact command and one-item payload,
- expected read-back fields,
- maximum physical writes = 1,
- no-retry policy,
- unique coordinates/marker,
- evidence output directory.

It should stop on any uncertainty and emit a complete fixture automatically.

Historical H2 remains a separate track; do not implicitly reuse it as a new primitive probe.

## Pass 16 — progressive command discovery for developers and AI

Borrow the MCP project's `list -> schema -> call` concept but point it at the **certified Safe BIM registry**, not raw Tapir.

Developer command examples:

- `safe-bim caps search roof`
- `safe-bim caps show roof.single_plane.v1`
- `safe-bim evidence show E-ROOF-001`
- `safe-bim probe status`

The same compact interface can feed an LLM. This reduces huge prompts and means adding Tapir commands does not automatically widen write authority.

## Pass 17 — source-informed verifier generator

Generate the boring parts of a verifier from a field contract:

- required keys,
- numeric tolerance checks,
- enum equality,
- polygon canonicalization hook,
- missing-field reason reporting.

Keep topology/semantic checks hand-written. Generated checks reduce duplicate code and make error reporting consistent.

## Pass 18 — cache read-only project metadata carefully

Repeated calls for stories, attributes, favorites, library parts and design options can become slow. Introduce short-lived/project-keyed caches only after measuring.

Cache key must include project identity and Tapir/Archicad version. Invalidate on:

- project identity change,
- explicit relevant mutation,
- element/project notifications where available,
- TTL as a fallback.

Never cache data used to prove ownership or final post-write verification; exact read-back stays fresh.

## Pass 19 — isolate semantic coding from mechanical Git transfer

The current workflow already discovered a good specialization:

- semantic architecture/fixes: reasoning agent/Arena in a scoped branch,
- independent audit: separate pass/agent,
- mechanical exact-object transfer/push: deterministic Git operation,
- normal chat: research/source synthesis.

Keep exact bundle/SHA transfer rather than re-creating commits from patches whenever possible. This prevents review drift and reduces expensive agent cycles.

## Pass 20 — benchmark the development loop itself

Record elapsed time for:

- environment bootstrap,
- unit suite,
- safety suite,
- full offline suite,
- schema sync/diff,
- controller/runtime startup,
- one read-only probe,
- one controlled write-probe evidence capture.

Then optimize the slowest measured stage rather than guessing. Store these timings in a small JSON history so regressions are visible.

# Final development-speed judgment

Highest-value changes, in order:

1. **Pin/sync Tapir 1.5.9 automatically and add schema drift checks.**
2. **Machine-readable capability/evidence registry.**
3. **Generic operation scaffolder + source-informed verifier scaffolding.**
4. **Golden fixtures + trace/replay backend.**
5. **Hypothesis state-machine safety fuzzing.**
6. **Fast test tiers; parallelize only hermetic tests.**
7. **Productized one-write probe harness.**
8. **FTS5 evidence/source index and progressive discovery.**
9. **Ruff + uv reproducible tooling.**
10. **Benchmark loop and cache only what measurements justify.**

These changes reduce developer time without making execution more autonomous or less conservative.
