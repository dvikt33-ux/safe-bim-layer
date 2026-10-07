# Architectural AI checkpoint 16 — best-of-breed component harvesting

Date: 2026-10-08  
Status: ACTIVE RESEARCH CHECKPOINT  
Target: Archicad 29 first  
Branch: feature/working-archicad-mvp

## 0. Research rule changed

No candidate is discarded merely because another candidate currently looks stronger.

From this checkpoint onward every project/product is decomposed into reusable layers:

- execution surface;
- transport / MCP exposure;
- tool discovery / schema handling;
- write safety / approval / transactions;
- geometry and model representation;
- event / revision semantics;
- agent orchestration;
- memory;
- normative-rule representation;
- compliance checking;
- healing / optimization;
- documentation production policy;
- cross-host coordination;
- IFC / IDS / BCF;
- visualization / provenance;
- graph / design-intent representation.

The goal is not to choose one monolithic platform.

The goal is to construct an SBIM stack from the strongest component at each layer, while
keeping providers replaceable behind capability interfaces.

Mandatory rule:

> A product may be rejected as a runtime dependency without rejecting its architecture,
> algorithm, workflow, schema, safety pattern, or benchmark value.

---

## 1. Updated top-level direction

### HuskyBIM remains Husky First for AC29 execution research

HuskyBIM stays the first proprietary Archicad 29 executor to investigate deeply because
its claimed command surface is large enough that exact disagreement between 500/600/700+
tools is not strategically important.

However "Husky First" means:

- benchmark it first as the broad execution provider;
- enumerate the actual MCP manifest after installation;
- map each command to semantic capability;
- measure read/write/read-back, safety, undo, batch and performance;
- retain Tapir/native/open wrappers as independent reference and fallback layers.

It does NOT mean:

- Husky owns the canonical project state;
- Husky owns Russian normative logic;
- Husky becomes the only executable backend;
- open alternatives are abandoned before deep audit.

---

## 2. Component harvest map

### 2.1 HuskyBIM — primary AC29 execution candidate

Harvest target:

- broad native Archicad element read/write;
- attributes / layers / classifications / properties;
- stories;
- layouts / drawings;
- BCF / issues;
- MEP where verified;
- IFC where verified;
- documentation primitives and compound workflows;
- deep geometry if its actual MCP schema proves sufficient;
- native JSON command escape-hatch where documented.

Do NOT let Husky become the single source of truth.

Keep outside Husky:

- canonical state/revision;
- verified Russian Rule IR;
- design-intent graph;
- long-lived provider-independent operation ledger;
- independent read-back verification for high-risk writes.

Architecture role:

`PRIMARY_EXECUTION_PROVIDER`.

---

### 2.2 Tapir — open execution reference, verifier and fallback

Tapir remains critical even if Husky wins most execution benchmarks.

Harvest:

- inspectable C++ implementation;
- exact schemas;
- broad AC29 write coverage;
- element notifications;
- per-command Archicad undo scopes;
- resolved floor-plan cut polygons;
- rich type-specific element details;
- Morph body round-trip;
- documentation primitives;
- reproducible test oracle for Husky results;
- fallback path where Husky has regressions or opaque behavior.

Architecture role:

`OPEN_REFERENCE_EXECUTOR + VERIFICATION_ORACLE + FALLBACK`.

Do not treat Husky and Tapir as mutually exclusive.

---

### 2.3 SzamosiMate/tapir-archicad-MCP — generated MCP surface

Harvest:

- generation of MCP tools from authoritative schemas;
- Pydantic runtime validation;
- progressive command discovery;
- exact schema lookup on demand;
- multi-instance support;
- stdio / SSE / Streamable HTTP;
- bearer-token transport;
- job handles.

This is a strong answer to the "hundreds of tools in model context" problem.

Architecture role:

`SCHEMA_TO_TOOL_COMPILER + MCP_DISCOVERY_REFERENCE`.

---

### 2.4 Boti-Ormandi/archicad-mcp — compact discovery pattern

Harvest only the method:

- very small stable MCP surface;
- discover commands first;
- inspect exact schema only when needed;
- compose multi-step work after discovery.

Reject for trusted production mutation:

- unsandboxed free-form Python execution.

Architecture role:

`PROGRESSIVE_DISCOVERY_PATTERN`.

---

### 2.5 alesdev88/Archicad-MCP — safety / QA wrapper patterns

Harvest:

- dry-run by default;
- explicit confirmation for destructive writes;
- planned changeset;
- one-shot expiring changeset;
- project identity binding before apply;
- post-write read-back mismatch reporting;
- YAML QA rule layer;
- whole-plan coverage awareness.

