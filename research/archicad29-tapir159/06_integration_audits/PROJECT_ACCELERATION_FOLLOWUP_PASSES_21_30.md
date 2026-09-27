# Project acceleration follow-up — passes 21–30

Follow-up to `../05_expansion_candidates/PROJECT_ACCELERATION_PASSES_01_20.md`.

Goal: close the most important gaps from the first productivity audit without weakening Safe BIM safety. No live Archicad writes were performed.

## Pass 21 — filtered multi-GUID readback contract is confirmed; optimal batch size is empirical

`GetDetailsOfElements` in Tapir 1.5.9:

- accepts an array of exact elements;
- has optional field filtering;
- implements `isFieldRequested` so unrequested fields are skipped;
- upstream registration specifically cites avoiding expensive `floorPlanPolygons` computation.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp

Conclusion: multi-GUID filtered readback is a safe optimization.

No fixed “best batch size” is supported by source evidence. It must be benchmarked on the user's AC29 project. Proposed benchmark sizes: 1, 4, 8, 16, 32, 64 exact GUIDs using only verifier fields. Production batch size must be configurable and bounded, not guessed.

## Pass 22 — hotlink instances have strong exact readback

Tapir 1.5.9 source comments state hotlink instances are ordinary elements for deletion/details. `GetDetailsOfElements` adds hotlink-specific data including:

- `hotlinkType`;
- `hotlinkNodeId`;
- decomposed 3D `origin`;
- transformation decomposition containing rotation/mirroring.

Elements inside a placed instance report the instance as `hotlinkId`.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp

Safe verifier proposal:

`instance GUID + expected node GUID + origin + rotation + mirror + optional flags`.

This is sufficient to promote hotlink instances to a future dedicated probe candidate after schema integration. No geometry search is needed.

## Pass 23 — SEO/trims can reconcile by exact relationship state

SEO creation calls `ACAPI_Element_SolidLink_Create(targetGuid, operatorGuid, operation, flags)`. Tapir also exposes relation reads/removal. Trims similarly have `GetElementTrims` and removal.

Sources:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/SolidElementOperationCommands.cpp

Important consequence: Safe BIM does **not** need to assume Create is idempotent.

Unknown-outcome reconciliation can reread the exact target/operator relationship:

- exact requested relation present -> APPLIED candidate, subject to full relation-field match;
- provably absent -> NOT_APPLIED only when the read itself is authoritative and complete;
- ambiguous/read error -> UNKNOWN_OUTCOME/STOP.

No blind retry.

## Pass 24 — Project Profile manifest design

Architecture proposal, not an upstream Tapir feature.

A profile should be declarative and hashable:

```text
profile_id/version
required_tapir_version
project/library policy
stories policy
favorites by semantic role
layers/linetypes/pens/fills/materials/composites/profiles
property/classification definitions
zone categories
text/label/dimension presets
view settings presets
master layout / publisher expectations
hotlink module catalog
```

Each entry needs a resolution strategy: stable GUID where portable, otherwise canonical name + type + critical fingerprint. The profile hash is stored with a job so resume cannot silently switch to a different project flavor.

Do not auto-create/overwrite missing global resources during geometry dispatch. Preflight produces an explicit remediation plan.

## Pass 25 — Recipe/DAG versioning and replay

Architecture proposal.

Every compiled recipe should persist:

- `recipe_schema_version`;
- source intent hash;
- project identity;
- project-profile hash;
- Tapir version;
- Safe BIM capability-manifest version;
- ordered DAG nodes + dependencies;
- parameter/fingerprint snapshot for each node.

Resume uses the stored compiled DAG rather than re-asking AI to regenerate it. This makes AI optional after planning and prevents a changed model/prompt from changing an in-flight job.

## Pass 26 — documentation operations need four execution classes

Based on Tapir 1.5.9 source behavior, documentation automation should not use one generic “document operation” policy.

Class A — exact-ID element creation/modification:
- section/interior elevation/detail/worksheet-like model/document elements;
- text/labels/dimensions/drawings where exact element GUIDs are returned.

Class B — replace operations:
- e.g. drawing-link workflows where source code recreates and changes identity. Receipt must record old GUID -> new GUID transition.

Class C — navigator/view state:
- view settings/folders/views addressed by navigator IDs. Reconcile by exact navigator ID + requested setting subset.

Class D — external/global output:
- publisher/export, project save, rebuild. These require output/global-state policies, not element ownership.

This classification should be encoded in the capability manifest before docs automation becomes production-enabled.

## Pass 27 — cache invalidation coverage is necessarily hybrid

