# Architectural AI checkpoint 12 — has someone already built SBIM?

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp

## Executive conclusion

A single verified product that matches the entire SBIM target exactly was NOT found.

However, the search found something more important:

1. One commercial platform, **Delta Flow**, publicly describes an architecture strikingly close to the high-level SBIM concept:
   - site intelligence;
   - generative design;
   - code compliance;
   - BIM operations;
   - project intelligence;
   - project knowledge graph;
   - design intent;
   - coordination/clash;
   - quantities/cost;
   - documentation;
   - neuro-symbolic reasoning.

2. **SWAPP** already executes modeling, documentation and QA inside live Revit and Archicad, grounded in firm standards/history.

3. **Archi Automate** already provides the multi-host MCP/control-plane layer we were considering building:
   - Archicad/Revit/Rhino/Grasshopper/AutoCAD/Tekla/Vectorworks/SketchUp/Blender/QGIS/IFC;
   - one MCP server;
   - GPT/Claude/Gemini-compatible clients;
   - read-only / preview / allow-changes governance;
   - action history;
   - one installer/hub.

4. Academic/open-source work already implements several layers we previously treated as likely custom inventions:
   - Text2BIM: NL -> multi-agent architectural design -> native editable BIM -> rule checker -> iterative correction.
   - Design Healing: graph-based propagation from compliance violations -> local design alternatives -> minimal modification selection.
   - IFC-Agent: hierarchical multi-agent IFC reasoning/modification with dual memory and adaptive execution modes.
   - CODE-COMPANION: natural-language regulation -> structured machine-readable rules -> deterministic BIM compliance.
   - Building Information Graphs (BIGs): graph-native building information supporting change propagation and object-level version control.
   - graph-based BIM change propagation / DSM methods: dependency and change-impact prediction already researched.

Therefore the project strategy should change again:

**Do not assume even our "unique core" is fully unique.**
Perform a second-stage reuse audit at the level of architecture/research frameworks, not only software libraries.

## Closest whole-system candidate: Delta Flow

Public 2026 positioning:
- "AI Operating System for Development";
- "end-to-end AI for the built environment";
- "neuro-symbolic platform";
- site analysis + generative design + code compliance + project intelligence;
- unified by a project knowledge graph;
- DF-BIM connects design intent with real-world data;
- inputs/outputs named on the site include design intent, site intelligence, code & standards, coordination & clash, quantities & cost, documentation.

### Why this matters

Conceptually this overlaps with:
- Project World Model;
- Normative Graph;
- Design Intent;
- project knowledge graph;
- generative design;
- validation;
- BIM execution;
- lifecycle/project intelligence.

### Why this is NOT yet "we can stop"

Current public evidence is mostly product/marketing material.
Before treating Delta Flow as a replacement, require a real capability audit:
- supported BIM authoring tools;
- Archicad support;
- Russian regulations;
- API/MCP/export;
- editable/native BIM round trip;
- deterministic rule engine;
- actual knowledge-graph semantics;
- change propagation;
- incremental updates;
- design-intent preservation;
- transaction/rollback;
- local/on-prem deployment;
- pricing/licensing;
- data ownership;
- ability to integrate external normative sources;
- performance on large projects.

Status: **HIGHEST-PRIORITY DEMO/TECHNICAL AUDIT.**

## Closest production BIM automation: SWAPP

Current public claims:
- construction documents and BIM modeling in Revit and Archicad;
- agentic assistant "Frank" reads/writes live BIM;
- models entire floors;
- places dimensions;
- solves collisions;
- QA;
- firm-specific standards and workflow memory;
- ADA compliance checks/fixes;
- live logs and human approval.

Overlap with SBIM:
- BIM execution;
- standards memory;
- agentic actions;
- documentation;
- QA;
- repetitive modeling;
- knowledge capture.

Likely gaps relative to our target:
- Russian normative corpus;
- clause-level normative dependency graph;
- transparent cross-provider provenance;
- project causal graph semantics;
- externally programmable solver stack;
- open integration/control plane.

Status: **HIGH-PRIORITY DEMO/AUDIT, especially because Archicad support is explicit.**

## Closest execution/control-plane product: Archi Automate

Current public 2026 product:
- one MCP server across many AEC applications;
- native Archicad bridge;
- AI clients include GPT/Codex, Claude, Gemini and generic MCP;
- read/analyze/validate/automate;
- policy modes: read-only / preview / allow changes;
- deny lists, action history, rollback/undo where host supports it;
- openBIM/IFC, IDS and BCF support;
- installer + Hub handles connection/setup.

This overlaps strongly with:
- SBIM Control Center;
- tool gateway;
- multi-application tool surface;
- policy/safety execution layer;
- action history.

Implication:
**Do not build a custom MCP/AEC control hub until Archi Automate is evaluated against HuskyBIM and our Add-On.**

Status: **HIGHEST-PRIORITY alongside HuskyBIM.**

## Open/research frameworks that match core SBIM ideas

### Text2BIM
Open-source, MIT core.
Architecture:
- Instruction Enhancer;
- Architect agent;
- Programmer/tool execution agents;
- natural language -> native editable BIM;
- internal/external layouts;
- semantic BIM;
- rule-based model checker;
- iterative feedback/correction;
- Vectorworks integration;
- Solibri checks.

Overlap:
- chat-to-BIM;
- multiple architectural agents;
- editable BIM;
- deterministic checker;
- iterative repair.

Action:
Study code before designing our own multi-agent planning/execution loop.

