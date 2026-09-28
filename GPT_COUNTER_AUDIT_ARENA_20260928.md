# GPT COUNTER-AUDIT — Arena full-system Safe BIM audit

Date: 2026-09-28

Base: `audit/arena-full-system-audit-20260928` @ `181ca75229d9fd949797dbfa607c5245b121aaec`.

This is an independent counter-audit of Arena's reports. No Archicad session was run in this pass. Evidence grades remain `LIVE_CONFIRMED`, `STATIC_CONFIRMED`, `INFERRED`, `UNRESOLVED_LIVE_REQUIRED`, and `CONTRADICTED`.

Primary source set checked in this pass:

- exact Tapir release `1.5.9` = `d0dbb11b13942e014661e1402b07958b70cd9dba`;
- exact 1.5.9 Tapir source, especially `ElementCreationCommands.cpp`, `ElementCommands.cpp`, `AttributeCommands.cpp`, `CommandBase.cpp`;
- official Archicad 29 API documentation for Morph edge changes, Solid Operations, Opening, collisions, and element/database APIs;
- Arena's six published audit artifacts;
- GOST 2.307-2011 and GOST R 21.101-2020 for dimension-layout rules.

## 1. Executive result

Arena materially improves the previous architecture and correctly found several important errors. Most of its direction is accepted. However, the counter-audit found several places where Arena's proposed solution is too broad or one specific implementation claim is wrong.

The most important corrections are:

1. **GOST dimension offsets are not merely policy.** GOST 2.307-2011 §5.11 specifies minimum 7 mm between parallel dimension lines and 10 mm between a dimension line and the contour; §5.12 requires avoiding crossings. GOST R 21.101-2020 §5.4.2 specifies 2–4 mm 45° ticks and 0–3 mm extension beyond the extreme extension/contour/axis lines. These belong in the `normative_ref` side of the rule engine, not only project policy.
2. **Arena's suggested stock check for “composite is in use” is invalid as written.** `GetElementsByType` does not accept an arbitrary `compositeId` filter; its filters are fixed visibility/editability/context flags. A stock implementation must enumerate relevant element types and inspect minimal `GetDetailsOfElements` structure/attribute fields, or add a dedicated attribute-usage wrapper.
3. **Automatic delete+recreate is too aggressive for permanent Morphs.** It is safe for Safe-BIM-owned temporary/operator Morphs. For permanent Morphs, body replacement must remain fail-closed until dependency capture/replay or a live-proven in-place fix exists. A GUID lineage record alone does not prove that every dimension, label, property, classification, group, hotlink relation, and external reference was preserved.
4. **`GetCollisions` and built-in Volume are candidate evaluated-geometry verifiers, not confirmed verifiers yet.** Their existence is STATIC_CONFIRMED, but SEO-evaluated semantics are `UNRESOLVED_LIVE_REQUIRED` until LT-C1/LT-C2. Before those tests, an SEO result must stay `LINK_ONLY`, even if both commands exist.
5. **`.mod` + Hotlink complements the shared library; it does not replace it.** Use `.mod` for reusable native BIM assemblies. Keep a linked local shared library + auto-attach for GSM/library parts. A future GSM writer is still required for true reusable parametric objects.
6. **`atomic:true` is the right Tapir-level direction, but the response contract must be rollback-aware.** If the undoable lambda rolls back, previously returned GUIDs from the loop must not be exposed as durable created elements. The command must mark them rolled back/clear them and Safe BIM must verify absence.
7. **Do not deliberately reproduce the known Slab crash as a normal test.** On Tapir 1.5.9, `Get3DBoundingBoxes` for Slab is blacklisted by version policy based on the exact source plus upstream #686/PRs. A crash-reproduction test is optional only in an isolated sacrificial Archicad session; it is not required to design the safe path.

## 2. Independent verification of Arena's strongest findings

### 2.1 Exact Tapir baseline — ACCEPT

`1.5.9` is the release/tag commit `d0dbb11...`. The later `b1dc828...` source reports 1.5.10-dev and must not be used as the live 1.5.9 baseline.

Grade: `STATIC_CONFIRMED`.

### 2.2 Partial create/modify batches — ACCEPT, implementation detail MODIFY

