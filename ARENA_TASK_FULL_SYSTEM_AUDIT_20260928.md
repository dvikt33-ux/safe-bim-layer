# Arena task — independent full-system audit of Safe BIM / Archicad architecture

Date: 2026-09-28
Repository: `dvikt33-ux/safe-bim-layer`
Target branch: `research/archicad-full-capability-audit-20260928`

## Mission

Perform an **independent adversarial audit** of the accumulated Safe BIM research, live-test evidence, Tapir 1.5.9 behavior, proposed Archicad 29 architecture, GOST/SPDS documentation engine, attribute/profile/composite strategy, shared-library architecture, execution acceleration strategy, and next live-test matrix.

Do not assume the proposed design is correct merely because it is documented here. If a proposed solution is weak, unnecessarily complicated, unsafe, slow, or based on a false premise, reject it and propose a better design.

The expected outcome is not a friendly summary. The expected outcome is a defensible engineering decision record with unresolved questions driven to zero or explicitly marked as requiring live Archicad evidence.

---

# Required source set

Read the complete target branch, especially:

- `research/ARCHICAD_CAPABILITY_LEDGER_20260928.md`
- `research/ARCHICAD_EXECUTION_ARCHITECTURE_20260928.md`
- `research/GOST_ATTRIBUTES_PROFILES_LIBRARY_20260928.md`
- `research/NEXT_LIVE_TEST_MATRIX_20260928.md`
- `LIVE_TEST_SUMMARY_R0_R4.md`
- `W7_ARBITRARY_MORPH_GEOMETRY.md`
- `W8_TRIM_AND_SOLID_SUBTRACTION.md`
- `ARENA_TASK_ARCHITECTURE_AUDIT.md`
- current implementation code under the repository
- tests and CI configuration

Also inspect exact Tapir 1.5.9 source where claims depend on wrapper behavior. Baseline source investigated by ChatGPT research: `ENZYME-APD/tapir-archicad-automation` at commit/tag baseline `b1dc828b3a47309e52d003578cbefb13371bd46a`.

Where necessary, verify against official Graphisoft Archicad 29 API documentation rather than secondary articles.

---

# Non-negotiable evidence policy

Maintain explicit labels:

- `LIVE_CONFIRMED`
- `STATIC_CONFIRMED`
- `INFERRED`
- `UNRESOLVED_LIVE_REQUIRED`
- `CONTRADICTED`

Never promote:

- API request success -> element exists;
- returned GUID -> durable real element;
- SEO link -> evaluated cut geometry;
- AABB overlap -> solid intersection;
- source/API capability -> Tapir wrapper capability;
- Tapir wrapper capability -> live Archicad behavior;
- mock test -> live Archicad proof.

Every major conclusion must identify its evidence grade.

---

# Required working method

Use repeated cycles exactly in this spirit:

```text
AUDIT
-> targeted passes / experiments / source inspections
-> AUDIT of what changed / what remains uncertain
-> more targeted passes
-> repeat until no material question remains
-> FINAL AUDIT
-> if Final Audit finds a new question, reopen another audit/pass cycle
```

Do **not** stop after a fixed number of passes merely because a quota was reached.

For each cycle:

1. list concrete questions/risks;
2. design the smallest pass that can answer each question;
3. execute static/source/test analysis available to Arena;
4. distinguish questions that cannot be resolved without a real Archicad 29 process;
5. update the architecture/recommendation based on findings;
6. run a new audit on the updated result.

Stop only when:

- no unresolved static/source/design question remains;
- remaining uncertainty is strictly live-runtime evidence that Arena cannot produce;
- every proposed major component has a reason, failure model, and verification strategy.

---

# Audit domains

## A. Existing Safe BIM safety architecture

Audit:

- choke points for writes;
- direct `TapirClient.call` bypass paths;
- qwen integration bypasses;
- `bimexec` separation;
- version gates;
- transaction/partial-write behavior;
- project identity guards;
- sandbox assumptions;
- raw evidence integrity;
- undo/rollback claims;
- fail-closed dependency resolution;
- attribute/material resolution.

Determine whether the current design actually enforces policy or merely documents it.

Propose a better enforcement architecture if needed.

---

## B. Morph subsystem

Audit all known findings:

- arbitrary body creation;
- open Surface/Wire semantics;
- holes/material/per-face Surface;
- large mesh stress;
- vertex ID renumbering;
- `ModifyMorphs(body=...)` closedness defect;
- `rotationDegreesZ` defect;
- edge smoothing limitation;
- transformation-only ModifyMorphs behavior;
- BIM->Morph lifecycle policy.

Questions Arena must answer:

1. Is the proposed workaround architecture correct?
2. Should body editing be fixed in Tapir, bypassed with a dedicated C++ command, or replaced by delete/recreate under controlled lifecycle?
3. What exact validation should precede/follow Morph body writes?
4. Is explicit basis-axis rotation the correct long-term abstraction or should Tapir fix `rotationDegreesZ` and expose pivot semantics explicitly?
5. What wrapper should expose Morph edge types safely?

---

## C. Solid modeling / SEO / Opening

Audit:

- associative SEO mapping and lifecycle;
- `Subtraction`, directional subtraction, Intersection, Addition;
- relation readback vs evaluated geometry;
- figured Wall-Morph cut investigation and why it is not currently PASS;
- destructive Morph solid operations;
- native Opening strategy;
- current stock Tapir `CreateOpenings` limitation to width/height caller input;
- proposed polygon/circular Opening extension.

Arena must propose the cleanest decision tree for:

```text
architectural hole
3D associative trim
freeform boolean result
temporary construction/operator geometry
```

Evaluate whether ChatGPT's proposed hierarchy (native Opening -> SEO -> destructive Morph boolean) is correct or should be changed.

Define the minimum evaluated-geometry verifier required before Safe BIM can call a boolean result PASS.

---

## D. Native BIM semantics

Audit whether Safe BIM is choosing the strongest native element type for:

- Wall / Slab / Beam / Column;
- Roof;
- Shell;
- Opening;
- Complex Profile;
- Composite;
- Object/Library Part;
- Morph.

Pay special attention to:

- one-GUID native multi-plane gable roof;
- missing per-edge roof wrapper data;
- native Revolved Shell vs Morph revolve;
- when Morph is truly preferable.

Reject any Morph fallback that unnecessarily destroys BIM semantics.

---

## E. Plan / Section / Elevation / 3D execution architecture

Audit the proposed dual-context model:

```text
Front Window != Current Database
```

and the proposed commands:

- `GetExecutionContext`
- `RunInDatabase`
- context scheduler
- generated DB prewarm
- batch rebuild
- owner resolution from Section/Elevation generated elements.

Questions:

1. Does this actually reduce expensive UI/view switching?
2. What Archicad API restrictions could invalidate background database writes?
3. Which operations must use the Front Window rather than only Current Database?
4. How should nested context changes restore safely after exceptions?
5. How should database identity be represented durably?

Audit section/elevation dimension presets and ghost-GUID risk.

---

## F. Off-screen 3D / geometry verification

Audit proposed hierarchy:

```text
readback -> AABB -> Quantity -> ModelAccess -> visible 3D
```

Evaluate:

- whether Quantity is a valid fast verifier for each target element type;
- ModelAccess isolation/temporary sight approach;
- selected-component generation;
- connection table use;
- performance risks;
- response-size risks;
- stale-model/rebuild risks;
- database/view dependencies.

Propose a precise `EvaluateElements3D` contract.

---

## G. Performance / acceleration

Audit all proposed performance improvements:

- batch/undoable command scope;
- preflight-all then write;
- fail-fast batch;
- minimal rebuilds;
- context grouping;
- fewer JSON round-trips;
- story/attribute/library/cache strategy;
- event-driven invalidation;
- runtime capability handshake.

For each, state:

- expected benefit;
- correctness risk;
- likely complexity;
- what must be measured live;
- whether there is a simpler alternative.

Propose benchmark methodology, preferably median/p95 rather than one-off times.

---

## H. GOST/SPDS documentation engine

Audit the proposed standards architecture rather than accepting any hard-coded style.

Review:

- font resolution by name;
- Pen Tables;
- Line Type attributes;
- Saved View pen set / dimension style;
- associative dimensions;
- section/elevation semantic witness presets;
- paper-space offset conversion;
- collision avoidance;
- compliance audit.

Required output:

1. distinguish normative requirements from project/university policy;
2. identify which rules should be parameterized;
3. identify which rules can be verified automatically;
4. identify which rules depend on final plotted scale/view state;
5. propose a robust `GostComplianceAudit` architecture.

Do not invent GOST requirements. If normative certainty requires source verification, mark it explicitly.

---

