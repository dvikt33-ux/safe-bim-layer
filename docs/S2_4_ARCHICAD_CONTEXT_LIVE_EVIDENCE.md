# S2.4 — Archicad Context Provider Live Evidence

Status: **GITHUB_ARCHICAD_E2E_LIVE_VERIFIED**

Date: 2026-09-29

## Scope

S2.4 verifies the real read-only Archicad context path:

GitHub `CONTEXT_REQUEST`
→ `SafeBIMBridge`
→ `ArchicadContextProvider`
→ Archicad 29 / Tapir 1.5.9
→ atomic local snapshot/outbox
→ GitHub `CONTEXT_READY`
→ remote readback.

No BIM mutation commands are permitted by this provider.

## Relevant commits

Implementation:

`1f4f93b50491a43918746c18db31785623b7a0c4`
`Add read-only Archicad context provider`

Live integration allowlist fix:

`5ae53f3629d6d88cbc8f2f83315635df9ec15783`
`Allow read-only selected element query`

The integration fix adds only `GetSelectedElements` to
`TAPIR_READ_COMMANDS`.

## Targeted verification

`git diff --check` — PASS

`python -m unittest tests_sync.test_s2_4_archicad_context_provider -q`

Result:

- 29 tests
- PASS

## Direct Archicad live verification

Environment:

- Archicad 29
- Python package `archicad==29.3000`
- Tapir 1.5.9
- real open Archicad project
- 5 real selected elements

Two consecutive direct captures produced the same canonical root hash:

`6b21a866750e711dfab0ab80cd0e2d00d2389baa3eb2992388eb5321888bc351`

Result:

- direct provider capture — PASS
- deterministic capture — PASS
- privacy check — PASS
- non-allowlisted commands — 0
- BIM writes — 0
- PLN writes — 0

Selected live elements:

- Morph — `PARTIAL`
- Roof — `SUPPORTED`
- Shell — `UNSUPPORTED`
- Stair — `UNSUPPORTED`
- Roof — `SUPPORTED`

## End-to-end GitHub ↔ Archicad verification

Private operational repository:

`dvikt33-ux/safe-bim-bridge`

Evidence namespace:

`safe-bim-mailbox/live-s24-20260928T231550Z-009f0a15`

Observed flow:

1. Bridge started successfully.
2. Live Archicad instance registered for the active bridge epoch.
3. Immutable `CONTEXT_REQUEST` was created in GitHub.
4. Bridge polled the remote mailbox.
5. Exactly one live Archicad capture occurred.
6. Five selected elements were read.
7. `CONTEXT_READY` was atomically committed with the local outbox.
8. `CONTEXT_READY` was published to GitHub.
9. The exact remote object was read back.
10. Remote snapshot root hash was independently recomputed.
11. Recomputed hash exactly matched the published root hash.
12. Second tick did not recapture.
13. Bridge restart with the same SQLite state did not recapture.
14. Pending outbox after successful publication was zero.

Snapshot:

`SNAPSHOT ID: snap-6260a7937ec1731b795a61a5`

Canonical root hash:

`6b21a866750e711dfab0ab80cd0e2d00d2389baa3eb2992388eb5321888bc351`

Published remote message:

`context-ready-d4310d6d45fcdc53c6ef45eeff544fef`

## Archicad read command audit

Commands observed during the end-to-end capture:

- `GetProjectInfo`
- `GetAddOnVersion`
- `GetStories`
- `GetSelectedElements`
- `GetDetailsOfElements`

`GetDetailsOfElements` was executed once for each of the five selected GUIDs.

Non-allowlisted Archicad commands:

`0`

Read-only fence:

`PASS`

BIM writes:

`0`

PLN writes:

`0`

## Privacy

Actual remotely published `CONTEXT_READY` payload was checked for:

- full `C:\Users\...` path leakage
- Windows username path leakage
- hostname leakage
- GitHub token names / token material

Result:

`PASS`

The remote snapshot uses the generated logical project identifier rather
than exporting the local project path.

## Idempotency

Second Bridge tick:

- request recognized as duplicate
- no second `GetSelectedElements`
- no second live capture

Result:

`PASS`

Bridge restart:

- remote head returned `NOT_MODIFIED`
- no second live capture
- pending outbox = 0

Result:

`PASS`

## Negative-path evidence

An earlier live attempt intentionally exposed an incorrect nested wire
shape (`body.body`).

Bridge rejected the malformed `CONTEXT_REQUEST` as `DEAD_LETTER`.

The Archicad provider was not invoked and no BIM write occurred.

This confirms fail-closed behavior at the remote protocol boundary.

## Milestone status

- S2.2 GitHub mailbox — `GITHUB_LIVE_VERIFIED`
- S2.3 context roundtrip — `GITHUB_LIVE_VERIFIED`
- S2.4 Archicad context provider — `GITHUB_ARCHICAD_E2E_LIVE_VERIFIED`

S2.4 is closed for the verified read-only `selection` scope.

Any future expansion of scope or allowed Archicad commands requires
separate verification.