Exact 1.5.9 `CreateElementsCommandBase::Execute` loops all items inside one `ACAPI_CallUndoableCommand`, records per-item errors, and returns `NoError` from the lambda. Therefore successful items can commit even when another item fails.

The current Safe BIM rule should be:

- preflight the complete risky batch;
- prefer one risky write item per command until `atomic:true` exists;
- classify any mixed result as `PARTIAL_APPLIED`;
- never blindly retry;
- record every durable created GUID before any compensation;
- verify compensation by absence readback.

For a future `atomic:true`, the Tapir response must distinguish `created`, `failed`, and `rolledBack`; stale GUIDs from rolled-back creates must never be treated as real.

Grade: `STATIC_CONFIRMED` for current partial-commit behaviour; post-PR atomic semantics require live/integration proof.

### 2.3 Morph edge type — ACCEPT

Official Archicad 29 API exposes `ACAPI_Element_ChangeMorphEdgeType(const API_Guid&, API_MorphEdgeTypeID)` and explicitly states that `ACAPI_Element_Change` does not provide that functionality. Therefore whole-Morph edge smoothing is an API capability and a small Tapir wrapper/patch is appropriate.

Limitation: this function changes **all** Morph edges; do not advertise arbitrary per-edge smoothing from this primitive.

Grade: `STATIC_CONFIRMED`.

### 2.4 Destructive Morph boolean — ACCEPT with strict lifecycle

Official Archicad 29 API exposes `ACAPI_Element_SolidOperation_Create`; it is a destructive operation between Morph/free-shape elements and deletes target/operator on success while returning result GUID(s).

Required Safe BIM contract:

- only when the user intent requires a destructive final freeform result;
- explicit GUID-replacing lifecycle;
- pre-capture properties/classifications/links that Safe BIM promises to replay;
- result readback + evaluated geometry proof;
- no silent use as a substitute for native BIM/Opening/associative SEO.

Grade: `STATIC_CONFIRMED` API capability; Tapir wrapper remains not implemented/live-proven.

### 2.5 Database-only execution primitive — ACCEPT with capability scoping

Arena correctly found that Tapir already contains `ExecuteActionForEachDatabase` and uses it for read commands. This is strong evidence that current-database switching without changing the Front Window is a valid internal pattern.

But do **not** expose a generic unrestricted `RunAnyCommandInDatabase`. Use:

- `GetExecutionContext`;
- optional `database` only on commands/types explicitly proven safe;
- a capability matrix with `front_window_required`, `current_database_required`, `floor_plan_required` flags;
- RAII restoration in C++ and verified `finally` restoration in Python.

Grade: `STATIC_CONFIRMED` primitive; write safety remains `UNRESOLVED_LIVE_REQUIRED` by element/command class.

### 2.6 `GetCollisions` — ACCEPT as candidate verification rung

Exact Tapir 1.5.9 exposes `GetCollisions`. Official Archicad API defines collision by intersection body volume/surface tolerance.

What is **not** documented strongly enough for promotion: whether associative SEO/Trim is reflected in the collision body used for the target. Therefore Arena's LT-C1 is mandatory before using “no collision after subtraction” as a PASS condition.

Grade: command/API existence `STATIC_CONFIRMED`; SEO semantics `UNRESOLVED_LIVE_REQUIRED`.

### 2.7 Profiles from scratch — ACCEPT

Exact Tapir 1.5.9 `CreateProfiles` source contains `newSkins` and allows a new Profile without `sourceAttributeId` on AC27+ when caller-supplied skin geometry is provided. This is not merely a 1.5.10-dev feature.

Safe BIM still needs polygon validity, material resolution, collision/name policy, readback canonicalisation, and a probe-element test.

Grade: `STATIC_CONFIRMED`; live builder behaviour needs LT-I2.

## 3. Corrections to specific Arena proposals

### 3.1 GOST/SPDS rule classification — Arena statement REJECTED

Arena's table says dimension placement offsets are “policy, not normative”. This is incorrect for the minimum spacing rules.

Normative minimums that belong in `RuleSet.normative_ref` include:

- first dimension line to contour: >= 10 mm on paper;
- parallel dimension lines: >= 7 mm on paper;
- avoid crossings of dimension/extension lines;
- construction-drawing tick rules from GOST R 21.101-2020.

