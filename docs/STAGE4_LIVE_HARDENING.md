# Stage 4 — current Wall fault handling

Base: `03c64733bb2b4f59970f5247a3ed89e1236f3090`.
Branch: `work/stage4-live-hardening`.
Scope: the existing `create_wall`, one goal, +1.0 m then +0.5 m.
Stage 5 is prohibited until every required Stage 4 criterion passes.

## Runtime

`Iteration` and `Job` gain additive attempt/recovery fields. Old Stage 2/3 jobs
can be deserialized with defaults. Ordinary terminal `run()` and `transition()`
still prohibit retry. Only `RecoverableWallOrchestrator.reconcile_and_continue`
can leave uncertainty, after a fresh observation bound to the attempt.

Each Stage 4 physical write has a UUID stored in its job and evidence before
execution. An exclusive, fsynced claim spends that ID. The executor journal
records dispatch before entering the unchanged v0 native API, then records the
response before injecting a lost response or a crash. The same ID cannot be
claimed or dispatched twice. Job writes flush/fsync before atomic replacement.

The signature contains the source GUID and semantic hash, source endpoint,
expected begin/end/length, story/elevation, height, thickness, bottom offset,
absolute bottom, offset, material/structure identity, tolerance, native request
parameters, model identity and the pre-mutation fingerprint. Timing is not part
of the model hash. Native body indices alone are technical noise for the source
semantic comparison; geometry/properties/material changes remain significant.

Reconciliation is scoped to this signature, never "last created Wall":

| Evidence | Result | Continuation |
|---|---|---|
| Exactly one new matching Wall; unchanged source/story; dispatch journal matches; native receipt, if retained, agrees | RECONCILED_APPLIED | Audit fresh factual read-back, then continue from the actual created GUID; never repeat the old attempt |
| Trusted controlled helper proves zero dispatch, and fresh model equals pre-state | RECONCILED_NOT_APPLIED | Fresh observation and fresh planning; a new attempt UUID |
| Multiple/no candidates after dispatch, stale source, conflicting receipt, missing journal or unavailable evidence | RECONCILIATION_AMBIGUOUS | BLOCKED_RECONCILIATION_AMBIGUOUS; no retry |

An unchanged dump after a dispatched timeout is not proof of non-application.
`retryAllowed` is cleared when a new attempt is prepared. Neither executor
success nor a correlation ID substitutes for factual model read-back.

Known pre-dispatch transport failure terminates `BLOCKED_BY_TRANSPORT`, not
`UNKNOWN_OUTCOME`. A confirmed native response with missing factual read-back
also blocks transport acceptance. A lost/unavailable execution result records a
structured UNKNOWN result with attempt ID and uncertainty reason. Recovery of
an unfinished EXECUTING/READING_BACK checkpoint starts as UNKNOWN and reconciles.

No-progress and maximum iterations have distinct terminal reasons:
`BLOCKED_NO_PROGRESS` and `BLOCKED_ITERATION_LIMIT`. The initial project identity
is pinned; re-observation cannot silently bind another PLN.

## Reproducible offline proof

```powershell
python -m closed_loop.stage4_offline_evidence --output outputs/closed-loop-stage4/new-offline-run
```

This preserves all 95 baseline tests, runs the new tests, recomputes the Stage
1/3 archived source SHA/geometry proof, and persists actual fixture-test outputs
for S4-04/05/06-offline/07/08/09/10. These records are explicitly OFFLINE_FIXTURE,
with zero real physical writes. They do not satisfy the mandatory live gate.
Tests and archived raw evidence are retained; previous checks are not weakened.

## Mandatory live proof

Only `NativeGeometry_Full_Test_20261004.pln`, Archicad 29 build 3000 RUS, Tapir
1.5.10, endpoint `127.0.0.1:19723`. Preflight reads GetProjectInfo first. A wrong
project stops before product/add-on follow-ons, model dump or writes. The code
never opens, switches, saves or undoes a project.

```powershell
python -m closed_loop.stage4_live_scenario --scenario S4-01 --output outputs/closed-loop-stage4/S4-01 --offline-proof <offline-verification-report.json> --live
python -m closed_loop.stage4_live_scenario --scenario S4-02 --output outputs/closed-loop-stage4/S4-02 --offline-proof <offline-verification-report.json> --happy-report outputs/closed-loop-stage4/S4-01/completion-report.json --live
python -m closed_loop.stage4_live_scenario --scenario S4-03 --output outputs/closed-loop-stage4/S4-03 --offline-proof <offline-verification-report.json> --happy-report outputs/closed-loop-stage4/S4-01/completion-report.json --live
python -m closed_loop.stage4_live_scenario --scenario S4-06 --output outputs/closed-loop-stage4/S4-06 --offline-proof <offline-verification-report.json> --happy-report outputs/closed-loop-stage4/S4-01/completion-report.json --live
```

Each output must be new. The offline proof pins the current implementation and
frozen v0 files. S4-01 performs one two-segment goal. The archived Stage 1 baseline
is labelled archived, not a fresh independent v0 write test.

S4-02 uses a separately journalled +0.5 m Wall helper to change the live model
after the old +1.0 m plan. The helper action differs from the stale action. The
old decision is invalidated before executor entry; fresh observation replans.
There are three writes in this scenario: helper, then two goal segments.

S4-03 loses the response after the actual first CreateWalls. The job stops UNKNOWN,
its checkpoint is retained, then fresh reconciliation and audit continue the
remaining segment without replaying the first.

S4-06 runs a dedicated child. It exits with code 86 after the physical create and
flushed native receipt, before ordinary read-back/audit. The parent loads the
durable job and reconciles; it never relaunches the old mutation. An unexpected
child outcome blocks. This is available for a safe authorized live probe but is
not claimed live-verified before that probe passes.

## Audit Packs and storage

`scripts/stage4_audit_pack.py` uses the completed v2 audit primitives without
altering the old extractor or its 47 tests. Scenario packs include source SHA
pins, sanitized records, deduplicated complete GUID/full-element-hash indices,
and recomputed rawChanged/semanticChanged/technicalNoiseChanged deltas. Added
and removed full objects remain in the delta. Failed/uncertain outcomes can have
a verifier-PASS pack; that proves evidence integrity, not a VERIFIED goal.

The verifier re-extracts from pinned sources and compares every byte. Public
path scanning applies to decoded values, keys and filenames. Full snapshots and
large raw native responses receive exact-path LFS rules only after capture;
compact packs remain ordinary Git. A manifest records original full-source
hashes. Pack/source corruption, extra files and unsupported contracts fail closed.

## Current gate

The latest actual identity gates returned another PLN and stopped before any
mutation. Therefore mandatory S4-01/02/03/06 are BLOCKED, regardless of UI/user
confirmation. No offline fixture is promoted to live evidence. Full Stage 4 is
BLOCKED until the endpoint reports the exact named test project and all live
scenarios plus C01–C30 pass.

Backlog only: general transactions/concurrent job ownership, additional BIM
operations, undo, UI, normative engines and performance work. None is implemented
as part of this stage.

Final offline proof: `outputs/closed-loop-stage4/hardening-offline-003/offline-verification-report.json` (95 baseline + 33 new tests, PASS).

The 30-criterion contract and ten-scenario status matrix are retained in `outputs/closed-loop-stage4/stage4-acceptance-contract.json` and `stage4-acceptance-report.json`. Mandatory live proof remains BLOCKED. Publication is deferred until acceptance is complete.
