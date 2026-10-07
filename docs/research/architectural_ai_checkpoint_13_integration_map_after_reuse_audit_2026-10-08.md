# Architectural AI checkpoint 13 — integration map after whole-system reuse audit

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp

## Why this checkpoint exists

The previous research found that many components we assumed were custom work already exist.
This pass went one level higher:

- what entire AEC/AI platforms already overlap with SBIM;
- which products can be connected rather than recreated;
- what changed in the market literally in October 2026;
- what a minimal-custom-code SBIM stack could look like;
- which remaining gaps are actually worth owning.

## Correction / accountability

Earlier project research was too implementation-first and too narrow.

Some of the late discoveries were avoidable:
- HuskyBIM existed before this audit;
- SWAPP has been in production for years;
- Text2BIM / Design Healing / BIM change-propagation research existed before our recent implementation work.

Some discoveries are genuinely brand new:
- Graphisoft publicly marked Archicad MCP as delivered on 2026-10-07;
- Graphisoft announced the 2026 product portfolio on 2026-10-07;
- Nemetschek Creator early access is scheduled for late October 2026;
- CODE-COMPANION was published in September 2026;
- several current AEC MCP products expanded substantially during summer 2026.

The process failure is therefore real, but not every missed component had been available for months.

## Major new discovery: Graphisoft itself is now building the stack

### Official Archicad MCP

Graphisoft's 2026 product line now includes:
- Agentic AI Assistant;
- Public Archicad MCP Server;
- bulk model edits;
- structured project/model access;
- guided review / confirmation / batch execution / single undo workflows.

Graphisoft's beta documentation describes:
- Smart Find and Replace;
- property/attribute unification;
- natural-language command execution;
- review before execution;
- single-batch apply;
- one-step undo.

Important limitation:
current public availability is tied to **Archicad 30 Collaborate / Max**.
Archicad 29 gets AI Assistant but not the new Public MCP package in the published availability matrix.

This means our current AC29 bridge can become a **transitional compatibility layer**, not necessarily a permanent core.

### Nemetschek Creator

Graphisoft/Nemetschek now describes Creator as:
- cloud-native early-stage design intelligence;
- site context;
- AI iterative design;
- design intent;
- feasibility;
- sustainability/performance;
- compliance;
- bidirectional Archicad workflow;
- continuous intent/data connection into BIM.

Early access: October 2026; mature commercial release planned for 2027.

This overlaps strongly with our:
- L0 Project Compiler front end;
- site/context reasoning;
- early candidate generation;
- performance evaluation;
- design-intent persistence.

### Open Collaboration Platform (OCP)

Graphisoft's Design Intelligence strategy describes an open collaboration fabric that will:
- synchronize models, documents, issues and decisions;
- support open standards;
- use object-based exchange rather than file-passing;
- expose open APIs;
- add intelligent issue management and automated clash detection;
- use agentic AI to identify/prevent problems.

This overlaps with:
- our project-state/control-plane ideas;
- issue graph;
- collaboration/version layer;
- some change-impact monitoring.

## Production/live-BIM options

### 1. Official Graphisoft MCP (AC30)
Best future "native" candidate.

Pros:
- first-party;
- built around Archicad transaction/undo semantics;
- no reverse engineering;
- likely best long-term compatibility.

Cons/current gaps:
- AC30/plan requirement;
- beta;
- documented unsupported properties/element types;
- no Russian normative graph;
- no project-wide design-healing brain.

### 2. HuskyBIM (AC29)
Current free AI-facing tool layer.

Strengths:
- broad ready-made tool surface;
- active AC29 support;
- free;
- local connector;
- CRUD/query/documentation workflows.

Risks:
- public tool counts change rapidly across pages/releases;
- currently positioned around Claude desktop;
- must benchmark deep geometry, transactions, eventing and batch semantics.

Role:
**immediate AC29 benchmark / possible commodity execution layer**.

### 3. Archi Automate (AC29 + many hosts)
Current commercial MCP/control plane.

Strengths:
- Archicad 29;
- Revit/Rhino/Grasshopper/AutoCAD/Tekla/Vectorworks/SketchUp/Blender/QGIS/IFC/Forma/ACC;
- one MCP surface;
- GPT/Codex + Claude + Gemini clients;
- governance modes;
- action history;
- QGIS/site context;
- IFC/IDS/BCF workflows;
- one installer/Hub.