Important limitation:

- changesets are not automatically all-or-none atomic;
- partial successful writes can survive later failure;
- optional script mode is unsandboxed;
- documented AC29 property-reading crash risk must remain visible.

Architecture role:

`SAFETY_ENVELOPE_REFERENCE`.

---

## 3. Archi Automate — do not reduce it to "weak Archicad writer"

Deep audit changed its role.

Current official docs describe a standard MCP stdio server compatible with Claude,
OpenAI Codex, Cursor, VS Code, Windsurf, Gemini and other MCP clients.

Archicad 27/28/29 write surface is deliberately curated and smaller than Husky/Tapir:

- read Wall / Slab / Column / Object;
- create Wall / Column / Slab;
- move / copy;
- delete by GUID.

Archicad writes have no native preview/dry-run in this product and apply directly in
Allow-changes mode.

That makes Archi Automate a weak candidate for PRIMARY AC29 CRUD, but a very strong
candidate for other layers.

### Harvest from Archi Automate

#### Cross-host MCP control plane

One MCP server namespaces and routes:

- Archicad;
- Revit;
- Rhino;
- Grasshopper;
- AutoCAD;
- Tekla;
- Vectorworks;
- SketchUp;
- Blender;
- QGIS;
- IFC;
- Forma;
- Autodesk Construction Cloud.

This is much more valuable than reproducing a multi-host gateway ourselves.

#### Governance pattern

- reads open by default;
- writes policy-gated;
- central Hub;
- guardrails configured independently of prompts;
- audit of actions;
- separate capability gate for dangerous script-authoring surfaces.

Especially valuable pattern from Grasshopper:

- code/script authoring separated from ordinary write permission;
- write requires hash of previously read code;
- stale concurrent edits are rejected.

This hash-bound write contract should influence SBIM operation preconditions.

#### IFC / IDS / BCF layer

Archi Automate already exposes:

- IFC2x3 / IFC4 / IFC4x1 / IFC4x3;
- multi-model federation;
- IFC read/query/write and save;
- IFC visual snapshot;
- COBie export;
- glTF export;
- IDS validation;
- EXPRESS/schema health check;
- bSDD search;
- IDS authoring;
- BCF read/write;
- IDS/clash -> BCF issue generation;
- clash detection;
- QTO;
- classification authoring;
- embodied-carbon estimation.

We should not build generic equivalents before testing this layer.

#### Scene Contract

A portable normalized scene is shared between IFC, Revit, Rhino and Forma.

This is potentially useful as:

- cross-host geometry contract;
- visualization/simulation payload;
- lower-fidelity transport beside our semantic Canonical Project Kernel.

Do not confuse it with the canonical BIM kernel until schema depth is inspected.

#### Provenance patterns

The image-generation subsystem records:

- source hash;
- camera;
- source image;
- provider/model;
- prompt;
- cost;
- elapsed time;
- watermark/provenance.

This is a useful pattern for our operation/evidence ledger even though the feature itself
is not core BIM execution.

Architecture role:

`CROSS_HOST_CONTROL_PLANE + OPENBIM_SERVICE_LAYER + GOVERNANCE_REFERENCE`.

---

## 4. SWAPP / Frank — harvest production intelligence, not low-level API

SWAPP now exposes a clearer architecture than the earlier pass suggested.

### Confirmed public strengths

- live read/write in Revit and Archicad;
- model whole floors;
- 2D -> 3D;
- dimension/tag/callout production;
- views and sheets;
- collision resolution;
- QA and validation;
- accessibility checking and proposed/fixed changes;
- change reflow across documentation;
- audit trail and approval;
- firm-specific standards.

### Most valuable finding: five memory classes

SWAPP publicly describes:

1. Firm memory
   - annotation standards;
   - dimensioning rules;
   - QA logic;
   - graphic conventions;
   - BIM policies.

2. Project memory
   - project exceptions;
   - PM/client requirements;
   - coordination context.

3. User memory
   - preferred workflows;
   - repeated approvals;
   - interaction habits.

4. Workflow memory
   - successful execution sequences;
   - corrections;
   - what worked last time.

5. Lifecycle memory
   - RFIs;
   - clash history;
   - constructability;
   - operational outcomes feeding back into design.

This is substantially better than one generic "memory" bucket.

### Harvest into SBIM

Adopt a provider-independent equivalent:

`Memory = Firm + Project + User + Workflow + Lifecycle`

plus IFC-Agent's entity cache as a sixth technical cache, not human knowledge memory.

