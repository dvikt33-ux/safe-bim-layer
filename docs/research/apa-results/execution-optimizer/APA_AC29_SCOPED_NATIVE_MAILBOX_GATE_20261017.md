# APA AC29 — scoped native mailbox integration (PR #153)

## Existing code reused

- **Transport:** existing single `apa_ac29_autonomous_job_bridge.py` receiver, unchanged inbox/results and persistent `attempted.json` no-replay checkpoint.
- **Native executor:** `APA.run_scoped_native_task` → `DynamicCommands.run_workflow` → **original** `SceneWriter.execute_bound_operation` → existing SQLite journal.
- **Native verifiers:** six source-owned registrations from installed `apa_ac29_dynamic_native_verifiers`, including Basic Beam/Wall/Roof CREATE and Basic Slab material-only MODIFY.
- **Save:** existing `GuardedSaveTransport`, original `router.execute(SaveProject)` and a separate persistent save scene; only after native typed + full BREP verification.

## Two inbox actions

`SCOPED_NATIVE_REGISTRY_PREFLIGHT`: **read-only** action with `sourceTask: null`. Reacquires live full native model and native BREP, installed registry and Tapir contract digests and SQLite scenes with state other than `PASS`. Returns an explicit blocker, **no native writes** and no local grants.

`APPROVED_SCOPED_NATIVE_MUTATION`: one JSON task pinned to **exact Git commit + Git blob** under `examples/accelerator/`, with source plan, parameters, current full GUID/BREP fingerprints, explicit affected GUIDs and selected code-owned contract. A **separate local grant file** `C:\LocalAI\APA_AC29_Stable\controller-grants\<job-id>.json` must match the immutable job/task blob, project SHA, command, graph, authorization and model fingerprints. Merely writing `USER_APPROVED_` into GitHub is never sufficient.

The task must have exact `APA_AC29_SCOPED_NATIVE_TASK_V1` schema; supported commands are `CreateColumns`, `CreateBeams`, `CreateWalls`, `CreateRoofs`, `ModifySlabs`, `MoveElements(copy=false)`. Existing native schema and installed verifier preflight still restrict each command to its specifically reviewed basic geometry. `CreateSlabs` is **not** added because its native schema cannot set basic structure/material directly.

## IMPORTANT: BDD native writes remain BLOCKED

The BDD working PLN was last verified with **298 GUID** and saved SHA-256 `9293c799cf4a87792016cc76ca5f2c1d8e569f85d6cbab0b529f82d10a303a34`. Current GUID hash `2619195fd2207da00f15c5db9269031a4b037228673bd0e6fe7a31624ef931a3`; current BREP signature hash `56ddccf0d78ac0986fd72b75145da9f6ff867c0a64d7f2dff0f0b964ff29579d`.

The original SceneWriter SQLite contains historical unresolved `BDD_BULK150_GRID_AND_LINE_20261016` and a later failed first-pass multi-prototype copy attempt. The first may have no current effect; the second did have accepted physical copies, independently reconciled/saved later. **They cannot be treated as interchangeable, and their original UNKNOWN rows must not be rewritten.**

The new write route invokes a read-only `pending_ledger` check before constructing the write-capable API and **rejects ANY non-PASS scene**. It does not forge local historical receipts or automatically clear past UNKNOWN. The original scope binder itself is also fail-closed on multiple pending records. The correct next task is independent proof-bound reconciliation of all the pending history, not another native test run.

## Deployment and acceptance

This branch extends the existing pinned updater using the user-confirmed installed release `6d4487d6b4ef34a0573de694c179335827d3b1fc` and initial working 298-GUID PLN. Do not deploy without matching exact file hashes and working/safe PLN evidence. No installer action creates a local native write grant. No direct local laptop access or native writes were performed from this GitHub development session.

**Status:** offline Windows/Linux unit gates verify source task allowlist, local grant match, no replay, one existing receiver, and invariant that two UNKNOWN rows block before write API creation. A confirmed Windows installation and fresh live preflight are distinct subsequent steps. Native CREATE/MODIFY LIVE PASS is **NOT claimed**.
