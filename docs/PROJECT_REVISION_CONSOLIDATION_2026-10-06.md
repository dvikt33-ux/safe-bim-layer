# Safe BIM project revision and consolidation — 2026-10-06

Status: **REVISION BASELINE — NO NEW BIM FUNCTIONALITY**

This document is the canonical cross-branch inventory for the current Safe BIM / Archicad project. Its purpose is to stop re-implementing capabilities that already exist in older generations of the repository.

## 1. Revision rule

Before any new Stage or BIM capability is implemented:

1. Check this report and `project_capability_migration_matrix.v1.json`.
2. Search the referenced canonical/legacy branch and evidence.
3. Reuse existing payload, read-back, safety and QA contracts whenever they are already proven.
4. Do not rewrite a stable capability merely to make the architecture cleaner.
5. A capability is promoted only by its strongest existing evidence:
   - `LIVE_VERIFIED`
   - `OFFLINE_VERIFIED`
   - `IMPLEMENTED_NOT_LIVE`
   - `RESEARCH_ONLY`
   - `PARTIAL`
   - `OBSOLETE`
   - `REJECTED`
6. `LIVE_VERIFIED` means actual Archicad/Tapir execution with factual read-back and/or required visual confirmation. Source inspection or mock tests alone do not qualify.

This revision branch contains documentation only. It does not change `main`, does not add Stage 5 and does not run Archicad mutations.

## 2. Generations that must be consolidated

The repository contains several useful generations that currently overlap.

### A. BIMEXEC / runtime safety generation

Important branches:
- `arena/t0-probes`
- `arena/runtime-safety-fix-ac01`
- `arena/runtime-hardening-v1`

Already contains real safety work that predates the current Closed Loop:
- T0 live transport/capability baseline;
- T2 wall connectivity live probe;
- T3 dependent Opening/owner-binding probe;
- T4 timeout-after-apply and read-only reconciliation;
- T5 process-kill after dispatch and restart reconciliation;
- T6 external model-drift fail-closed behavior;
- T7/T8/T9 negative/recovery/duplicate-delivery verification;
- durable attempt/checkpoint/runtime state;
- UNKNOWN_OUTCOME handling;
- no blind retry;
- execution lease;
- read-back before DONE.

**Consolidation rule:** Stage 4 must regression-check these behaviors; it must not reinvent them.

### B. Safe BIM house/runtime generation

Important branch:
- `arena/fix-house-offline-audit-f7d38af`

Implemented primitives include:
- `create_wall_loop`
- `create_basic_slab`
- `insert_window`
- `insert_door`
- `create_room`
- resumable `test_house.py` / `continue_test_house.py`

A two-storey 10x8 m house scenario is encoded with exterior walls, slabs and windows. Individual primitives have later live evidence in other branches. A single published receipt proving the complete house as one end-to-end LIVE PASS has not been located in this revision, so the whole-house scenario remains **IMPLEMENTED_NOT_LIVE as an integrated scenario**, not LIVE_VERIFIED.

### C. broad Archicad capability / research generation

Important branches:
- `research/archicad-full-capability-audit-20260928`
- `archicad-capability-registry`
- `research/library-system-v3`

Recorded live/reviewed capabilities include Window, Door, Slab, Roof, Zone, Column, Beam, Mesh, Morph, Opening, Object/Lamp/Text/Label, 2D elements, SEO links, attributes and library mechanisms.

The capability registry at head `bdd38ef457ac1c56990f026aefecf14f623de4f8` explicitly promotes only capabilities that were exercised against Archicad/Tapir. Two canonical smoke scripts are especially important:
- `tests/smoke/native_window_door_continuous_wall.py`
- `tests/smoke/basic_slab_favorite.py`

The registry also records VERIFIED profile/Beam, curved Beam, SEO and Door library-part behavior; their migration must preserve provenance and should locate/attach the original live evidence before being promoted inside the modern Closed Loop.

### D. Working Archicad MVP generation

Important branch:
- `feature/working-archicad-mvp`, head `565ea2e0414a14bedbca09999690d7b97f877fa3`

This is more capable than the current chat adapter exposes.