### Design Healing
Published 2025.
Core:
- consumes BIM + compliance violations;
- graph-based topology propagation identifies relevant objects;
- explores design alternatives;
- finds code-compliant options;
- ranks modifications by distance/disruption from original design.

This is extremely close to our:
- impact cone;
- design healing;
- local alternative generation;
- minimum project disruption objective.

Action:
Treat this as a foundational algorithmic reference, not a vague precedent.
Reproduce its benchmark before inventing another healing algorithm.

### IFC-Agent
Published 2026.
Core:
- hierarchical multi-agent IFC reasoning/modification;
- dynamic tool composition;
- dual memory;
- adaptive dual-mode execution;
- small tasks: asynchronous detailed reasoning;
- large tasks: sample/explore then aggregate/generalize to avoid token explosion.

This overlaps directly with our performance architecture:
- light vs deep modes;
- adaptive task execution;
- caches/memory;
- only inspect representative entities at scale.

Action:
Study its execution strategy before finalizing SBIM model router/project-graph query planner.

### CODE-COMPANION
Published September 2026.
Core:
- natural-language building regulation;
- structured machine-readable rules;
- deterministic BIM evaluation;
- real-time/cross-platform compliance;
- digital permit workflows.

Overlap:
- Rule IR;
- rule compiler;
- BIM binding;
- deterministic checking.

Action:
Audit its rule representation and architecture before implementing our own Rule IR from scratch.

### Building Information Graphs (BIGs)
Recent research proposes graph-native building information to enable:
- explicit relationships;
- graph learning;
- change propagation;
- object-level version control;
- generative/AI applications.

Overlap:
- project causal graph;
- revision/invalidation;
- graph-native project state.

Action:
Study BIG schema and available implementation/data before fixing our internal graph schema.

### BIM change-propagation / DSM literature
Existing work already integrates Design Structure Matrices and BIM to predict change propagation.

Overlap:
- dependency matrix;
- causal impact;
- escalation risk.

Action:
Use established engineering-change theory rather than inventing influence scoring from intuition alone.

## Commercial systems covering adjacent layers

### Finch
- generative building design;
- firm design systems;
- local-code-aware layouts;
- thousands of options;
- high-rise vertical alignment;
- BIM geometry.

Potential role:
candidate generator / early-design engine.

### Hypar
- program/site planning;
- alternatives;
- spaces/circulation/doors/windows/equipment;
- dRofus import;
- Revit/Rhino export.

Potential role:
program/spatial candidate generator.

### Kestrel
- deterministic + AI building code compliance in BIM/Revit;
- jurisdiction-specific codes;
- exact clause citations.

Potential role:
architecture reference for trustworthy compliance UX.

### UptoCode
- reads PDF/IFC/Revit/DWG;
- code/document grounding;
- compliance reports with citations;
- full-regulation audits.

Potential role:
reference for drawing/BIM+regulation multimodal compliance.

### Bluebrick
- site context;
- generative design;
- code compliance;
- environmental/performance inputs.

Potential role:
feasibility/site/generative benchmark.

## Revised uniqueness map

### Probably commodity / existing
- generic BIM CRUD/tool exposure;
- MCP gateway/control hub;
- generic IFC read/write;
- generic clash/IDS checks;
- multi-agent tool-use skeleton;
- code-text extraction;
- rule-check execution frameworks;
- change-propagation algorithms;
- graph databases/algorithms;
- generative space planning;
- workflow memory;
- generic local/cloud model routing.

### Possibly still project-specific
- Russian normative-source federation and legal applicability semantics;
- mapping SP/GOST/state registry requirements into executable project rules;
- Archicad-specific semantic integration if commercial tools lack deep result geometry/event semantics;
- combining external-context constraints, architectural intent and construction-system detail semantics;
- one canonical Project Kernel spanning Russian standards + Archicad + project decisions;
- ranking changes using our architectural/project hierarchy;
- deployment tailored to a single architect/student workstation and later reusable office workflow.

Even these must undergo deeper search before custom coding.

## New rule: three-pass absence proof

The old rule "search, and if nothing exists, build" is not strict enough.

Before declaring a substantial capability absent:

### PASS A — product search
- commercial AEC software;
- vendor add-ons;
- MCP servers;
- SaaS.

### PASS B — open-source/code search
- GitHub/GitLab;
- SDK examples;
- plugins;
- research code.

### PASS C — literature/research search
- Automation in Construction;
- Advanced Engineering Informatics;
- ASCE computing;
- CIB/EC3;
- arXiv;
- university labs/theses.

A module may be labelled `BUILD_CUSTOM` only when all three passes are documented.

If a research method exists without production code, preferred decision is:
`REIMPLEMENT_KNOWN_METHOD`, not `INVENT_NEW_METHOD`.

## Immediate research priority

Before any major new coding:

1. Delta Flow technical/product audit.
2. SWAPP technical/product audit.
3. Archi Automate vs HuskyBIM vs our native Add-On capability matrix.
4. Text2BIM source-code architecture audit.
5. Design Healing method reproduction/algorithm extraction.
6. IFC-Agent architecture extraction.
7. CODE-COMPANION rule representation extraction.
8. BIGs schema/implementation audit.
9. Only then freeze SBIM's own architecture.

## Strategic conclusion

We may not be inventing a new category.

We are likely assembling a **Russia/Archicad-specific integration of a category that is now emerging rapidly in 2025–2026**:
agentic BIM + automated compliance + graph-native building models + generative design + design healing.

That is good news.

The technical risk is much lower if SBIM becomes a well-engineered composition of proven methods/components rather than a bespoke reinvention of every layer.
