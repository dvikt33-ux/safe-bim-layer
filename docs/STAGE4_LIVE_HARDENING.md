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

Repository drift is guarded semantically rather than by freezing the entire `main` SHA.
The historical Stage-4 merge-base remains `72e9be15...`, but unrelated main commits are
allowed. At the final read-back, the runner fetches current `origin/main` and requires zero
diff from that baseline across protected BIM runtime/evidence paths. Changes under unrelated
domains such as `knowledge/detail-machine/` do not fail the live loop; changes to
`closed_loop/`, `scripts/`, `archicad-addon/`, Stage tests/evidence, or the pinned v0.1
runtime do fail closed.

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

Default binding remains the original Stage 1 PLN identity. Stage 4 may instead
be explicitly rebound to another named disposable PLN by setting the absolute
Windows path in `SAFE_BIM_STAGE4_PROJECT_PATH`. This does not rewrite or weaken
the archived Stage 1 identity/evidence. Preflight reads GetProjectInfo first and
compares the active PLN to the explicit Stage 4 path before product/add-on
follow-ons, model dump or writes. Archicad 29 build 3000 RUS, Tapir 1.5.10 and
endpoint `127.0.0.1:19723` remain mandatory. The code never opens, switches,
saves or undoes a project.

A rebound PLN is not assumed to contain the synthetic Stage 1 wall chain.
Before a rebound live scenario, `stage4_fixture` prepares (or reuses) an isolated
two-Wall chain at the archived Stage 1 sandbox coordinates. It first proves that
the corridor is empty and the archived building material is available. Setup is
a separate, explicitly labelled LIVE_FIXTURE_SETUP action, not an S4 scenario
mutation. One CreateWalls dispatch creates the predecessor and 0.5 m seed;
factual read-back must prove exactly those two new Wall GUIDs. A dispatched
uncertain setup is UNKNOWN_OUTCOME and is never blindly repeated. The fixture
report pins the project path and seed GUID. Rebound Stage 4 planners then follow
only that unique fixture chain; they never fall back to unrelated building Walls.

```powershell
$env:SAFE_BIM_STAGE4_PROJECT_PATH = 'C:\Users\Admin\Downloads\дбликат.pln'

python -m closed_loop.stage4_fixture --output outputs/closed-loop-stage4/fixture-rebound-001 --live
$env:SAFE_BIM_STAGE4_FIXTURE_REPORT = 'outputs/closed-loop-stage4/fixture-rebound-001/fixture-report.json'

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

The two earlier rebound blockers are resolved:

1. the explicit disposable-PLN identity gate passes for the rebound project;
2. the isolated synthetic Wall fixture has been created and factual read-back
   proved exactly two added Wall GUIDs.

The latest operator run also completed the new source-pinned
`hardening-offline-006` proof with PASS. The fixture setup used one physical
`CreateWalls` dispatch and changed the factual element count from 5297 to 5299.
The retained fixture predecessor/seed GUIDs are recorded in
`docs/CURRENT_STATUS.md`.

S4-01 has now completed as LIVE PASS / VERIFIED in
`live-20261007-001/S4-01`. It produced exactly two confirmed physical mutation
calls, no duplicate mutationAttemptIds, two factual zero-distance joints, the
second action sourced from the first created Wall GUID, protected-main guard
PASS and Audit Pack PASS.

S4-02 has also completed as LIVE PASS / VERIFIED. It proved one stale-plan invalidation, zero executor calls for the stale action, three confirmed physical writes total (helper plus two goal segments), zero duplicate mutation attempts and Audit Pack PASS.

S4-03 has also completed as LIVE PASS / VERIFIED. The injected lost response after the first native write was recovered as `RECONCILED_APPLIED`; the old mutation was not replayed, the second segment continued from the reconciled created GUID, duplicate mutation count remained zero, and Audit Pack passed.

Stage 4 itself remains **NOT VERIFIED** because S4-06 is the only remaining mandatory live scenario.

Backlog only: general transactions/concurrent job ownership, additional BIM
operations, undo, UI, normative engines and performance work. None is implemented
as part of this stage.

The operator observed `hardening-offline-006` PASS before the protected-main guard change.
That proof is now source-stale because `closed_loop/live_wall.py` changed. A fresh
source-pinned offline proof is required before any new accepted Stage-4 live run.

The 30-criterion contract and ten-scenario status matrix are retained in
`outputs/closed-loop-stage4/stage4-acceptance-contract.json` and
`stage4-acceptance-report.json`. Publication is deferred until acceptance is
complete.
