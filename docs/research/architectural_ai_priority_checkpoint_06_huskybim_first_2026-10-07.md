# Architectural AI priority checkpoint 06 — HuskyBIM-first audit and automatic model routing

Date: 2026-10-07
Status: ACTIVE RESEARCH PRIORITY
Branch: feature/working-archicad-mvp

## Priority change

Highest research priority now:
1. HuskyBIM for Archicad 29 — deep capability audit before writing more low-level Archicad writers.
2. dRofus — deep requirements/rooms/equipment workflow audit before building our own room/equipment database from scratch.
3. Local-model role and benchmark — define exactly where local inference improves the system versus cloud GPT.
4. Automatic model routing — user should not have to choose which model runs each task.
5. Continue performance-first reactive kernel and project compiler architecture.
6. Expand low-level Archicad write commands only after the HuskyBIM/Tapir/our-add-on capability diff is complete.

## Correction to previous research process

Earlier conclusions that "nothing suitable exists" were too shallow. This project must adopt a new research rule:

Before implementing a substantial subsystem, perform an explicit existing-solution sweep:
- official Archicad features/add-ons;
- MCP/connectors;
- commercial AEC tools;
- open-source AEC frameworks;
- current research/software;
- current GitHub projects;
- vendor documentation.

A subsystem moves to custom implementation only after documenting:
- existing candidates;
- coverage;
- gaps;
- licensing/deployment constraints;
- integration cost;
- why custom work remains necessary.

## HuskyBIM vs Tapir — do not compare raw counts naively

Current verified public facts:
- HuskyBIM Archicad 29 advertises 733 MCP tools and says all are functional/tested against Archicad 29.
- Its published domains include element CRUD, attributes, classifications, layouts/drawings, BCF issues, stories and properties.
- Tapir is an Archicad Add-On that adds JSON commands on top of Graphisoft's official JSON/API surface.
- A current independent Archicad-MCP project reports 309 commands in its verified combined official+Tapir command surface (138 reads / 171 writes).

Therefore "733 > 150" is not an apples-to-apples proof that HuskyBIM is technically superior:
- one MCP tool may be a narrow wrapper around a lower-level command;
- one Tapir command may cover many element types/operations;
- HuskyBIM count includes high-level management/documentation tools;
- Tapir/open API and our C++ Add-On may expose lower-level geometry/resultant-model data that HuskyBIM may or may not expose.

But HuskyBIM clearly has much broader ready-made AI-facing coverage and is now the leading candidate for replacing a large amount of low-level glue work.

## Mandatory HuskyBIM capability-diff

Build a matrix for:
- Walls / Doors / Windows / Slabs / Roofs / Shells / Morphs;
- Columns / Beams / Stairs / Railings / Curtain Wall;
- Zones;
- attributes/materials/composites/profiles;
- stories;
- layouts/drawings/views;
- classifications/properties;
- BCF/issues;
- batch operations;
- multi-story operations;
- Hotlinks/modules;
- undo/transaction grouping;
- read-back;
- element/result geometry;
- memos;
- hosts/relationships;
- materials per face;
- observer/change events;
- 3D bodies/faces/vertices;
- performance/payload sizes;
- error semantics;
- MCP clients supported;
- ability to use with our own model router instead of a fixed Claude-only workflow.

Classify each cell:
PASS / PARTIAL / BLOCKED / UNKNOWN.

Only after this matrix should we decide what parts of Tapir/our Add-On remain strategic.

## What our existing work still provides even if HuskyBIM wins most CRUD

Our two weeks are not discarded.

Already-built/learned layers remain directly useful:
- native Archicad API build pipeline;
- full model dump and geometry/material understanding;
- live create/read-back/delete evidence;
- host relationships;
- writer verification;
- BIM minimality rules;
- change watcher research;
- safe commit/read-back ideas;
- knowledge of Archicad API limitations;
- current GitHub structure and executable test harness.

If HuskyBIM replaces low-level writers, our code becomes:
- independent verifier;
- deep geometry reader;
- event/revision bridge;
- specialized command layer for gaps;
- safety/transaction layer;
- benchmark oracle.

## Why use a local LLM when cloud GPT exists?

Local AI is NOT the lead architect by default.

It earns its place only where it improves one or more of:
- marginal cost for very high-volume repetitive reasoning;
- privacy/local-only processing;
- offline availability;
- long-running background work without tying up cloud interaction;
- low-latency local classification/extraction/tool planning;
- independent second-opinion/audit;
- preprocessing/compression of huge local model/log/document context before cloud escalation.

The strongest current role is L0/background work:
- Project Compiler;
- normative/document extraction;
- model-dump/log compression;
- candidate enumeration;
- first-pass classification;
- long batch jobs;
- independent critique.

Cloud GPT remains preferred for:
- architectural synthesis;
- ambiguous design decisions;
- cross-discipline conflict resolution;
- high-risk changes;
- final explanation/choice among valid candidates.

Deterministic code remains preferred for:
- calculations;
- geometry;
- exact rules;
- graph traversal;
- indexes;
- cache;
- known repeated operations.

## Automatic routing — user chooses goals, not models

Expose one user interface.

Internal Router uses task metadata:
- task_class;
- risk;
- latency budget;
- privacy requirement;
- modality;
- context size;
- structured-output requirement;
- deterministic confidence;
- project revision;
- rule-pack state.

Proposed routing ladder:

1. DETERMINISTIC
   If the task is exact and already formalized, no LLM.

2. LOCAL_FAST
   High-volume, low-risk, structured classification/extraction/tool planning.

3. LOCAL_DEEP
   Long background compilation/research/critique where minutes are acceptable.

4. CLOUD_LEAD
   Architectural judgement, ambiguity, major escalation, high-risk synthesis.

5. DUAL_REVIEW
   For high-impact transactions: primary reasoning + independent critic, but hard compliance still decided by deterministic rules.

The user never manually selects Qwen/GPT during ordinary work.

## Qwen/Strata clarification

Current Strata documentation recommends for 48 GB RAM:
- Q2_0 or IQ2_XS.

Current Strata docs state Qwen3.8-Flash-Next is the large MoE model it is optimized for and separates model data across RAM/VRAM/SSD.

On the target laptop with 48 GB RAM and 8 GB VRAM, fitting is plausible for the recommended low-bit variants, but interactive speed and UI coexistence with Archicad must be benchmarked. Current upstream Strata requirements pages are inconsistent about minimum VRAM across revisions/forks, so do not treat "supported on 8 GB" as verified until a local test succeeds.

Qwen3.5-35B-A3B is not automatically better for this project merely because it activates fewer parameters. Fewer active parameters can improve inference cost, but actual usefulness depends on:
- architecture/reasoning quality;
- quantization;
- prompt ingest;
- tool calling;
- Russian architecture vocabulary;
- structured output reliability;
- memory bandwidth;
- VRAM/RAM placement.

Benchmark on our workload; do not decide from parameter counts.

## Immediate next actions

1. Install/evaluate HuskyBIM in an isolated test setup.
2. Produce the capability matrix against:
   - HuskyBIM;
   - Tapir + official Archicad surface;
   - our native Add-On.
3. Evaluate dRofus trial/workflow and integration surface.
4. Build one automatic ModelRouter abstraction before binding any local model deeply.
5. Benchmark Strata/Qwen3.8 only as a candidate worker, not as an architectural requirement.
6. Stop adding low-level writers that HuskyBIM already proves reliable unless our verifier/geometry layer specifically needs them.