## I. Attributes / Complex Profiles / Composites

Audit:

- `CreateProfiles` source/copy/newSkins/replaceSkins paths;
- arbitrary polygon/arc/hole/multi-skin profile authoring;
- crash-prone/internal edge slots;
- Wall/Beam/Column applicability flags;
- `CreateComposites` skins/separators;
- Building Material dependency policy;
- Composite physical thickness semantics;
- Profile/Composite readback and downstream element rebuild.

Arena must propose contracts for:

- `ProfileBuilder`
- `CompositeBuilder`
- `ElementRecipe`

with exact preflight and postcondition checks.

---

## J. Shared library across projects

Audit exact Tapir 1.5.9 library commands and the proposed architecture:

```text
shared local folder
-> auto-attach on Project Open/New
-> manifest/versioning
-> reload
-> stable Library Part identity
```

Confirm or reject:

- Embedded Library is not sufficient for cross-project reuse;
- linked Local Library is the correct basic mechanism;
- auto-attach add-on behavior is appropriate;
- runtime library-part index is not durable identity.

Design `SaveSelectionAsSharedLibraryObject` or a better alternative.

Consider:

- GSM/API path;
- dependencies/macros;
- subtype handling;
- compatibility/versioning;
- overwriting an object already used by projects;
- Teamwork/server library future implications.

---

## K. Arrays / replication / figures of revolution

Audit proposed high-level array engine based on copy + transforms:

- linear;
- grid;
- radial;
- path;
- 3D path;
- rising Z;
- lateral offset;
- tangent orientation.

Audit native Revolved Shell wrapper vs Morph revolve fallback.

Propose the most BIM-semantic implementation for architecture work.

---

# Tests and CI audit

Run all repository tests available to Arena and inspect CI.

Do not report "all tests pass" without stating whether they are:

- unit/mock;
- integration without Archicad;
- live Archicad.

Identify missing regression tests for every confirmed bug:

- Morph closedness after body replacement;
- `rotationDegreesZ`;
- edge type write;
- ghost GUID existence;
- Composite thickness semantics;
- partial-write batch behavior;
- invalid Building Material dependency;
- database/context restoration;
- library duplicate attach;
- GOST role resolution.

---

# Required independent solutions

For every P0/P1 problem, Arena must provide:

```text
Problem
Current ChatGPT proposal
Arena verdict: ACCEPT / MODIFY / REJECT
Arena alternative
Why it is safer/faster/simpler
Required implementation changes
Required tests
Remaining live evidence
```

Arena is explicitly encouraged to replace our design when it has a better one.

---

# Required final artifacts

Create a new audit branch; do not modify `main`.

Produce at least:

1. `ARENA_FULL_SYSTEM_AUDIT_20260928.md`
   - executive findings;
   - confirmed contradictions;
   - risk register;
   - recommended target architecture;
   - accepted/rejected ChatGPT proposals.

2. `ARENA_CAPABILITY_MATRIX_20260928.md`
   - feature;
   - Archicad API capability;
   - Tapir wrapper capability;
   - Safe BIM capability;
   - evidence grade;
   - known bug;
   - next proof.

3. `ARENA_LIVE_TEST_PLAN_20260928.md`
   - minimal ordered live suite;
   - exact evidence gates;
   - stop conditions;
   - expected destructive/non-destructive behavior.

4. `ARENA_IMPLEMENTATION_PLAN_20260928.md`
   - prioritized wrapper/code changes;
   - dependency order;
   - expected performance impact;
   - tests required before enabling each feature.

If further cycle artifacts are necessary, add them rather than compressing unresolved reasoning into the final report.

---

# Restrictions

- Do not modify `main`.
- Do not claim live Archicad evidence if Arena did not run a real Archicad process.
- Do not delete or overwrite existing evidence files.
- Do not treat mock tests as live proof.
- Do not weaken fail-closed policies merely for convenience.
- Do not preserve a ChatGPT proposal solely for consistency; correctness wins.
- Do not perform destructive live operations on a non-disposable project.

---

# Completion criterion

The audit is complete only after the final audit can answer **all static/design/source questions without material uncertainty**.

Any question that truly requires live Archicad must be reduced to a precise executable experiment with:

- setup;
- exact action;
- readback/evaluated proof;
- failure interpretation;
- cleanup/persistence policy;
- evidence grade that will result.

If the final audit finds a new static/design question, reopen the audit/pass cycle and continue until it is resolved.