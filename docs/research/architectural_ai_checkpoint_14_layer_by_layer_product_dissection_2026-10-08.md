# Architectural AI checkpoint 14 — layer-by-layer product dissection and minimal-code AC29 stack

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first
Branch: feature/working-archicad-mvp

## Scope

This pass does not search for new product ideas. It dissects the already identified candidates and classifies every useful layer as:

- TAKE_AS_IS
- WRAP
- USE_METHOD
- BENCHMARK_ONLY
- DEFER_AC30
- KEEP_CUSTOM_GAP_ONLY
- DROP_FROM_ROADMAP

The active target remains Archicad 29. Archicad 30 findings are documented only to prevent dead-end architecture.

---

## Executive decision

For AC29, the current best minimal-code hypothesis is:

User / AI client
  -> HuskyBIM as primary broad Archicad execution candidate
  -> our native Add-On only for deep/event/transaction/read-back gaps
  -> dRofus if room/program/equipment evaluation passes
  -> Russian normative source federation
  -> deterministic Rule IR
  -> Design Healing-derived correction engine
  -> Solibri / IfcOpenShell / IDS as independent audit
  -> optional Archi Automate only for cross-tool/QGIS/IFC orchestration that HuskyBIM does not cover

Do not make Archi Automate the primary AC29 model writer before benchmarking: its published Archicad write surface is deliberately narrow.

Do not make SWAPP or Delta Flow runtime dependencies until a public/contractual integration path is proven.

Do not port Text2BIM wholesale. Extract the architecture and test methodology.

---

# 1. Graphisoft Public Archicad MCP

## What it actually is

Current Graphisoft Beta 2026 documentation exposes:
- built-in MCP for AI Assistant;
- Public MCP connection for compatible desktop AI tools;
- structured access to Archicad model/project data;
- Smart Find and Replace;
- property/attribute unification;
- command execution;
- bulk edits;
- confirmation where needed;
- single undoable batch for supported batch edits.

## Verified limitations

Current beta limitations include:
- unavailable in element Edit Mode;
- unavailable in Model Compare;
- some built-in properties unsupported;
- GDL parameters/properties unsupported;
- locked layers / Hotlinks / unreserved Teamwork elements protected;
- multiple element types cannot be filtered/modified, including several documentation/analysis entities.

## AC29 decision

DEFER_AC30.

Reason:
- current project target is AC29;
- official MCP is an AC30-era solution;
- it should not distort current implementation except through clean version-agnostic adapter boundaries.

## Roadmap effect

DROP from AC29 execution roadmap.
KEEP as AC30 migration target.

Our AC29 execution abstraction should make later replacement easy:
`ProjectSemanticOperation -> ArchicadExecutionAdapter`.

---

# 2. Nemetschek Creator

## What it appears to cover

Official current description:
- site analysis;
- concept design;
- AI-powered iterative exploration;
- performance evaluation;
- compliance;
- design intent;
- BIM data continuity;
- bidirectional workflow with Archicad.

## Decision

DEFER_AC30 / BENCHMARK_ONLY for now.

Reason:
- early-access/current-product timing is AC30-era;
- no reason to split the current AC29 target;
- potentially replaces a substantial part of future early-design candidate generation.

## Roadmap effect

Do not write a large proprietary early-design generator until Creator is tested after AC30 installation.

Keep only project-independent:
- project requirements model;
- Russian rules;
- candidate scoring;
- design-intent representation.

---

# 3. Archi Automate

## Strong layer

Archi Automate is stronger as a **cross-host MCP/control plane** than as an AC29 modeling engine.

Current published capabilities:
- one MCP surface across Archicad/Revit/Rhino/Grasshopper/IFC and additional hosts;
- GPT/Codex, Claude, Gemini and generic MCP clients;
- Hub;
- Guardrails;
- session discovery across hosts;
- QGIS and openBIM/IFC/IDS/BCF workflows;
- licensing/trial and deploy tooling.

