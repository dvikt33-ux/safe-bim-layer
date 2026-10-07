# Architectural AI checkpoint 17 — Time-to-Project, Fast Modeling and Compliance-by-Construction

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first
Branch: feature/working-archicad-mvp

## 0. Single project objective

The project has one optimization target: minimize total elapsed human time required to produce a correct, coordinated and deliverable architectural project.

Every candidate capability is evaluated against: manual actions removed; repeated checks removed; rework prevented; documentation steps removed; error probability reduced; and latency/compute overhead introduced.

Primary KPIs: time-to-valid-model, time-to-valid-documentation, time-to-release, number of human rechecks, number of late corrections, and first-pass compliance coverage.

## 1. Compliance-by-Construction

Preferred path: intent -> applicable verified rules -> constrained operation -> read-back -> proof.

For machine-checkable ACTIVE rules, creation/editing tools should receive the constraint before geometry is committed. Commands should be able to snap to the nearest compliant value, show legal min/max while dragging, reject impossible values, require an explicit exception reason, and attach rule/evidence to the operation ledger.

Use four evidence classes:
- A ENFORCED_AT_CREATION — deterministic rule applied before commit.
- B VERIFIED_IMMEDIATELY — deterministic read-back/post-condition after mutation, with rollback/repair on failure.
- C VERIFIED_BY_HEAVY_CHECKER — cross-element/cross-discipline/document-level condition.
- D HUMAN_INTERPRETATION_REQUIRED — interpretation-dependent rule, never silently promoted to guaranteed compliance.

A release Coverage Gate distinguishes passed, failed, not-applicable, not-verified and interpretation-required. Not checked must never become pass.

Useful references: zdanie.ai Coverage Gate and CODE-COMPANION's deterministic/conditional/interpretation-dependent separation.

## 2. Fast Modeling Layer — bring SketchUp-like interaction into AC29

This is a separate workstream from AI. Goal: preserve Archicad BIM semantics while making common geometric edits feel as direct as SketchUp/Qonic.

Archicad C++ API already supports point/line/arc/polygon graphical input, 3D XYZ input, custom input planes, smart-cursor/neig filtering, constraints, dynamic rubber/feedback graphics, element highlighting, modeless palettes and custom toolboxes. Therefore direct-manipulation commands inside AC29 are technically feasible.

### UX benchmark: Qonic

Relevant Qonic operations already exposed publicly in 2025-2026 include Push/Pull, Boundary Push/Pull, Chalk sketch-on-face, Extrude, Loft, Sweep, Slice from curves, Boolean tools, Mirror, Align, snapping, manipulator repositioning, deep face/edge selection, Select Same, right-click context actions, Components and Component Editor.

Qonic's key design lesson is to combine direct modeling and object/BIM modeling instead of forcing one paradigm.

### Native AC29 precedent: Ci Tools

Ci Structure retains rotate, split, bend, offset, align and remove-cuts workflows. Other Ci Tools add domain-specific fast-edit patterns: Fitout clearance areas and room sets; Doors+Windows trims/sills/returns/schedules; Cabinets with 3D edit palettes and select-similar; Coverings linked to host elements; Sites placement along curves/fills and onto Mesh; Labeller surface-specific labels.

### Candidate Fast Modeling commands

FM-01 BIM Push/Pull
FM-02 Sketch/Chalk on Face
FM-03 Extrude Boundary
FM-04 Slice by Sketch
FM-05 Smart Offset
FM-06 Align/Distribute
FM-07 Manipulator Anywhere
FM-08 Select Same
FM-09 Repeat Last Operation
FM-10 Mirror
FM-11 Array Along Path
FM-12 Fill Area With Objects
FM-13 Place on Surface
FM-14 Smart Component Replace
FM-15 Context Menu at Cursor
FM-16 Smart Opening Edit
FM-17 Smart Wall/Slab/Roof Edge Edit

