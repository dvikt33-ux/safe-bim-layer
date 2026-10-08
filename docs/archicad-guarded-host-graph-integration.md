# Guarded Wall Host + BIM graph integration (2026-10-09)

**Status:** Offline integration only. No Archicad commands were executed; no
PLN, running watcher, mailbox JOB/RESULT or local SQLite journal was modified.

## Proven baseline retained

- Deployed application: **Archicad 29.2.1 (5101) RUS FULL (x86-64)**.
- Read back from the installed extension: **Tapir 1.5.10**.
- Schema snapshot used for offline validation: `tapir-1.5.8.json`
  (**older than the live add-on**; schema validation is not native execution proof).
- Original local Wall Host source and 10 safety tests were copied unchanged
  from commit `c0223e18370e5e3d5205ca401a68d7603b4be120`:
  `scripts/archicad_mailbox_wall_host.py`,
  `scripts/test_archicad_mailbox_wall_host.py`.
- The guarded runtime host still depends on clean original bridge checkout at
  `27906e2a1370146a8d740f02384ab02a584ce918`.
- Live command allowlist is still exactly `{"CreateWalls"}`, with a single
  straight, centered Basic wall, active native story index 0 (first story,
  not an actual “zero floor”). No `CreateWindows`, `CreateDoors`,
  `CreateSlabs`, `CreateColumns`, or MEP write access.
- The existing Mailbox watcher remains dry-run only. No new background
  executor was deployed by these GitHub changes.

## Integration changes

1. Graph-to-Mailbox `_wall_params` matches guarded live host validation:
   length 0.2–5m, height 0.5–5m, thickness 0.05–0.5m; index 0,
   Z/offset/arcAngle = 0; Basic/Center.
2. `execute` planning refuses **all mixed-command graphs up front** while
   unverified recipes are present, even if prior steps are marked complete.
   It never posts a JOB from this offline compiler.
3. RESULT verification additionally requires `plnSaved=false` and an
   explicit 64-character lower-hex `operationHash`. This hash is checked for
   form, **not cryptographically tied to a prior trusted JOB** by this module:
   caller MUST retrieve evidence through the trusted authenticated mailbox
   and perform operation correlation before a later production rollout.
4. CI discovers and runs the 10 unmodified original `WallExecutor` synthetic
   tests through an integration suite, then asserts the generated dry-run
   envelope is directly accepted by the copied live host `validate()`.
5. Schema-correct wall → hosted window/door and slab/column graphs remain
   **offline graph structures only**, and fail safe with
   `UNSUPPORTED_GRAPH` if requested for execute mode.

## Required gates before more write recipes

- Obtain and compare an authentic **Tapir 1.5.10 schema** with bundled
  1.5.8 (especially ownerWallId, openings, slab origin, story and material).
- Keep the installed guarded `WallExecutor` fully intact until the newly
  integrated source and the original safe-bridge version are validated on the
  test system. Do not replace a running host from GitHub without an audit.
- Implement typed hosted window/door recipes with explicit parent wall GUID,
  host readback, aperture/edge-clearance validation and exact operation hash.
  Slab/column follow independently. MEP next; do not enable generic `Create*`.
- Retain exact project path/name, port, logicalProjectId, before-write binding
  checks, fsynced intent, durable de-duplication and GUID readback. Never save
  or switch projects and never re-issue a write after UNKNOWN_OUTCOME.
- As the user works on another PLN, keep this test-only runner fail closed.

**Current milestone:** source-level end-to-end interface plus offline safety
proof, NOT live multi-element BIM creation. The main development branch and
production PLN are unchanged.
