# Stage 5 — Hosted Window closed loop

Status: **IN PROGRESS / NOT VERIFIED**

Base: verified post-Stage-4 performance baseline `ad0c0ed127c068d2a7446f3bf03a31f7584decad`.

## Scope

Stage 5 adds exactly one new BIM capability to the closed loop: creating one
hosted Window in one factual Wall. No Door, Slab, Roof, Morph, material edit or
delete capability is added to the closed-loop allowlist in this stage.

The lower-level `CreateWindows` recipe already has historical live PASS
evidence. Stage 5 does not rewrite that geometry logic; it binds it to the
closed-loop reliability contract.

## Typed action

`create_window` is model-bound before dispatch with:

- `sourceGuid` — factual host Wall GUID;
- `centerOffset` — station along the Wall reference line;
- `sillHeight` — height above Wall base;
- `width`;
- `height`.

Orientation flags remain frozen to the proven recipe:
`reflected=false`, `refSide=false`, `oSide=false`.

## Safety invariants

Before native dispatch:

1. host GUID exists and is a Wall;
2. host reference line is straight;
3. opening lies strictly inside Wall ends;
4. opening lies inside Wall vertical extent;
5. action, host identity, native parameters, model identity and pre-model hash
   are frozen into a durable mutation attempt;
6. stale model invalidates the action before write.

After uncertain dispatch:

- zero dispatch + unchanged fresh model -> `RECONCILED_NOT_APPLIED`;
- exactly one new Window with matching host/station plus factual host aperture
  topology change -> `RECONCILED_APPLIED`;
- zero/multiple candidates, changed host placement, conflicting receipt or
  insufficient evidence -> `RECONCILIATION_AMBIGUOUS` / BLOCKED;
- blind retry is forbidden.

## Acceptance sequence

1. typed-action and attempt/reconciliation tests;
2. offline one-iteration orchestrator proof;
3. live adapter dry-run against the explicitly bound test PLN;
4. one retained live Hosted Window create + factual read-back;
5. independent Audit Pack verification;
6. only then Stage 5 may become VERIFIED.

Until all six complete, Stage 5 remains **NOT VERIFIED**.


## Offline gate result

The first complete Stage 5 offline gate is **PASS**:

- focused Stage 2 + Stage 5 command tests: **51/51 PASS**;
- Stage 2–5 regression proof: **PASS**;
- Stage 1 historical evidence revalidation: **PASS in 6.086 s**;
- Stage 3 historical evidence revalidation: **PASS in 6.047 s**;
- total `offline-001`: **21.036 s**;
- physical mutation calls: **0**.

Acceptance criteria **W01–W07 are PASS**. Criteria **W08–W10 remain pending**
because no Stage 5 live Hosted Window has yet been accepted. Stage 5 therefore
remains **IN PROGRESS / NOT VERIFIED**.

Offline receipt:
`outputs/closed-loop-stage5/stage5-offline-acceptance.json`.