Project/office policy may impose larger distances or preferred chain ordering, but it may not downgrade those minima to optional policy.

Implementation implication: dimension layout works in **paper space**, then converts through view scale to model-space offsets. Example: 10 mm at 1:100 = 1.0 m model offset, 7 mm = 0.7 m. The engine must then move farther outward when collision/legibility requires it.

### 3.2 Composite overwrite “in-use” preflight — Arena implementation REJECTED, goal ACCEPTED

Arena proposed checking `GetElementsByType` “filter by compositeId”. Stock Tapir's `GetElementsByType.filters` are fixed element-context filters, not arbitrary attribute predicates.

Safe stock path:

1. enumerate relevant element classes that can reference Composite;
2. request only the minimum detail fields needed to identify structure type and Composite GUID;
3. build an attribute-use index for the current job snapshot;
4. refuse overwrite if the target Composite GUID is in use unless the user explicitly approves a migration plan.

Future better path: a dedicated `GetAttributeUsage` C++ command if scanning proves expensive.

### 3.3 Morph replacement policy — MODIFY

Use delete+`CreateMorphs`+relink automatically only for:

- Safe-BIM-owned temporary Morphs;
- SEO operators/helpers whose lifecycle and dependencies are fully controlled;
- explicitly disposable test geometry.

For permanent/user Morphs:

- `ModifyMorphs(body)` remains disabled while closedness/functional consequences are unresolved;
- default result is `STOP_NEEDS_SAFE_MORPH_REWRITE`;
- GUID replacement requires explicit approval and a dependency capture/replay contract.

This preserves the user's rule that permanent BIM/Morph semantics are not destroyed merely to make automation easier.

### 3.4 Morph topology validator — MODIFY

Do not rely on a single `V-E+F = 2(1-g)` rule as the universal solid test. Multiple disconnected shells/components change the Euler characteristic. Required checks are primarily:

- every undirected manifold edge has exactly two incident face uses for a closed shell;
- opposite winding across paired edges;
- connected-component analysis;
- signed volume per closed connected shell;
- duplicate-coordinate and zero-length-edge rejection;
- face planarity where the target API requires planar polygons;
- self-intersection checks on generated/triangulated faces.

Euler characteristic is a consistency diagnostic per component, not the sole acceptance rule.

### 3.5 Shared asset architecture — MODIFY

Use three distinct stores, not one overloaded “library” abstraction:

1. **Shared linked local library** — GSM/library parts, auto-attached with `GetLibraries -> AddLibraries -> ReloadLibraries`.
2. **Shared module repository** — `.mod` native BIM assemblies, placed through Hotlinks.
3. **Safe BIM Favorites/template pack** — standard element/document settings, including creation-time font/style recipes.

This exactly serves both user intents: “object appears in later projects” and “repeated native BIM assembly remains native BIM”.

### 3.6 Font architecture — MODIFY

Favorites are a good immediate creation path, but are not a full font-resolution subsystem.

Keep both:

- NOW: Safe BIM-owned Favorites for deterministic creation, with snapshot/readback of `fontIndex`;
- P1 wrapper: `GetFonts` / `ResolveFontByName` so existing arbitrary project text can be audited by family name and missing fonts can fail closed.

### 3.7 Slab `Get3DBoundingBoxes` — ACCEPT risk, change test policy

Upstream issue #686 documents a hard crash path when `ACAPI_Element_CalcBounds` is used for a Slab not drawn in the current window. The user runs exact Tapir 1.5.9, so Safe BIM must blacklist this combination now.

Do not make a normal regression suite intentionally crash Archicad. Validate the blacklist in unit tests and remove it only after upgrading to a fixed Tapir build and running a positive non-crash test.

## 4. Verdict on Arena's 20 P0/P1/P2 recommendations