Current published individual price is low enough for serious testing (roughly $17.40/month, with annual discounts), plus a 14-day trial.

Role:
**highest-priority test for replacing our proposed custom SBIM Control Center + multi-host MCP glue**.

### 4. Community/open Archicad MCPs
Several current projects already provide:
- official JSON API access;
- Tapir wrappers;
- dynamically generated tools;
- safety modes;
- command discovery;
- QA from YAML;
- ChatGPT/Codex/Claude connectivity.

These are valuable as:
- implementation references;
- fallbacks;
- free adapters;
- test harnesses.

Do not build another generic MCP wrapper from zero unless a proven gap remains.

## Production "AI architect" candidate: SWAPP / Frank

Public 2026 capabilities:
- reads/writes live Revit and Archicad;
- models whole floors;
- agentic 2D -> 3D;
- dimensions/annotations;
- creates views/sheets;
- collision cleanup;
- QA/validation;
- ADA checks with proposed fixes;
- firm-specific workflow memory;
- learns corrections over time;
- traceable/reversible actions.

SWAPP states production use since 2019 and large-scale delivered documentation.

This overlaps heavily with:
- our "teach AI how our office works" idea;
- documentation automation;
- QA;
- modeling;
- project memory;
- iterative revision support.

Unknown / must audit:
- public API;
- external MCP integration;
- Russian regulations;
- custom normative feeds;
- whether its workflow memory can be exported/queried;
- pricing/availability for individual/student use;
- deep Archicad command scope.

Decision:
**P0 product/demo audit before writing our own documentation-learning/workflow-memory layer.**

## Near-whole-system conceptual candidate: Delta Flow

Public architecture is almost a direct SBIM analogue:
- site intelligence;
- generative design;
- code compliance;
- DF-BIM;
- project intelligence;
- project knowledge graph;
- design intent;
- coordination/clash;
- quantities/cost;
- documentation;
- neuro-symbolic reasoning.

Potentially this is the closest "someone already built our concept" candidate.

But public evidence is not enough to adopt it.

Must verify:
- product maturity;
- Archicad support;
- API;
- native/editable BIM round-trip;
- Russian codes;
- knowledge-graph semantics;
- event/incremental model;
- transaction safety;
- pricing/access;
- data ownership/export.

Decision:
**P0 demo/technical audit, but no architectural dependency yet.**

## Early-design alternatives

### Nemetschek Creator
Best strategic fit for an Archicad-first stack because of explicit bidirectional Archicad integration and design-intent continuity.

### Snaptrude 3.0
Current modular AI agents already perform:
- site analysis;
- code/standards research with citations;
- program generation;
- room dimensions;
- storey assignment;
- layout generation;
- downstream propagation when a part of the workflow changes.

Important conceptual overlap:
Snaptrude explicitly frames its system around connected project context and downstream updates rather than isolated AI answers.

Role:
reference architecture / possible early-design tool; weaker direct Archicad fit than Creator.

### Hypar
Strong program/site/space-layout candidate generator; integrates dRofus, Revit, Rhino.

### TestFit
Strong feasibility/site/candidate engine and now exposes MCP; direct Revit workflow.

### Finch
Generative/design-option engine; Archicad route currently through Grasshopper.

## Compliance options

### Russian normative source federation
Still project-specific:
- Стройкомплекс.РФ;
- protect.gost.ru;
- Minstroy;
- pravo;
- spatial state data;
- optional TechExpert/NormaCS/GARANT.

### UptoCode
Current product can:
- read IFC + PDF together;
- accept arbitrary user-supplied regulation documents;
- output clause-cited findings;
- check geometry/properties across fire/accessibility/light/waterproofing/etc.

Potential role:
**independent multimodal compliance auditor for Russian codes that we legally supply**, even without native Russian corpus support.

This may let us avoid building some generic PDF+IFC reasoning/audit infrastructure.

### Solibri
Now provides:
- mature parameterized model-checking;
- custom rules;
- IDS;
- Cloud Checking API;
- BCF output;
- developer platform;
- AI assistant beta.

Potential role:
**deterministic / independent QA executor**.

Do not write our own generic IFC clash/checking service before exhausting Solibri + IfcOpenShell.

