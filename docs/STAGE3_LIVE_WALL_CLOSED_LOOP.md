# Stage 3 — one live Wall closed loop

**STAGE 3: PASS.** Branch: `work/stage3-live-wall-closed-loop`, based on VERIFIED Stage 2 `d6ed3b071c1e7d17b8d819377e1984c80dd9ed33`.

One supplied goal command:

> Продолжи последнюю созданную стену сначала на 1 метр, затем ещё на 0,5 метра и проверь результат.

Goal ID: `stage3-live-wall-001`. Tested PLN: `NativeGeometry_Full_Test_20261004.pln`; the full pinned identity is retained in preflight and identity responses. Archicad 29 build 3000 RUS, Tapir 1.5.10, localhost port 19723.

| Iteration | Automatic source | Created GUID | Length, m | Joint distance, m | Element count |
| --- | --- | --- | --- | --- | --- |
| 1 | C621D5B7-6215-4925-8651-DD5FBB71EA14 | B492859E-E508-46B3-87ED-0B07C6C580CC | 1.0 | 0.0 | 5304 → 5305 |
| 2 | B492859E-E508-46B3-87ED-0B07C6C580CC | 40F79CDC-61BC-43E1-A65C-32E962568F3F | 0.5 | 0.0 | 5305 → 5306 |

Both operations belong to one job. After the first read-back, required criteria for the unfinished second segment remained FAIL, causing REPLANNING rather than VERIFIED. The live branch then performed a new observation before planning the second action. The unchanged baseline planner automatically selected the factual first created GUID. The equality `iteration2.sourceGuid == iteration1.createdGuid` is machine-checked.

All C01–C24 PASS; required FAIL = 0, NOT_VERIFIED = 0; UNKNOWN_OUTCOME = 0. Both stale verdicts are CURRENT. Planning, model-check and executor pre-write fingerprints match within each iteration. Model hashes progressed `c6d081be… → af196a3f… → 036fe623…`; full SHA-256 fingerprints are in the report. No-progress protection remains active with limit 2.

## Implementation

`closed_loop/live_wall.py` provides Live Observer, Planner, Executor, ReadBack and ModelCheck adapters. Planning uses the existing `archicad_chat_executor.instruction_to_request` on the fresh full dump. Execution uses the exact existing `archicad_executor.run` typed request/write/read-back path under that chat adapter. No second Wall writer or new BIM operation was introduced. Baseline scripts and native add-on are unchanged.

The executor adapter wraps the existing dump/API dependencies to retain per-iteration evidence, pin project identity, allow only CreateWalls and compare the executor's own fresh pre-write dump with the bound plan. A mismatch raises a distinct pre-write stale signal before native dispatch; the orchestrator invalidates the plan and re-observes. The normal ModelCheck remains active before EXECUTING. Timeouts, transport exceptions or uncertain native results stop UNKNOWN_OUTCOME without retry or recovery.

Stage 2 defaults remain offline and still reject live components. Stage 3 explicitly selects LIVE and uses separate typed live provenance records. `closed_loop/stage3.py` accepts only this fixed two-segment goal; it is not a general natural-language intent expansion.

## Regression and retained evidence

48/48 offline tests PASS: all 44 unchanged Stage 2 tests plus 4 adapter tests. Adapter tests use synthetic data and forbid networking; they are separate from actual live proof.

The independent v0 regression used unchanged `chat.run` for its original two commands, before the autonomous Stage 3 job: 5302 → 5303 → 5304, lengths 1.0/0.5, joints 0.0/0.0, dependent GUIDs verified. These regression mutations are separate from the one-goal job above. An initial runner attempt stopped during offline test discovery before any live call; its local directory was preserved and is excluded from publication.

- [Full C01–C24 verification report](../outputs/closed-loop-stage3/run-002/stage3-verification-report.json)
- [Full job and evidence trail](../outputs/closed-loop-stage3/run-002/job.json)
- [V0 regression report](../outputs/closed-loop-stage3/run-002/v0-regression/v0-regression-report.json)
- [Offline regression](../outputs/closed-loop-stage3/run-002/offline-report.json)
- [SHA-256 manifest](../outputs/closed-loop-stage3/run-002/manifest.json)

Goal, contract, preflights, identity responses, planner decisions, model-check fingerprints, typed requests, native request/response receipts, read-back witnesses, summaries and audit history are retained. Full dumps larger than 1 MB remain LOCAL_ONLY at manifest absolute paths, with sizes and hashes. Compact evidence is committed. Historical Stage 1/2 evidence and tests are unchanged. Main remained `72e9be15ac3b943d7b6f0c46eaa45aa5798d56bc`.

No cleanup, manual model correction, save, undo or transaction command was issued. All four created Walls (two regression plus two job Walls) remain in the current live model; PLN save was not part of this acceptance.

## BACKLOG / NOT PART OF STAGE 3

Stage 4, recovery/reconciliation, new BIM capabilities, UI, normative work and optimization require a separate task. No Stage 3 blockers remain. Stop after this stage.