`scripts/archicad_executor.py` already supports:
- `create_wall`
- `create_window`
- `create_slab`
- `create_roof`
- `create_morph`
- `change_wall_material`
- `delete`

The branch also contains six geometry-derived write cycles:
- Wall create/joint
- Wall material write
- Hosted Window
- Slab
- Roof create/read-back/delete
- Morph create/read-back/delete

Its README records PASS for all of the above except a known single-plane Roof surface-override blocker. The thin Russian chat adapter exposes only a subset, which is why later discussions incorrectly treated several executor capabilities as missing.

**Consolidation rule:** the executor is a source of proven typed recipes; the modern orchestrator should wrap/migrate them instead of re-discovering their Tapir schemas.

### E. Bridge / ChatGPT transport generation

Important branches:
- `prototype/s2.4-archicad-context-provider-20260929`
- `feature/gpt-direct-bridge-20261002`
- `feature/chat-bridge-wall-write-mvp`
- `feature/gpt-mailbox-write-path-20261005`

S2.4 records `GITHUB_ARCHICAD_E2E_LIVE_VERIFIED` for:
`GitHub CONTEXT_REQUEST -> SafeBIMBridge -> Archicad 29/Tapir -> CONTEXT_READY -> GitHub readback`.

It includes real selected-element capture, restart/dedup behavior, privacy filtering and fail-closed malformed-request handling.

Later branches add:
- zero-setup host/bootstrap;
- typed remote JOBs;
- one-job-per-tick semantics;
- project/instance binding;
- stale-source read before mutation;
- typed Wall write;
- factual read-back;
- UNKNOWN_OUTCOME/no retry after timeout or restart.

**Consolidation rule:** do not build another independent transport unless a concrete missing requirement is demonstrated. Modern Closed Loop should consume the already-tested bridge semantics or explicitly replace them with equivalent regression evidence.

### F. current Closed Loop generation

Important verified branches:
- Stage 1 v0 regression: `work/stage1-v0-regression`, commit `27fc10267e71d1cd4f8322fe1d3c334e2cef1b4c`
- Stage 2 skeleton: `work/stage2-orchestrator-skeleton`, completion `d6ed3b071c1e7d17b8d819377e1984c80dd9ed33`
- Stage 3 live wall closed loop: `work/stage3-live-wall-closed-loop`, commit `2674e1ebd7656fb306bcff294d8d17174be78a`
- Audit Pack completion: `work/audit-pack-fix`, commit `03c64733bb2b4f59970f5247a3ed89e1236f3090`

This generation provides the best orchestration contract:
`OBSERVE -> PLAN -> EXECUTE -> READ_BACK -> AUDIT -> REPLAN -> VERIFIED`.

It should become the **integration shell**, not the sole source of BIM capability implementations.

Stage 4 local implementation was reported at local commit `f297572` with 128/128 offline tests, but it is not present in GitHub at the time of this revision. The live environment blocker has since been cleared by a successful preflight on `NativeGeometry_Full_Test_20261004.pln`. Stage 4 therefore remains **NOT VERIFIED until mandatory live scenarios are run and evidence is published**.

### G. design / planning generation

Important branch:
- `work/planning-engine-v0`, head `8881c46c`

The following producer chain is already implemented offline:

`Stage 0 Intake -> Functional Program -> Design Intent -> Site Context -> Project Constraint Input -> Project Normative Bundle -> Constraint Compilation -> Planning Engine v0`.

Planning Engine v0 creates actual XY room rectangles in metres, assigns spaces to floors, resolves overlaps/circulation, checks supported hard constraints, scores preferences and independently re-audits the chosen candidate. Its documented test suite covers 70+ scenarios.

A reproducible two-storey synthetic house example exists in:
`examples/planning_house_v0.py`
with source data in:
`docs/examples/planning_engine_v0/house-inputs.json`.

Important boundary:
- the planning mechanism is real;
- the demo normative library is synthetic;
- it is not proof of Russian SP/GOST compliance;
- Archicad translation is not implemented in this branch.

**Primary architectural gap:** `Planning Engine -> BIM Translator -> typed Closed Loop operations`.

## 3. Canonical capability summary

### LIVE_VERIFIED / proven live building blocks