## Critical finding: AC29 writer is deliberately narrow

Published Archicad command set currently describes:
- reads around Wall / Slab / Column / Object;
- create Wall / Column / Slab;
- move/copy;
- delete by GUID.

Writes apply directly in Allow-changes mode; published guidance explicitly says no preview step for Archicad writes.

This is far narrower than HuskyBIM's claimed Archicad API surface.

## Decision

WRAP / OPTIONAL.

Use if we need:
- one AI across multiple AEC hosts;
- QGIS -> Archicad context;
- IFC/IDS/BCF operations;
- one managed client connection;
- governance around heterogeneous tools.

Do NOT replace HuskyBIM/current deep AC29 executor with Archi Automate based only on its broad host list.

## Roadmap effect

DROP custom generic multi-host MCP gateway for now.
DEFER custom SBIM Control Center UI until after Archi Automate trial.
KEEP our project-specific preflight/state UI only if still needed.

---

# 4. HuskyBIM for Archicad 29

## Strong layer

Current official product pages claim broad AC29 API coverage:
- element queries/editing;
- geometry operations;
- layers/combinations;
- classifications;
- properties;
- stories;
- layouts/drawings;
- BCF/issues;
- attributes/materials/surfaces/composites/profiles;
- read/write workflows.

It is free and local on Windows.

## Documentation inconsistency discovered

Current HuskyBIM pages disagree on exact Archicad coverage:
- some current pages say 687 API operations;
- product/FAQ pages say 733 tools.

Therefore tool count is not trustworthy enough to architect around.

Required runtime test:
enumerate actual installed MCP tools and classify them by operation/domain.

## Client constraint

Current public workflow is centered on Claude Desktop and also mentions Cursor, VS Code and Windsurf.
Do not assume direct standard ChatGPT-local-MCP support without an explicit client path.

## Decision

TAKE_AS_IS as **primary AC29 execution candidate**, conditional on BIM-EXEC-01 benchmark.

## What our native Add-On keeps until disproven

KEEP_CUSTOM_GAP_ONLY:
- native element observer/change event stream;
- project revision and stale-transaction guard;
- deep Model Dump result geometry;
- faces/vertices/bodies;
- face-material provenance;
- exact host/relationship/memo reads;
- specialized writes HuskyBIM lacks;
- safe batch/undo semantics if HuskyBIM does not expose them;
- targeted read-back verifier;
- performance instrumentation.

## Roadmap effect

STOP adding generic CRUD writers until installed HuskyBIM capability diff is complete.

---

# 5. SWAPP / Frank

## What is clearly production-grade

Current public claims for Revit + Archicad:
- live BIM read/write;
- whole-floor modeling;
- 2D -> 3D;
- walls/doors/furniture/fixtures;
- dimensions/annotations;
- views/sheets;
- collision cleanup;
- QA;
- ADA checking/fixes;
- persistent firm workflow memory;
- corrections reused on later projects;
- human approval;
- traceable/reversible actions.

This is the closest production precedent for:
`firm standards -> workflow memory -> automatic BIM production`.

## Integration problem

No public general API/MCP/SDK has been verified in this pass.
Pricing is custom/credit-based.
The product is positioned as an enterprise operational platform.

## Decision

BENCHMARK_ONLY until a technical demo proves:
- programmatic integration;
- exportable workflow memory;
- Russian-rule integration;
- individual/student commercial viability.

If it is closed, do not architect SBIM around it.

## What to steal conceptually

USE_METHOD:
- corrections become reusable workflow memory;
- standards learned from reference projects;
- production action -> audit trail;
- review gates;
- re-running documentation after design revision.

## Roadmap effect

PAUSE custom "firm workflow memory" subsystem until SWAPP demo/audit.
If no open integration is possible, implement the minimum analogous layer ourselves.

---

# 6. Delta Flow

## Why it is important