| Item | Counter-audit verdict | Required change |
|---|---|---|
| P0-1 Morph body closedness | **MODIFY** | Temporary/operator Morph may recreate; permanent Morph body edit stays fail-closed unless dependency-safe GUID replacement or in-place fix is proven. |
| P0-2 `rotationDegreesZ` | **ACCEPT** | Keep forbidden on affected Tapir; explicit basis axes are the durable path. |
| P0-3 SEO evaluated proof | **MODIFY** | Stock collision/quantity first, but they remain experimental until LT-C1/C2. |
| P0-4 partial batch writes | **MODIFY** | `PARTIAL_APPLIED` now; risky writes preferably one item/call; future `atomic:true` must have rollback-aware results. |
| P0-5 evidence integrity | **ACCEPT** | Raw request/response + SHA-256 manifest. |
| P1-6 Morph edge type | **ACCEPT** | Whole-Morph API, not per-edge promise. |
| P1-7 polygonal Opening | **ACCEPT + LIVE GATE** | API capability strong; stock Tapir 1.5.9 still rectangular wrapper. |
| P1-8 destructive Morph boolean | **ACCEPT** | Strict GUID-replacement lifecycle. |
| P1-9 native Shell | **ACCEPT** | Extruded/Revolved first; live after wrapper. |
| P1-10 per-edge Roof | **ACCEPT** | Native roof semantics preferred. |
| P1-11 section dimension existence | **ACCEPT+** | Target-DB existence plus `GetDimensionData`/semantic readback where available. |
| P1-12 background DB execution | **MODIFY** | Optional DB parameter only on proven-safe command/type pairs; no unrestricted runner. |
| P1-13 `EvaluateElements3D` | **ACCEPT** | Implement only after stock verification rungs are measured. |
| P1-14 font by name | **MODIFY** | Favorites now + `GetFonts/ResolveFontByName` for audit and portability. |
| P1-15 GOST engine | **ACCEPT WITH CORRECTION** | 10/7 mm and related rules are normative, not mere policy. |
| P1-16 shared library | **MODIFY** | `.mod`/Hotlink for assemblies; linked library/GSM remains separate required subsystem. |
| P2-17 capability negotiation | **ACCEPT -> P0** | Exact version + allowlist + behavioural quirks. |
| P2-18 caches | **ACCEPT for v1** | Per-job snapshots first; events later if profiling justifies. |
| P2-19 context grouping | **ACCEPT** | Planner-level scheduler, measured live. |
| P2-20 transactions/round-trips | **MODIFY** | `atomic:true` + safe batching + batched readback; no claim of transaction until rollback proven. |

## 5. Revised target architecture

```text
USER INTENT
   |
PLANNER / RULE ENGINE
   |-- GOST/SPDS RuleSet (normative_ref separated from policy)
   |-- ElementRecipe / ProfileBuilder / CompositeBuilder
   |-- Asset resolver (Attributes / Favorites / GSM Library / MOD Repository)
   |
CAPABILITY + SAFETY GATE
   |-- exact Tapir version handshake
   |-- command/parameter allowlist
   |-- sandbox token + project identity
   |-- command/type execution-context matrix
   |-- destructive/GUID-replacing lifecycle policy
   |
CONTEXT SCHEDULER
   |-- MODEL: floor-plan/current DB as required
   |-- DOCUMENT: section/elevation DB as required
   |-- VERIFY: stock collision/quantity, then ModelAccess only if needed
   |
WRITE EXECUTOR
   |-- preflight-all
   |-- atomic when proven, otherwise small/reconcilable writes
   |-- receipts + PARTIAL_APPLIED / UNKNOWN_OUTCOME states
   |
EVIDENCE LADDER
   1 typed readback / target DB existence
   2 analytic geometry checks
   3 GetCollisions (only after LT-C1)
   4 built-in quantity delta (only after LT-C2)
   5 EvaluateElements3D when required
   6 visual QA when useful
```

## 6. Live-test order after this counter-audit

The order is chosen to answer architectural gates before spending time on wrappers.

### Stage 0 — zero-write identity

**GPT-LT-00**

- `GetAddOnVersion` must be exactly 1.5.9.
- Verify sandbox project path and project identity.
- Record Front Window, stories, current project, available Building Materials/attributes required for tests.
- No writes.

STOP if identity is not exact.

### Stage 1 — stock Tapir verification gates

**GPT-LT-01 — SEO evaluated collision + quantity**