Use/migrate, do not redesign:

- Wall create/continuation and joint verification.
- Hosted native Window in a Wall.
- Hosted native Door in a Wall.
- Basic Slab using verified Favorite.
- Roof native creation/read-back (simple creation path; complex canonical gable acceptance remains separate).
- Morph creation/read-back.
- Zone creation/read-back.
- Column and Beam creation/read-back.
- Profile Beam and horizontally curved Beam behaviors.
- Mesh creation/read-back.
- Rectangular Opening creation/owner binding; detailed Opening read-back remains limited.
- Solid Element Operation links/subtraction workflow.
- Wall material/surface modification workflow.
- exact GUID Delete cleanup/restoration workflow.
- native Object/Lamp/Text/Label and common 2D element creation in broad live capability runs.
- Story/elevation placement semantics.
- selected-element context capture through the GitHub bridge.
- BIMEXEC timeout/process-kill/model-drift reconciliation behaviors.

### OFFLINE_VERIFIED / ready to wire to live evidence

- Stage 0 intake/data-gap gate.
- Functional Program.
- Design Intent.
- Site Context.
- Project Constraint Input.
- Project Normative Bundle mechanism.
- Constraint Compilation.
- Planning Engine v0.
- BIM QA native-element / story / fragmentation rules.
- Geometry QA for roof gaps/collisions, wall tops and rafters.
- Coordination QA for roof-wall coverage, wall connectivity, vertical support, opening conflicts/clearances and masonry modular fit.
- Stage 2 orchestrator stale/no-progress logic.
- Audit Pack verification/tamper/sanitization logic.

### IMPLEMENTED_NOT_LIVE as an integrated modern path

- complete old two-storey `test_house.py` scenario as one current end-to-end run;
- modern Closed Loop execution for Window/Door/Slab/Roof/Morph/Zone;
- Planning Engine candidate translated into native BIM and closed-loop audited;
- real Russian normative bundle feeding the planner end-to-end;
- whole modern ChatGPT -> planner -> BIM translator -> Closed Loop -> Archicad -> QA -> correction cycle.

### PARTIAL / specific remaining engineering

- canonical simple gable Roof geometry with a modern acceptance gate;
- Wall-to-Roof trim/crop;
- rafter generation from accepted Roof geometry;
- complex roof intersections;
- full typed Edit/Move/Modify abstraction beyond existing per-type modify recipes;
- generalized typed Delete policy beyond exact controlled GUID cases;
- robust custom Library Part authoring/placement pipeline and evidence consolidation;
- profile/composite/material builders as modern orchestrated capabilities;
- Opening detailed geometry verification while Tapir read-back is limited;
- real production geometry collectors for existing offline QA modules.

### REJECTED patterns that must not return

- fragmented Walls used to fake Window/Door openings;
- Morph windows as normal hosted building windows;
- stepped Wall stacks used to fake gables;
- unverified overlapping Roof planes;
- rafters generated independently from accepted Roof geometry;
- blind retry after ambiguous write outcome;
- using planner prediction as factual post-write evidence.

## 4. Duplicate work found

The revision found the following major duplication risks:

1. **Stage 4 vs BIMEXEC T4/T5/T6/T8/T9**
   - Modern implementation is valid, but the behaviors were already exercised in older live fault tests.
   - Action: import old scenarios as regression/reference evidence; do not invent different semantics without a documented reason.

2. **Future Window/Door work vs existing live smoke tests**
   - Native host placement, sizes, host preservation and read-back already exist.
   - Action: migration only.

3. **Future Slab work vs Basic Slab Favorite smoke + Working MVP cycle**
   - Creation/read-back/material/elevation semantics already exist.
   - Action: migration only.

4. **Future Roof research vs Working MVP Roof cycle + W4 research**
   - Native creation/read-back exists.
   - Action: focus only on canonical gable topology/QA and modern orchestration.

5. **Future Morph work vs Working MVP + broad W7 research**
   - Do not restart arbitrary-body research.
   - Action: migrate only when a real product use-case needs Morph.

6. **Future Edit/Delete/material work vs `archicad_executor.py`**
   - Existing controlled paths already exist.
   - Action: generalize from proven implementations instead of starting blank.