Do not implement Push/Pull as a Morph-only trick. Preferred design is semantic direct modeling: evaluated face -> owner BIM element -> semantic editable parameter.

Examples: wall end face changes endpoint; wall top face changes height/top constraint; hosted opening face changes width/height/offset; slab edge changes polygon; object/component uses editable hotspots/GDL parameters where available; raw Morph/B-Rep is the fallback only when no semantic BIM representation exists.

## 3. Light / Medium / Heavy execution architecture

### LIGHT — interactive deterministic path

No LLM in the critical path. Direct modeling, snapping, favorites/components, deterministic transforms, Rule-IR class-A constraints, cached applicability and instant read-back. If intent maps to one deterministic semantic command, AI stays out.

### MEDIUM — local orchestration path

For short context-sensitive workflows, use: intent -> semantic tool retrieval -> local router -> 3-5 candidate tools -> bounded plan -> execute -> read-back.

Routing order: deterministic aliases/grammar first; embedding-based MCP tool retrieval second; small local function-calling model only if intent remains ambiguous.

A 2026 semantic MCP discovery study reports high hit rate while exposing only a small top-K set instead of the whole tool catalogue. FunctionGemma 270M is an example of an edge model specialized for function calling. Larger local 7-9B models can be benchmarked only where the tiny router is insufficient.

### HEAVY — reasoning/audit/healing path

Use frontier GPT planning, Canonical Project Graph, verified Rule IR, Design Healing, IFC-Agent sample->toolchain->batch, and external checkers only for cross-discipline, high-blast-radius, ambiguous-rule or full-project work.

Default escalation: LIGHT for one deterministic operation; MEDIUM for short repetitive multi-tool work; HEAVY for cross-discipline/high-risk/full-project work. The user should rarely need to pick the level.

## 4. Local neural network role

Do not embed a large general LLM directly inside the Archicad Add-On process. Preferred architecture is Archicad thin Add-On/palette <-> local sidecar router <-> MCP/providers.

Benefits: isolates crashes, avoids blocking the Archicad UI, permits independent model restart/update, changes CPU/GPU policy per workload and keeps providers replaceable.

The local model is primarily a switchboard: infer intent, retrieve relevant tool families, map words to parameters and compose short bounded macros. It never owns normative meaning or canonical project state.

## 5. New neighboring-research projects and their roles

### zdanie.ai / Proektologiya
Current public material describes a versioned Russian norm base, PDF/DWG/IFC parsing in the platform, 18 specialized critics, REST API/webhooks already working, MCP/BCF integrations planned, clause-linked findings and a Coverage Gate. Best role: HEAVY independent Russian final/document audit, benchmarked against our authoritative norm corpus rather than trusted blindly.

### CYPEURBAN
Free user-definable urban-rule engine covering plot, floors/heights, setbacks, overhangs, occupancy/buildability, patios, parking and adjacent-building-dependent constraints. Best role: deterministic external urban/site checker and rule-representation reference.

### CYPE Construction Systems
Defines layered wall/slab/roof/partition assemblies, materials/thicknesses and links them to BIM elements; reports assembly-thickness mismatch. Best role: construction-assembly knowledge and deterministic thickness-coherence checker.

### Qonic
Best current Fast Modeling UX benchmark. Also supports IDS validation and agentic property repair at scale. Do not confuse IDS/data validation with full legal compliance.

### Motif
Publicly demonstrates parametric associative BIM, synchronized drawings, version history, live collaboration and agents. Archicad integration remains unconfirmed. Best role: modern BIM UX and agent-in-live-model benchmark.

### Speckle
Archicad 27/28/29 connector plus Automate triggers on model changes, schedules or manual actions. Model Checker validates Archicad properties/naming/ranges. Best role: event-driven external automation bus and open data/analytics layer.