Public architecture is very close to our whole-system concept:
- canonical DF-BIM model;
- project knowledge graph;
- site intelligence;
- design intent;
- generative design;
- code compliance;
- BIM operations;
- project intelligence;
- coordination/clash;
- quantities/cost;
- documentation;
- neuro-symbolic reasoning.

## What is NOT verified

No public evidence found in this pass for:
- Archicad integration;
- public API/MCP/SDK;
- Russian regulations;
- native editable PLN round-trip;
- event/invalidation semantics;
- transaction/rollback;
- rule-schema details;
- deployability/local mode.

## Decision

BENCHMARK_ONLY / DEMO_REQUIRED.

Do not take marketing architecture as proof of usable components.

## Roadmap effect

Use Delta Flow as a **whole-system benchmark**:
for every SBIM subsystem ask whether Delta Flow demonstrates a simpler architecture.

No runtime dependency until integration details exist.

---

# 7. Text2BIM — source-code audit

## Actual implemented architecture

Repository inspection confirms:

1. Product Owner agent receives user task.
2. PO can invoke an Architect/Floor Plan Designer agent.
3. Programmer/Coder agent receives a bounded set of BIM tools.
4. Coder generates Python that calls predefined BIM tools.
5. Code is executed inside Vectorworks.
6. Model is exported to IFC.
7. Solibri runs an external checker.
8. BCF issues are parsed.
9. Reviewer agent gets:
   - original generated code;
   - checker issues;
   - related element UUIDs;
   - available API/tool documentation.
10. Reviewer proposes patches; the loop can iterate.

The repository also maintains:
- session state;
- experiment logs;
- LLM-provider abstraction;
- tool descriptions;
- IFC/checking artifacts.

## Strong reusable concepts

USE_METHOD:
- separate design/planning and execution roles;
- bounded tool vocabulary;
- external independent checker;
- BCF as machine-readable correction evidence;
- reviewer receives exact offending element IDs;
- iterative correction loop;
- experiment logging.

## Weaknesses for our project

DO NOT PORT AS RUNTIME:
- Vectorworks-specific execution;
- generated Python execution is broader/riskier than our desired transactional command model;
- state is simple JSON/session state, not a causal project kernel;
- error recovery can leave previously executed side effects;
- architectural reasoning is prompt-driven rather than linked to a deep normative/project graph;
- Solibri loop requires IFC round-trip rather than live Archicad delta checking.

## Decision

USE_METHOD + SOURCE_REFERENCE.

Roadmap effect:
DROP custom invention of generic PO/Coder/Reviewer agent choreography.
ADAPT the proven pattern into:
`Planner -> deterministic/tool execution -> independent checker -> Repair Planner`.

---

# 8. Design Healing — method audit

## This is much closer to our intended correction engine than previously understood

The paper explicitly defines:
1. graph-based topological propagation from a compliance violation to related objects/design variables;
2. progressive/local scope: remain close to the violation first, expand scope only when no feasible solution exists;
3. screening-based sensitivity analysis (Morris method) to reduce the variable space;
4. prior-knowledge-conditioned design-space exploration;
5. conditioned Latin Hypercube sampling;
6. weighted Euclidean distance from the original design to rank low-disruption alternatives.

The authors treat the compliance checker as a black box and assume a parametric BIM model.

They explicitly cite parametric BIM authoring environments including Archicad as a suitable foundation.

## Decision

USE_METHOD as the baseline SBIM healing algorithm.

Do not invent a new search/healing strategy until this baseline is reproduced.

## SBIM adaptation

Replace simple weighted Euclidean distance with our richer lexicographic/project-disruption objective:
- legal/safety;
- functional invariants;
- architectural intent;
- structure/MEP/detail impact;
- spatial/topological change;
- cost/change radius;
- geometric displacement.

But retain the research pipeline:
`violation -> graph propagation -> sensitivity -> constrained exploration -> rank alternatives`.

## Roadmap effect

DROP vague custom "impact cone + candidate search algorithm" implementation.
Replace with **Design Healing-derived v1**, then extend only where benchmarks justify.