7. **Future “house planner” vs `work/planning-engine-v0`**
   - Functional/program/site/constraint planning pipeline already exists.
   - Action: build the missing translator and connect real normative inputs.

8. **Future ChatGPT/Archicad transport vs S2.4/direct bridge**
   - Read context and typed job transport already exist.
   - Action: reuse or formally supersede.

## 5. Canonical target architecture after consolidation

```text
USER / CHATGPT
    |
    v
STAGE 0 INTAKE / DATA GAPS
    |
    v
FUNCTIONAL PROGRAM + DESIGN INTENT + SITE CONTEXT
    |
    v
PROJECT NORMATIVE BUNDLE
    |
    v
CONSTRAINT COMPILATION
    |
    v
PLANNING ENGINE
    |
    v
BIM TRANSLATOR                 <-- principal missing integration layer
    |
    v
CLOSED LOOP ORCHESTRATOR       <-- current canonical orchestration shell
    |
    +--> migrated typed BIM recipes
    |      Wall / Window / Door / Slab / Roof / Zone / ...
    |
    v
SAFE MUTATION / RUNTIME
    |
    v
ARCHICAD / TAPIR
    |
    v
FACTUAL READ-BACK
    |
    v
BIM + GEOMETRY + COORDINATION QA
    |
    +--> FAIL -> REPLAN / CORRECT
    |
    v
VERIFIED
```

## 6. Revised roadmap

### R0 — consolidation
Status: **THIS REVISION**

- maintain this report and machine matrix;
- no new BIM operation;
- every future stage must cite an existing capability or explicitly state that none exists.

### R1 — finish Stage 4 by regression, not reinvention

- publish/localize current Stage 4 implementation;
- run only mandatory live scenarios;
- compare semantics to T4/T5/T6/T8/T9;
- produce Audit Pack;
- Stage 4 VERIFIED only after live evidence.

### R2 — migrate the existing house primitives into Closed Loop

Preferred first bundle:
- Window + Door
- Slab
- Zone
- existing Delete/material paths where needed

Each operation gets:
- typed request schema;
- modern planner adapter;
- immediate pre-write state check;
- factual read-back;
- auditor;
- old evidence/reference links;
- one minimal live regression.

Do not re-research Tapir schemas unless the old recipe fails on the pinned current environment.

### R3 — BIM Translator v0

Translate a VERIFIED rectangular Planning Engine candidate into a typed BIM plan:
- floors/stories;
- room rectangles -> wall graph;
- exterior/internal wall roles;
- slabs;
- Zones;
- opening intents;
- deterministic IDs/provenance;
- no direct Archicad mutation from the translator.

Output must be a closed-loop executable plan, not factual BIM state.

### R4 — first end-to-end simple house

Target:
`brief -> planning -> BIM translator -> walls/slabs/zones/windows/doors -> readback -> QA -> VERIFIED`.

Roof may be excluded from the very first integration acceptance if the gable gate is not yet VERIFIED; if excluded, status must explicitly say `HOUSE_SHELL_WITHOUT_VERIFIED_ROOF`, not DONE.

### R5 — canonical simple gable Roof + Wall trim

Only after base house integration:
- two native Roof planes;
- one accepted ridge;
- no gap/overlap;
- wall coverage;
- wall trim/crop;
- geometry QA.

### R6 — real normative planning integration

Feed only production VERIFIED rules from the real project normative library into the existing Project Normative Bundle / Constraint Compilation mechanism. Do not replace the planner's synthetic fixture by merely renaming it; production rule provenance must meet the normative source contract.

## 7. Current practical conclusion

The project is not short of isolated capability code. The immediate engineering problem is **fragmentation of proven work across branches and generations**.

For a simple-house assistant, the highest-value next work is therefore:
1. complete Stage 4 live acceptance;
2. migrate existing BIM recipes into the modern Closed Loop;
3. implement the Planning Engine -> BIM Translator boundary;
4. connect existing QA and real normative inputs.

Any task that begins with “research how to create Window/Door/Slab/Roof in Tapir” should now be treated as a likely regression in project knowledge and must first consult the migration matrix.