### Kestrel
Strong precedent for BIM-native jurisdiction-specific code checking, currently Revit/US-oriented.

Role:
architecture/UX reference, not immediate Russian/Archicad dependency.

## Research already covering "unique" SBIM algorithms

### Text2BIM
Natural language -> multi-agent design -> editable BIM -> rule checker -> iterative repair.

### Design Healing
Compliance violation -> graph propagation -> relevant objects -> design-space alternatives -> compliant result -> minimum-change ranking.

This strongly overlaps our impact-cone + candidate-healing concept.

### IFC-Agent
Schema-guided multi-agent IFC reasoning:
- dynamic tool composition;
- adaptive execution by task scale;
- dual memory;
- sampled exploration + aggregation to avoid token explosion.

This overlaps our deep/light execution architecture.

### CODE-COMPANION
Natural-language regulations -> structured rules -> deterministic BIM checks.

This overlaps our Rule IR compiler.

### BIGs / graph-native BIM research
Explicit graph relationships, change propagation, object-level version control.

This overlaps our Project Causal Graph.

Therefore:
**we should reproduce/borrow known algorithms before inventing our own variants.**

## Minimal-code architecture — current best hypothesis

### CURRENT AC29 stack

User
  -> ChatGPT / chosen AI client
  -> Archi Automate OR HuskyBIM (benchmark both)
  -> Archicad 29

Parallel project services:
  -> dRofus for program/room/equipment requirements (if licensing fits)
  -> Russian Norm Source Adapters
  -> existing graph/solver libraries
  -> Solibri / IfcOpenShell / UptoCode for independent checking
  -> optional QGIS/FPPD for spatial constraints

Our code:
  -> canonical project/requirement IDs
  -> Russian legal/applicability logic
  -> Rule IR bindings
  -> design-intent bridge
  -> cross-system transaction/impact state
  -> only missing Archicad deep/event operations

### FUTURE AC30+ stack

User
  -> AI client
  -> Official Archicad MCP
  -> Archicad 30

Early design:
  -> Nemetschek Creator

Collaboration/state:
  -> OCP / existing CDE/BCF infrastructure

Independent audit:
  -> Solibri / IFC / compliance tools

Our custom scope may shrink mostly to:
- Russian regulatory semantics;
- canonical project graph across systems;
- design-healing/ranking policy;
- source federation;
- specialized project decisions.

## Most important technical choice now

Do **not** decide between HuskyBIM, Archi Automate, official Archicad MCP, SWAPP and our Add-On from feature lists.

Build one shared acceptance benchmark:

### BIM-EXEC-01
On the same AC29 test project:
1. create wall;
2. create hosted window/door;
3. copy slab/story;
4. modify materials/face overrides;
5. edit properties/classifications;
6. batch edit 100 elements;
7. undo as one action;
8. read back exact geometry/data;
9. measure latency/payload;
10. test failure rollback;
11. test multi-story/hidden elements;
12. test documentation/views/sheets;
13. test project close/open safety;
14. verify no unintended model fragmentation.

Run through:
- HuskyBIM;
- Archi Automate;
- best open MCP wrapper;
- our native Add-On/Tapir path.

For AC30 later:
- add official Graphisoft MCP.

Whichever passes becomes commodity execution.

## New search rule: no "absence" claim without an evidence matrix

Before saying "this does not exist", record:
- commercial search;
- vendor/ecosystem search;
- open-source search;
- academic search;
- current-year announcement search;
- adjacent-industry search.

Then classify:
- FOUND_PRODUCTION;
- FOUND_BETA;
- FOUND_RESEARCH_METHOD;
- FOUND_PARTIAL;
- NOT_FOUND_AFTER_AUDIT.

Never use plain "doesn't exist" for major project capabilities again.

## Immediate next research

P0:
1. Archi Automate AC29 technical tool list / trial.
2. HuskyBIM AC29 technical tool list / trial.
3. SWAPP Frank Archicad demo/API/access.
4. Delta Flow demo/API/architecture.
5. Graphisoft official MCP + Creator access path / upgrade implications.
6. Text2BIM source audit.
7. Design Healing algorithm extraction.
8. CODE-COMPANION Rule IR extraction.
9. IFC-Agent memory/execution architecture extraction.

Only after P0 should we freeze the next SBIM coding sprint.