SWAPP also provides a useful distinction:

- deterministic/repeatable execution and firm standards;
- AI for orchestration;
- human approval before execution;
- corrections become reusable workflow knowledge.

### Documentation intelligence to benchmark

SWAPP's value is not CreateDimension/CreateLayout primitives.
It is the policy above them:

- identify what needs dimensions;
- dimension coverage QA;
- detect missing/indirect/redundant/conflicting dimensioning;
- generate enlarged plans/callouts/elevations;
- organize complete sheet sets;
- resolve annotation overlap;
- propagate changes through the document set;
- validate output against firm guidelines.

Architecture role:

`PRODUCTION_POLICY + FIRM_MEMORY BENCHMARK`.

Do not abandon it merely because no public SDK/MCP is available.

---

## 5. Text2BIM — harvest stateful agent choreography and patch feedback

Repository:
https://github.com/dcy0577/Text2BIM

The code confirms several reusable implementation patterns.

### Agent sequence

- Product Owner expands the brief;
- Architect/floor-plan designer produces spatial intent;
- Coder translates intent into bounded BIM tool usage;
- BIM model exports to IFC;
- external Solibri checker evaluates it;
- BCF issues identify problems and related GUIDs;
- Reviewer interprets issues;
- Coder produces a patch.

### Important implementation detail: patch, not rewrite

The checking loop explicitly instructs the Coder to generate an executable patch and
not rewrite the original model-generation code.

This is very aligned with our minimal-disruption philosophy.

Harvest:

`model -> independent checker -> issue IR/BCF -> reviewer -> bounded patch -> recheck`

### Stateful execution

The workflow stores agent state in a JSON file between iterations.

Useful concept:

- persistent structured execution context independent of chat transcript.

Do not copy raw state format blindly; map it into our Canonical Kernel / operation
ledger.

### Experiment logging

The repository records:

- model/provider;
- task;
- round;
- issue-fixing iteration;
- issue count/types;
- generated file;
- phase.

Harvest this as a benchmark/evaluation ledger.

### Runtime rejection remains

The custom persistent Python interpreter is broader than a safe semantic-command
runtime. It parses AST but supports many Python constructs and imports.

Do not use generated Python as the trusted AC29 mutation layer.

Architecture role:

`AGENT_CHOREOGRAPHY + CHECKER_PATCH_LOOP + EXPERIMENT_LEDGER`.

---

## 6. IFC-Agent — harvest scale-aware reasoning and technical memory

Paper:
DOI 10.1016/j.autcon.2026.106888

### Adaptive dual-mode execution

Mode I:
- small / heterogeneous tasks;
- multiple agents;
- asynchronous detailed reasoning.

Mode II:
- large / homogeneous entity sets;
- explore representative samples;
- infer reusable toolchain;
- ObserverAgent generalizes it;
- deterministic batch execution for the remaining entities.

This should become a core SBIM execution policy:

`reason on samples -> compile plan -> deterministic batch`

rather than LLM-per-element execution.

### Dual technical memory

1. Procedural memory
   - tool traces;
   - timestamps;
   - summaries;
   - reusable prior task results.

2. Semantic entity caches
   - stable entity IDs;
   - parsed entity structures;
   - cross-agent reuse.

Combine this with SWAPP, but keep categories distinct:

- SWAPP memory = organizational/domain knowledge;
- IFC-Agent cache = computational reuse.

Architecture role:

`SCALE_AWARE_AGENT_EXECUTION + PROCEDURAL_CACHE + ENTITY_CACHE`.

---

## 7. Design Healing — harvest actual code structures, not only paper algorithm

Repository:
https://github.com/Jaaaaabin/DesignHealingWu

The public source confirms the paper is backed by executable experimental code, not
only a conceptual diagram.

### GraphNeighbor implementation

The code represents classes such as:

- wall;
- space;
- parameter;
- failure;
- failure-neighbor.

It searches from a failed location through:

`failure/space -> belonging wall -> propagated neighboring space -> associated parameter`

with restrictions based on:

- object properties;
- wall length;
- connection counts;
- fixed/align/total-area constraints.

This gives us a concrete model for an impact cone that respects constraint semantics.

### Constraint preservation

The implementation distinguishes active/passive parameters and can create equality /
offset constraints between parameters rather than blindly moving every connected wall.

Harvest:

- neighborhood propagation;
- constrained scope;
- active/passive design variables;
- constraint-aware parameter sets.

### Search / ranking

The code includes:

- Morris sensitivity results;
- LHS exploration;
- weighted Euclidean distance;
- explicit filtering to compliant alternatives.