### Tangl
Public API exposes model metadata/geometric data and identifiers. Tangl Control advertises clash/min-distance, parameter rules, EIR, apartment/product/regulatory checks. Best role: Russian BIM QA/data-checking benchmark and API/data-model reference.

### usBIM
IFC viewer/editor/federation, BCF, validation/checklists, clash, 4D/CDE/GIS ecosystem. Keep as openBIM federation/checking alternative until depth/API/cost are compared.

## 6. Incremental validation

Do not recheck the whole model after each edit. Graphisoft Solibri Connection already demonstrates changed-element synchronization. Preferred architecture: element event -> changed GUID set -> impact graph -> applicable rules -> incremental checks. Full-model audit is for milestones.

## 7. Approved Construction Primitive (ACP)

For recurring details, the largest time saver is a verified semantic template rather than repeated AI generation.

ACP examples: exterior wall assembly, window reveal/quarter, sill/head/jamb, slab edge, accessible door, restroom module, stair/ramp, roof eave/parapet, fire-rated partition and MEP penetration detail.

Each ACP stores semantic parameters, applicable rule IDs, allowed parameter intervals, layer/material requirements, host requirements, dependent detailing, documentation recipe, verification tests, version and provenance.

Workflow: choose intent -> ACP -> rule-constrained parameters -> place -> instant proof. AI chooses/adapts the right ACP; it does not reinvent it every time.

## 8. Time-saving pipeline

1. User acts directly or states intent.
2. Router identifies semantic operation.
3. Canonical Kernel resolves selected/related objects.
4. Rule applicability resolves only relevant ACTIVE rules.
5. Fast Modeling / Husky / Tapir / specialist provider executes.
6. Read-back compares requested vs actual Archicad state.
7. Incremental checker validates affected rule cone.
8. Pass becomes verified state.
9. Deterministic failure rolls back or repairs to nearest compliant state.
10. Ambiguous/cross-discipline failure escalates to HEAVY planning/healing.
11. Documentation updates only affected views/sheets.
12. Milestone runs a coverage-gated full audit.

## 9. Optimization rule

Always use the least expensive intelligence that can produce a correct result:
1 cached approved primitive;
2 deterministic native command;
3 deterministic rules;
4 semantic retrieval;
5 tiny/local router;
6 bounded local agent;
7 frontier LLM;
8 full multi-agent/healing/audit.

Never use a frontier agent when a deterministic command is sufficient.

## 10. Immediate research queue

FASTMODE-01 — map Qonic/Ci gestures to AC29 C++ APIs and semantic BIM edits.
COMPLIANCE-BY-CONSTRUCTION-01 — prove one rule-constrained interactive edit.
ACP-01 — define Approved Construction Primitive schema, starting with opening/reveal or wall/slab build-up.
ROUTER-01 — semantic index over Husky/Tapir/open manifests; benchmark top-K retrieval and local routing.
DELTA-CHECK-01 — event -> impacted GUIDs -> applicable rules only.
CYPE-01 — map CYPEURBAN/CYPE Construction Systems concepts to Russian constraints and construction assemblies.
RUS-AUDIT-01 — benchmark zdanie.ai findings against authoritative Russian norm corpus.
QONIC-UX-01 — detailed command/gesture matrix.
CI-TOOLS-01 — inventory direct reuse versus UX-pattern harvesting.
SPECKLE-01 — evaluate as non-blocking validation/automation bus.
TANGL-USBIM-01 — deep API/QA comparison.

## 11. Governing conclusion

The fastest future workflow is not AI does everything.

It is: human direct manipulation + deterministic constrained BIM + reusable verified primitives + tiny local orchestration + heavy AI only on hard problems.

The target experience should feel like SketchUp/Qonic when editing, Archicad when documenting, a rule engine when enforcing constraints, SWAPP when producing documentation, Husky/Tapir when executing BIM operations, Design Healing when conflicts appear, and independent checkers when proving a milestone — while the user sees one coherent interface.