---

# 9. IFC-Agent — architecture audit

## Key reusable design

The 2026 paper provides:
- hierarchical main agent + specialized sub-agents;
- schema-guided dynamic tool composition;
- dual execution modes based on task size;
- small task: asynchronous fine-grained execution;
- large homogeneous task: sample a few entities -> infer reusable toolchain -> deterministic bulk execution;
- dual memory:
  - procedural reasoning/tool summaries;
  - entity semantic caches keyed by identifiers;
- incremental understanding without full upfront graph conversion.

## Decision

USE_METHOD, especially for performance.

## SBIM adaptation

For live Archicad:
- small heterogeneous change -> targeted deep reads/reasoning;
- large homogeneous batch -> sample/validate pattern -> deterministic batch execution;
- cache semantic facts by stable element ID/revision;
- avoid sending thousands of identical element records to LLM.

For IFC audit:
- use IFC-Agent pattern almost directly on IfcOpenShell data.

## Roadmap effect

DROP a naive "LLM reasons over every affected element" design.
KEEP compact deterministic graph/cache kernel.

---

# 10. CODE-COMPANION — Rule IR audit

## Most important lesson

The paper does NOT let LLM autonomously define final code rules.

Its published 18-rule pilot was manually interpreted and formalized.

Rules are represented through fields conceptually including:
- identifier;
- measurable variable;
- threshold/condition;
- unit;
- description;
- logical/executable expression;
- applicability;
- model data needed.

Execution is deterministic after formalization.

## Decision

USE_METHOD.

This validates our current normative compiler direction:
`source text -> draft normalization -> expert/verified rule -> deterministic Rule IR`.

## Roadmap effect

DROP any design where LLM-generated normative rules become ACTIVE automatically.

KEEP custom:
- Russian legal/applicability semantics;
- source versions/provenance;
- exception/reference logic;
- bindings to Archicad/project variables.

---

# 11. Building Information Graphs (BIGs)

## Relevant concepts

BIGs research argues for graph-native building information with explicit relationships enabling:
- change propagation;
- object-level version control;
- learning/generative applications.

## Decision

USE_SCHEMA_REFERENCE, not a full dependency yet.

Before freezing our graph schema:
- map our Entity/Dependency/Revision concepts against BIGs;
- reuse generic graph patterns and only add Russian/project semantics.

## Roadmap effect

PAUSE invention of a universal new building ontology.
Build only the relations needed for project reasoning.

---

# 12. What is now removed or reduced from our roadmap

## DROP / do not custom-build now

- generic MCP gateway for many AEC programs;
- generic Archicad CRUD wrapper;
- generic IFC parser;
- generic IDS validator;
- generic clash engine;
- generic solver;
- generic agent PO/Coder/Reviewer architecture;
- generic rule-check execution pipeline;
- generic compliance-healing search from scratch;
- generic LLM-per-element large-model reasoning;
- giant standalone early-design generator;
- giant universal BIM ontology.

## KEEP but shrink

### Native AC29 Add-On
From "our whole Archicad execution platform"
to:
"deep native gap layer + event/revision + verifier".

### Project engine
From "own everything"
to:
"canonical semantics + dependency/invalidation + transactions".

### Normative subsystem
From "own corpus + own search + own rules"
to:
"source federation + Russian applicability + Rule IR + project binding".

### AI orchestration
From "large custom multi-agent framework"
to:
"thin task router + known planning/review patterns".

---

# 13. Provisional AC29 component ownership