Our extension remains:

weighted disruption cost should include:

1. life safety / mandatory rules;
2. function;
3. design intent;
4. structural/MEP/document dependencies;
5. graph radius;
6. cost/time;
7. geometric deviation.

Architecture role:

`HEALING_SEARCH_BASELINE + IMPACT_CONE_REFERENCE`.

---

## 8. CODE-COMPANION — harvest Rule IR validation discipline

The 2026 paper is valuable not because of its 18 rules but because of its boundary
between legal interpretation and software execution.

Rule representation contains:

- rule identifier;
- measurable variable;
- comparison operator;
- threshold/condition;
- unit;
- applicability;
- explanatory output;
- required model information.

Before implementation, each clause is classified as:

- deterministic;
- conditionally deterministic;
- interpretation-dependent.

The published 18 rules were manually interpreted and validated; no LLM generated them.

Harvest:

### Rule lifecycle

`SOURCE -> INTERPRETATION_DRAFT -> VERIFIED_RULE -> ACTIVE_EXECUTABLE_RULE`

Never:

`LLM extraction -> immediate PASS/FAIL engine`.

### Required trace fields

Add to our Rule IR:

- source/version;
- clause;
- applicability;
- variable;
- operator;
- threshold/condition;
- unit;
- exceptions/dependencies;
- required model evidence;
- computability class;
- validation status;
- executable function reference.

Architecture role:

`RULE_IR + HUMAN_VALIDATION_BOUNDARY`.

---

## 9. BIGs — strongest current reference for Canonical Project Graph

Paper:
Building Information Graphs (BIGs), Wang & Sacks, 2025.

### Structure

Each discipline is a subgraph:

`G_arch / G_struct / G_mep / ...`

A meta-graph links objects between disciplines.

This is better than flattening every object into one undifferentiated graph.

### Objectified relationships

A cross-discipline relation can become a node with properties such as:

- condition;
- operator;
- status.

This is highly relevant to design intent.

Instead of only:

`Wall --HOSTS--> Column`

we can represent:

`Wall -> ConstraintNode -> Column`

where ConstraintNode holds:

- relationship type;
- expected condition;
- tolerance;
- origin/source;
- active/inactive state;
- severity;
- owner discipline.

### Change propagation

BIGs explicitly uses links to determine what a changed object affects across disciplines.

This should feed directly into our:

- impact cone;
- invalidation;
- healing scope;
- coordination warnings.

### Object-level version control

The paper describes:

- incremental object change detection;
- transmitting only changed objects/relations;
- branches;
- merge;
- design variants/history.

This is a much better conceptual base for our revision kernel than a global integer
revision alone.

Harvest target:

`ProjectRevision = object deltas + relation deltas + provenance + branch/operation id`

A simple monotonically increasing revision may remain as a fast stale guard, but the
canonical history should be object-level.

Architecture role:

`CANONICAL_PROJECT_GRAPH + DESIGN_INTENT + OBJECT_LEVEL_VERSIONING`.

---

## 10. Delta Flow — retain as architecture benchmark

Public material still does not expose enough implementation detail to adopt runtime
components safely.

But its product architecture remains highly relevant:

- canonical building model (DF-BIM);
- project knowledge graph;
- design intent;
- site intelligence;
- code and standards;
- coordination/clash;
- quantities/cost;
- documentation;
- neuro-symbolic reasoning.

The important benchmark is the product boundary:

`canonical model + symbolic constraints + probabilistic interpretation`

rather than a pure LLM assistant or pure rule engine.

Architecture role:

`END_TO_END_NEURO_SYMBOLIC_PRODUCT_BENCHMARK`.

Do not remove from research registry.

---

## 11. New composite architecture hypothesis

The best current design is no longer "build SBIM around one executor".

It is:

### A. Planner / reasoning

Use:
- Text2BIM role separation;
- IFC-Agent adaptive execution;
- schema-guided progressive tool discovery.

### B. Organizational memory

Use SWAPP-style:
- Firm;
- Project;
- User;
- Workflow;
- Lifecycle.

### C. Computational cache

Use IFC-Agent:
- procedural cache;
- entity cache.

### D. Canonical Project Kernel

Use BIGs:
- discipline subgraphs;
- meta-graph;
- objectified constraints;
- object-level version/diff.

### E. Rule IR

Use CODE-COMPANION:
- validated deterministic/conditional rule representation;
- human-controlled activation.

### F. Healing

Use Design Healing:
- graph propagation;
- constraints;
- sensitivity;
- conditioned sampling;
- compliance black box;
- minimum-disruption ranking.

