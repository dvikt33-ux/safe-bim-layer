# APA Archicad 29 — native Create/Modify operation-scoped integration

## Purpose

Do not create another executor or repeat hundreds of already completed function tests. Reuse the installed `DynamicCommands.prepare_workflow / run_workflow / execute`, BIM Graph, existing live Tapir schemas and original durable SQLite `SceneWriter.execute_bound_operation`.

## New modules

- `scripts/apa_ac29_dynamic_write_scopes.py`: binds exactly one source-approved CREATE or MODIFY operation in an existing mixed read/write graph to a code-owned native verifier. Supports read steps in the same graph. Enforces source plan hash, reviewed command effect + impact, exact native contract hash, pinned user-authorized PLN SHA and full pre-operation GUID/BREP fingerprints, an exact affected/retained GUID partition, a unique never-before-used SQLite scene and independent native pre/post callbacks. Dependent mutation input bindings must be separately approved; general deferred writes are deliberately not silently enabled. Any earlier `UNKNOWN` requires a separate external live native reconciliation receipt; original SQLite row stays unchanged.
- `scripts/apa_ac29_dynamic_native_verifiers.py`: the first installed-code-native verifier `VerifiedNativeColumns` reuses the previously accepted `CreateColumns` criteria: centered vertical rectangular source, exact native typed dimensions/material/position/story, one owned `ColumnSegment` per root, closed source-approved BREP envelope, no unexpected GUID changes. Source inputs with slant/rotation, unexpected parameters or unsupported family types fail closed.
- `tests/test_apa_ac29_dynamic_write_scopes.py`: only new contract tests for approval, duplicate/unknown scenes, GUID/BREP fingerprint requirements, no unreviewed second mutation, and the code-owned Column source geometry gate.

## Where this fits

The original `APA.run_native_task(router, api, preview, writer, scopes=scope_callback)` delegates to the existing dynamic graph. The new binder returns only the missing per-step scope callback; the original router still performs native registration, command schema checking, durable intent-before-write, retained-BREP checks, and no automatic replay. An external/untrusted task **cannot supply executable verifier code**, claim a command effect is safe by prefix, or create its own writer.

## Status and next integration

Code and focused CI only. **No installer, no bridge write action, no local deployment, no Archicad execution** in this branch. Nothing changes the user's `main`, BDD PLN, stable APA core, UI dispatcher or Archicad 30. CreateColumns has a reviewable code-owned verifier, but it is not yet part of the installed runtime registry. Other Create/Modify families remain `VERIFIER_NOT_REGISTERED` until their existing strict source/geometry checks are attached and natively qualified. The generic scope framework supports both CREATE and MODIFY but does not assert runtime acceptance of any newly wired native write.