Tapir notifications are element-event callbacks and use a 100 ms connection timeout. They are excellent for marking element caches dirty but are not a durable event log and do not cover every project-global state change.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NotificationCommands.cpp

Therefore:

- element caches: notification-invalidated + exact reread on demand;
- project identity: reread before every physical write (existing Safe BIM rule);
- story vertical fingerprint: reread/validate before affected writes;
- favorites/libraries/attributes/profile: preflight once, then validate at point of use when a write depends on them;
- after any Safe BIM global mutation: explicitly invalidate relevant cache domains.

Avoid constant polling.

## Pass 28 — save checkpoints must be policy-controlled, not per element

`SaveProject` directly calls `ACAPI_ProjectOperation_Save`. It is a real project-global persistence side effect.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp

Per-element save would add latency and can create undesirable persistence behavior. Runtime SQLite receipts already provide execution recovery independently of PLN save frequency.

Proposed policies:

- `manual`: user/runtime never auto-saves;
- `phase`: save after a verified major DAG phase;
- `explicit_nodes`: recipe chooses specific save checkpoints.

Which policy becomes default requires a real timing/user-workflow benchmark, not a source-only decision.

## Pass 29 — deterministic fast path should bypass AI entirely

Architecture proposal.

The main runtime should route tasks in this order:

1. exact existing recipe/macro match -> deterministic execution;
2. parameterized recipe match -> collect only missing parameters (ScriptUI / point pick if needed);
3. structured planner/rules -> deterministic compile;
4. only then on-demand local/cloud AI for ambiguous natural language/design reasoning.

Approved recipes can be cached by semantic operation + profile version. The local model is not started for repetitive actions such as “place this certified apartment module 6 times”, “generate standard sections”, “update dimensions”, or “publish the approved set”.

This is both faster and more stable than trying to make the LLM itself faster.

## Pass 30 — capability tiers and certification gates

Proposed capability classes:

- **R0 READ_ONLY**: scans/details/relations/QA. Broadly usable after schema validation.
- **W1 EXACT_LOCAL**: one exact create/modify with one durable ownership target and strict readback.
- **W2 RELATION**: exact relation writes such as SEO/trim; receipt is a relation tuple.
- **W3 REPLACE**: old identity replaced by new identity; explicit transition receipt.
- **W4 GLOBAL**: stories/libraries/geolocation/project save/global recalculation/view/publisher state.
- **W5 MULTI_OBJECT_TOPOLOGY**: operations that may create/split/merge several elements, e.g. advanced MEP connections.
- **I1 INTERACTIVE**: point/UI calls that block/wait for the user; isolated WAITING_USER lifecycle.
- **X1 EXTERNAL_OUTPUT**: publisher/export/file-producing operations.

Certification gate for a write capability:

1. pinned schema/source contract;
2. pure offline payload validator;
3. exact ownership/result model;
4. verifier/reconciliation contract;
5. crash/timeout tests;
6. wrong-project/modal/busy fail-closed tests;
7. one controlled live probe;
8. independent audit;
9. only then production enablement.

# Pre-final audit after passes 21–30

## Gaps closed

- Hotlink instance verification is much stronger than the previous audit assumed.
- SEO/trim reconciliation can be designed around exact relationship reads without assuming idempotent Create.
- Filtered batched readback is source-confirmed; only performance tuning remains empirical.
- Cache architecture is now split correctly between event-driven element invalidation and explicit global-state validation.
- Project Profile, Recipe DAG and capability-tier structures are sufficiently concrete to start offline implementation design.

## Remaining material unknowns

1. Empirical AC29 timing: filtered readback batch sizes, save cost, section/drawing generation cost.
2. Arc-wall sign/orientation and single-plane roof positive-side semantics still need tiny live geometry probes.
3. Mesh Z and Morph body changes discovered in source need to be applied to offline Safe BIM builders/verifiers before probes.
4. Need exact 1.5.9 schema artifact/pin in Safe BIM instead of `tapir-1.5.8.json`.
5. Need a dedicated audit of Project Profile resource portability (names/GUIDs across template/library language/version changes).
6. Need a dedicated documentation-pipeline audit for returned identities and replacement/global semantics command by command.
7. Need a benchmark plan that measures end-to-end project time, not only individual command latency.

## Current conclusion

The dominant development path is now clear: **do not expand by adding hundreds of raw Tapir commands directly. Build a recipe compiler over a small set of certified operation families, add Project Profiles/Favorites and Hotlink Modules for reuse, batch only reads, use relations for topology, and generate documentation as a downstream DAG phase.**

This is the highest-confidence route found so far to simultaneously increase speed, reduce routine and contain failure modes.