### G. AC29 execution providers

Priority research order:

1. HuskyBIM — broad primary provider candidate.
2. Tapir — open verifier/fallback/reference.
3. Graphisoft official JSON — underlying standard calls where useful.
4. residual native Add-On — only proven missing semantics.

### H. MCP exposure

Candidate combination:

- Szamosi schema-generated tools;
- Boti progressive discovery method;
- bounded semantic command layer for high-risk writes.

### I. Safety

Combine:

- Archi Automate system-level guardrails;
- alesdev dry-run/changeset/project binding;
- Tapir per-command Undo;
- our stale-state/idempotency/operation ledger;
- read-back verification.

### J. Cross-host/openBIM

Prefer testing Archi Automate for:

- multi-host routing;
- IFC;
- IDS;
- BCF;
- bSDD;
- clash;
- QTO;
- Scene Contract;
- visualization.

Do not custom-build equivalents before capability audit.

### K. Documentation intelligence

Use:

- Husky/Tapir for primitive execution;
- SWAPP as policy/memory benchmark;
- our own firm/project policy only where no reusable implementation exists.

---

## 12. New decision vocabulary

The old matrix used actions such as STOP or BENCHMARK_ONLY too aggressively.

Replace them with component-level statuses:

- `PRIMARY_PROVIDER_CANDIDATE`
- `SECONDARY_PROVIDER_CANDIDATE`
- `FALLBACK_PROVIDER`
- `HARVEST_RUNTIME`
- `HARVEST_ARCHITECTURE`
- `HARVEST_ALGORITHM`
- `HARVEST_SCHEMA`
- `HARVEST_SAFETY_PATTERN`
- `HARVEST_MEMORY_PATTERN`
- `BENCHMARK_PRODUCTION_POLICY`
- `FUTURE_VERSION_CANDIDATE`
- `REJECT_ONLY_SPECIFIC_RUNTIME_MECHANISM`

A candidate is removed from the registry only after:

1. deep source/docs inspection where possible;
2. explicit overlap analysis;
3. license/runtime feasibility analysis;
4. evidence that it contributes no unique reusable component.

---

## 13. Immediate deep-research queue

### HUSKY-DEEP-01
Enumerate every real MCP tool after installation and classify by layer.

### HUSKY-GEOM-01
Compare Husky geometry output field-for-field against Model Dump v1.

### HUSKY-TXN-01
Test:
- multi-element batch;
- partial failure;
- undo;
- duplicate retry;
- read-back;
- active database/window;
- stale target.

### HUSKY-DOC-01
Test:
- views;
- sections;
- exterior/interior elevations;
- dimensions;
- layouts;
- drawings;
- schedules;
- publisher;
- associative behavior after model change.

### HUSKY-COMPLEX-01
Deep element types:
- Curtain Wall;
- Stair;
- Railing;
- Object/GDL;
- MEP;
- Hotlink;
- Opening.

### OPENSTACK-DEEP-01
Continue exact comparison:
- Tapir;
- Szamosi;
- alesdev;
- Boti;
- chronista.

### ARCHI-AUTOMATE-DEEP-01
Inspect:
- actual tool schemas;
- Scene Contract schema;
- guardrail policy model;
- IFC/IDS/BCF output shapes;
- host-session routing.

### SWAPP-DEEP-01
Mine:
- public skill catalog;
- documentation QA categories;
- workflow-memory behavior;
- Archicad-specific demos;
- approval/audit semantics.

### GRAPH-KERNEL-01
Prototype schema merging:
- BIGs subgraphs/meta-graph;
- Design Healing failure/parameter graph;
- Rule IR constraint nodes;
- project operation/version nodes.

### MEMORY-01
Define separate stores for:
- Firm;
- Project;
- User;
- Workflow;
- Lifecycle;
- Procedural;
- Entity cache.

---

## 14. Core conclusion

The project should not become "our replacement for Husky", "our replacement for
Tapir", or "our replacement for SWAPP".

It should become the **composition layer that can use the strongest parts of all of
them**:

- Husky for breadth;
- Tapir for transparency and fallback;
- Archi Automate for cross-host/openBIM/governance;
- SWAPP for production intelligence and memory architecture;
- Text2BIM for checker-driven patch choreography;
- IFC-Agent for scalable reasoning;
- Design Healing for minimum-disruption correction;
- CODE-COMPANION for verified Rule IR;
- BIGs for the canonical graph and object-level version semantics;
- Delta Flow as the neuro-symbolic end-state benchmark.

That is now the governing research direction.