| Layer | Current owner candidate | SBIM custom code |
|---|---|---|
| Archicad broad CRUD/data | HuskyBIM | only proven gaps |
| Archicad deep result geometry/events | Native Add-On | yes |
| Cross-host MCP/QGIS/IFC | Archi Automate optional | project-specific policies only |
| Room/program/equipment | dRofus candidate | adapter + constraints |
| IFC parsing | IfcOpenShell | no parser |
| IFC QA | Solibri / IfcTester / IDS | project-specific rule selection |
| General compliance healing | Design Healing method | adapter/objective extensions |
| Rule execution | CODE-COMPANION pattern + solvers | Russian Rule IR/bindings |
| Large BIM query strategy | IFC-Agent method | adaptation/cache |
| Normative corpus | external/free/commercial sources | federation/provenance |
| Project causal semantics | BIGs + graph libs as reference | yes, narrow |
| Firm workflow memory | SWAPP benchmark | TBD after demo |
| Early design generation | existing products/research | scoring/requirements only |
| Whole-system reference | Delta Flow | no dependency yet |

---

# 14. What remains genuinely worth coding now

After this audit, the likely custom AC29 core is much smaller:

1. **Execution capability adapter**
   - normalize HuskyBIM/native Add-On results into one internal operation model.

2. **Native Gap Bridge**
   - events;
   - project revision;
   - targeted deep geometry;
   - exact read-back;
   - missing specialized writes.

3. **Canonical Project Kernel**
   - stable IDs;
   - selected semantic relationships;
   - revisioned derived facts;
   - Validity Envelopes.

4. **Russian Normative Adapter + Rule IR**
   - source federation;
   - applicability/version/legal semantics;
   - rule binding.

5. **Design Healing v1**
   - adapt published graph/sensitivity/exploration method;
   - plug in our disruption objective.

6. **Thin Router**
   - deterministic/local/cloud/escalation decision;
   - no full custom agent framework.

Everything else requires evidence before custom implementation.

---

# 15. Concrete next benchmark sequence

## TEST-AC29-01 — HuskyBIM capability enumeration
- install current AC29 build;
- enumerate actual tool list;
- resolve 687 vs 733 discrepancy;
- classify by element type + CRUD + documentation + attributes + relationships;
- inspect schemas and transport.

## BIM-EXEC-01 — apples-to-apples executor benchmark
Run the same operations via HuskyBIM and our native/Tapir stack:
- wall;
- hosted door/window;
- slab;
- roof;
- morph;
- materials/overrides;
- stories;
- properties/classifications;
- layouts/drawings;
- batch 100 elements;
- failure/rollback;
- exact read-back;
- performance.

Archi Automate joins only for the operations its published AC29 bridge supports.

## HEAL-01 — reproduce Design Healing baseline
One known spatial violation:
- map violation to graph;
- local propagation;
- sensitivity screening;
- constrained sample generation;
- compliance black-box;
- low-disruption ranking.

Compare against our current ad-hoc candidate logic.

## RULE-IR-01 — CODE-COMPANION-style rule
Take one already verified SP rule:
- source/provenance;
- variables;
- threshold/operator;
- applicability;
- model binding;
- deterministic evaluation;
- evidence output.

## AGENT-01 — Text2BIM/IFC-Agent-inspired workflow
- planner;
- bounded tools;
- execution;
- independent checker;
- reviewer/repair;
- entity cache;
- batch path for homogeneous operations.

No free-form generated code in the production transaction path.

---

# 16. Decision summary

### TAKE_AS_IS / primary candidate
- HuskyBIM for AC29 broad execution (pending benchmark)
- IfcOpenShell / Solibri / IDS components

### WRAP
- dRofus if evaluation passes
- Archi Automate only where cross-host orchestration adds value

### USE_METHOD
- Text2BIM agent/check/review loop
- Design Healing correction algorithm
- IFC-Agent adaptive execution + dual memory
- CODE-COMPANION deterministic Rule IR principle
- BIGs graph modeling concepts

### BENCHMARK_ONLY / no dependency yet
- SWAPP
- Delta Flow

### DEFER
- Graphisoft official MCP
- Nemetschek Creator
until AC30 is installed.

### KEEP_CUSTOM_GAP_ONLY
- native AC29 event/deep geometry/read-back layer
- Russian regulatory semantics
- canonical project causal kernel
- design-intent/project-disruption policy
- thin integration/router layer