Fresh sandbox wall + simple closed Morph cutter. Measure `GetCollisions` and Volume before link, create subtraction link, rebuild as needed, measure again. This settles Arena LT-C1/C2 and decides whether verification rungs 3–4 are usable for SEO.

**GPT-LT-02 — explicit `floorIndex` without per-write `ChangeWindow`**

Keep another story/view displayed, create a harmless native element with explicit floorIndex, verify exact target story/database. Repeat only for representative classes; Window/Door stays floor-plan DB constrained.

**GPT-LT-03 — section dimension target database**

Create a dedicated test section, obtain raw section element IDs, create one associative chain while the section DB is current, verify GUID appears in `GetElementsByType(Dimension, databases=[sectionDb])`, then inspect `GetDimensionData`.

### Stage 2 — known-risk geometry behaviour

**GPT-LT-04 — Morph body replacement**

Use only a disposable Safe-BIM-owned Morph. Capture canonical body, `isClosed`, collision/volume proof; perform no-op body replacement; repeat proof. Do not run this on permanent user geometry.

**GPT-LT-05 — Morph create/recreate lineage**

Test the safe temporary/operator delete+recreate+SEO-relink path and prove link recreation plus evaluated effect if GPT-LT-01 established a verifier.

### Stage 3 — builders and documentation

**GPT-LT-06 — CompositeBuilder**

Create 3/5/7-skin test composites with exact BM GUIDs; verify skin order, thickness sum, separators, and a test wall. Include overwrite refusal when a composite is actually detected in use using the corrected usage-index method.

**GPT-LT-07 — ProfileBuilder**

Create rectangle/L/T/U/arc/hole profiles from `newSkins`; verify `GetProfiles` canonical geometry and create test Beam/Column/Wall as applicable.

**GPT-LT-08 — GOST dimension placement**

At 1:50 and 1:100 create plan dimension chains. Prove the first chain is >=10 mm paper-space from the contour and parallel chains >=7 mm paper-space; introduce a collision obstacle and verify the layout engine moves farther outward rather than violating the minimum. Also verify construction-drawing ticks/extension settings where the current Dimension API/Favorite exposes them; unsupported fields are `NOT_AUDITABLE`, not PASS.

**GPT-LT-09 — font/favorite round-trip**

Create text/label from Safe-BIM-owned Favorite, read fontIndex/height/pen; confirm deterministic creation. `GetFonts` remains a future wrapper for family-name audit.

### Stage 4 — reusable assets

**GPT-LT-10 — linked shared library across projects**

Attach a dedicated Safe BIM local library with `AddLibraries`; reload; open a second disposable PLN and prove auto-attach/availability without duplicate entries. This tests the user's original cross-project library requirement.

**GPT-LT-11 — `.mod` + Hotlink assembly**

Save a tiny native BIM assembly to `.mod`, create a Hotlink node/instance in another disposable project, verify constituent native BIM semantics and update path.

### Stage 5 — post-wrapper tests

Only after their C++ commands exist:

- Morph `ChangeMorphEdgeType`;
- polygonal/circular Opening;
- destructive Morph solid operation;
- `atomic:true` batch rollback;
- `GetExecutionContext` / guarded DB write parameter;
- `EvaluateElements3D`;
- per-edge Roof;
- Revolved/Extruded Shell;
- `GetFonts`.

### Explicitly NOT in the normal live sequence

Do **not** intentionally run the known Slab `Get3DBoundingBoxes` crash repro on the normal Archicad session. On exact 1.5.9 the command/type combination stays forbidden.

## 7. Stop condition for the next Arena cycle

Arena should now attack only the disputed/corrected items above rather than repeat the entire audit.

A static cycle is complete when:

- every counter-audit correction is ACCEPT/MODIFY/REJECT with exact source evidence;
- the GOST normative classification is reconciled;
- the invalid `GetElementsByType(compositeId)` usage check is replaced;
- permanent Morph lifecycle is explicitly safe;
- shared-library vs `.mod` responsibilities are unambiguous;
- no stock command is promoted to evaluated verifier before its live gate;
- all remaining uncertainty maps to an executable live test, not a prose question.

Then run one FINAL STATIC AUDIT. If it opens another source/design contradiction, reopen targeted passes. Otherwise the only remaining work should be the ordered live tests above.
