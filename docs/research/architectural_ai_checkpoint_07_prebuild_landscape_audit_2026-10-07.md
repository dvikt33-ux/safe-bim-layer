# Architectural AI checkpoint 07 — pre-build landscape audit

Date: 2026-10-07
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp

## Purpose

Apply the project's new SEARCH-BEFORE-BUILD rule to the concrete subsystems we are about to implement.

Decision labels:
- REUSE — use directly.
- WRAP — keep the existing product/library and add our project safety/semantic layer.
- ADAPT — extend/configure/fork.
- COMPOSE — combine several existing systems.
- BUILD_GAP_ONLY — write only the missing bridge/intelligence.
- BUILD_CUSTOM — custom implementation justified only after benchmark/gap proof.

## Executive result

A large fraction of the "infrastructure" should NOT be written from scratch.

The strongest current reuse candidates are:
- HuskyBIM — broad Archicad 29 AI-facing tool surface.
- dRofus — room/program/requirements/equipment synchronization.
- IfcOpenShell family — independent IFC parsing, validation, diff and clash.
- buildingSMART IDS + bSDD — machine-readable information requirements and semantic dictionaries.
- Solibri / BIMcollab Zoom — independent model QA/release checking.
- Hypar — dependency-based computational workflows and early spatial/program design.
- TopologicPy — spatial/topological graph generation and analysis.
- BHoM — transdisciplinary AEC object-model and adapter patterns.
- Speckle — Archicad interoperability/data flow/version-oriented collaboration.
- Grasshopper–Archicad Live Connection — parametric/special geometry.
- LiteLLM — unified model gateway/router.
- pgvector/Qdrant — retrieval infrastructure; do not implement vector search.
- Temporal — durable long-running workflows if/when L0 compilers become multi-process or failure-sensitive.
- Taskflow/Boost/SQLite/OR-Tools/Z3/Feldera — performance/runtime building blocks.

The unique custom code should focus on:
1. Russian normative clause graph + legal applicability/version logic.
2. Cross-domain project causal graph and change-impact semantics.
3. Architectural-intent representation/preservation.
4. Project transaction/escalation/healing logic.
5. Archicad-specific event/revision/read-back safety gaps not covered by existing products.
6. Compiled Project Kernel + Validity Envelopes.
7. Integration/orchestration among existing components.

## Subsystem audit

### A. Archicad CRUD / AI tool surface

Candidates:
- HuskyBIM for Archicad 29: advertises 733 tested MCP tools across element CRUD, attributes, classifications, layouts/drawings, BCF, stories, properties.
- Tapir + official Graphisoft JSON/API.
- Community Archicad MCP projects.
- Our current native Add-On / Model Dump.

Decision: **WRAP / BUILD_GAP_ONLY**

Do not continue implementing generic CRUD until the HuskyBIM capability matrix is complete.

Our likely retained custom responsibilities:
- deep result-geometry/material read;
- element observer/change event queue;
- project revision/stale-transaction guard;
- specialized operations missing from HuskyBIM;
- safe batch commit/read-back verifier;
- independent benchmark oracle.

Unknowns requiring tests:
- batch semantics;
- undo grouping;
- element observer/change feed;
- 3D bodies/faces/vertices;
- face material provenance;
- host/link depth;
- memo access;
- latency/payload;
- use from our own router rather than only vendor-default client.

### B. Room program / requirements / equipment

Candidates:
- dRofus: room data sheets, room templates/groups, function program, Archicad Zone <-> Room linking, Archicad Object/element <-> Item linking and room item-list comparisons.
- Hypar: program import, spaces, circulation, doors/windows/equipment and live area/equipment metrics.

Decision: **REUSE/WRAP dRofus first; study Hypar for early design.**

Do not build a complete room/equipment requirements database before dRofus evaluation.

Custom gaps likely remain:
- normative causality;
- equipment substitution solver;
- architectural intent;
- geometric feasibility/clearance propagation;
- deep relationship to our project graph.

### C. Spatial/topological graph

Candidates:
- TopologicPy and research/examples converting buildings to adjacency, movement and visibility graphs.
- NetworkX/Boost.Graph for generic graph algorithms.
- Hypar model dependencies for computational design-function dependencies.

Decision: **COMPOSE / ADAPT**

Do not invent adjacency, movement, visibility or generic graph algorithms.

Custom code should define our architectural semantics and map BIM/geometry into these structures.

### D. Common AEC object schema

Candidates:
- IFC.
- BHoM: software-agnostic transdisciplinary AEC schemas + Push/Pull adapter framework.
- bSDD: stable semantic class/property dictionaries and class/property relations.

Decision: **ADAPT / COMPOSE**

Before inventing hundreds of object classes:
- map required entities to IFC/BHoM/bSDD;
- create custom classes only where project reasoning requires semantics not represented cleanly.

Do not make BHoM a hard dependency until Archicad/integration fit is proven.

### E. Information requirements / property compliance

Candidates:
- buildingSMART IDS 1.0: official machine-readable IFC information requirements and automatic checking.
- IfcTester: author/read IDS and validate IFC.
- BIMcollab Zoom: IDS validation.
- Solibri: information/model checks.

Important limitation:
IDS is primarily alphanumeric/information requirements, not general geometric code compliance.

Decision: **REUSE for information requirements; BUILD_GAP_ONLY for geometric/legal rules.**

Do not invent our own property-requirement file format.

### F. Normative/code compliance graph

Candidates:
- IDS / bSDD for information semantics only.
- Solibri/BIMcollab/custom rules for portions of model checking.
- Generic knowledge-graph/rule engines (Datalog/Soufflé, Z3).

No mature product was found in this pass that directly provides:
- Russian SP/GOST/73-FZ/PZZ/GPZU clause-level legal versioning;
- dated/undated normative-reference semantics;
- project applicability closure;
- exact provenance;
- propagation from changed normative clause into project design variables.

Decision: **BUILD_CUSTOM CORE, reusing generic engines.**

This remains one of the project's strongest genuinely unique areas.

### G. IFC validation / clash / independent audit

Candidates:
IfcOpenShell ecosystem:
- IfcTester;
- IfcClash;
- IfcDiff;
- IfcQuery;
- IfcPatch;
- BCF;
- IfcMCP and more.

Independent GUI QA:
- Solibri;
- BIMcollab Zoom, including clash, IDS and distance checking.

Decision: **REUSE.**

Do not build an IFC parser, diff engine, generic clash engine or IDS validator.

Our role:
- generate/project-specific checks;
- interpret results;
- link them to causal graph and design healing.

### H. Versioning / model diff / collaboration state

Candidates:
- IfcDiff for IFC changes.
- Speckle for Archicad-connected data flow and design evolution.
- BIMserver: IFC object database with model checking, revision/versioning, query, merge, notifications and low-level change calls.
- Git/BCF for source/issues where appropriate.

Decision: **COMPOSE / BENCHMARK BEFORE CUSTOM.**

Our custom project-revision guard is still likely necessary in the live Archicad transaction path, but do not reinvent general IFC history/diff/collaboration infrastructure.

BIMserver's AGPL licensing and Java stack must be reviewed before adoption.

### I. Computational/generative early design

Candidates:
- Hypar: program/site-driven spatial planning, model dependency workflows, alternatives.
- TestFit: rapid feasibility/generative schemes.
- Finch3D: candidate-generation direction to re-evaluate separately.
- Grasshopper for parametric logic.

Decision: **REUSE AS CANDIDATE GENERATORS, NOT PROJECT AUTHORITY.**

Our system should consume/score candidates rather than rewrite mature generative-layout tools unless specific gaps justify it.

### J. Parametric/special geometry and repeated structures

Candidates:
- official Grasshopper–Archicad 29 Live Connection.
- Archicad Edit Elements by Stories.
- Archicad Hotlink Modules.
- native multi-story elements where suitable.

Decision: **REUSE.**

Our L0 Project Compiler should select repetition strategy:
INDEPENDENT_COPY / HOTLINK_MODULE / STACK_CONSTRAINT / MULTI_STORY_NATIVE.

Do not recreate parametric geometry or repeated-floor propagation when native mechanisms fit.

### K. Incremental dependency computation

Candidates:
- custom compact C++ dirty graph with Boost/Taskflow for the interactive hot path.
- Feldera/DBSP for incremental view maintenance at larger scale.
- Soufflé for compiled recursive relations/rule closure.
- GraphBLAS/LAGraph for very large graph analytics.

Decision: **BUILD MINIMAL HOT KERNEL; ADOPT BIG ENGINE ONLY AFTER BENCHMARK.**

Do not introduce Feldera/Soufflé/GraphBLAS before real profiling proves need.

### L. Solver

Candidates:
- OR-Tools CP-SAT;
- Z3;
- generic geometry engines.

Decision: **REUSE.**

Do not write a generic CSP/SAT/SMT optimizer.

Write domain-specific constraint compilation and candidate generation only.

### M. Local persistence / analytics

Candidates:
- SQLite WAL for single-machine working state/event log.
- DuckDB for analytics on logs/Parquet.
- PostgreSQL/PostGIS + pgvector if/when multi-project/networked backend becomes justified.
- Qdrant if dedicated vector retrieval is needed.

Decision: **REUSE.**

Do not build a database, vector database, transaction log engine or analytics engine.

Start simple with SQLite; migrate only when benchmarks/use-case require.

### N. Retrieval/search over project knowledge

Candidates:
- pgvector/Postgres full-text hybrid search.
- Qdrant filtering + vector search.
- local embedding/reranker models.

Decision: **REUSE.**

Our custom work:
- metadata/provenance schema;
- exact normative filters;
- retrieval policy;
- reranking/evidence requirements.

Vector similarity can retrieve candidates but never determines normative truth.

### O. AI model routing

Candidate:
- LiteLLM gives a unified OpenAI-compatible interface, retries/fallbacks, routing, timeouts and optional caching across many model providers.

Decision: **WRAP/REUSE once >2-3 model endpoints exist.**

Do not build a full provider gateway.

Our custom layer should only decide semantic task class/risk:
DETERMINISTIC / LOCAL_FAST / LOCAL_DEEP / CLOUD_LEAD / DUAL_REVIEW.

### P. Long-running orchestration

Candidate:
- Temporal provides durable workflow execution that retains state/progress across failures.

Decision: **DEFER / REUSE IF NEEDED.**

For the initial single-machine L0 compiler, a local job runner may suffice.
If multi-hour pipelines span services, retries, restarts and external tools, adopt Temporal rather than inventing durable execution.

### Q. Performance scheduler/profiling

Candidates:
- Taskflow work-stealing executor;
- Tracy profiler;
- Google Benchmark;
- CRoaring bitmaps;
- xxHash.

Decision: **REUSE.**

Do not write thread pool, profiler or bitmap containers.

## What we should probably code ourselves next

After this audit, the next custom code should be narrow:

1. **HuskyBIM capability test harness**
   - execute equivalent operations through HuskyBIM/Tapir/our Add-On;
   - compare read-back, semantics, latency and failure behavior.

2. **Archicad Change/Revision Bridge**
   - only if HuskyBIM does not expose native observers and safe revision semantics.

3. **CompiledProjectKernel schema**
   - composed from existing standards/models, not a new universal BIM ontology.

4. **ValidityEnvelope + Invalidation Engine**
   - small initial implementation.

5. **Russian Normative Clause Graph**
   - clause/source/version/reference/applicability/provenance model.

6. **Project Causal Edge Layer**
   - architectural types missing from generic graph systems.

Everything else should remain an integration/benchmark task until a proven gap exists.

## Software evaluation queue

Highest priority trials/evaluations:
1. HuskyBIM.
2. dRofus.
3. TopologicPy.
4. IfcOpenShell toolchain.
5. Hypar.
6. BHoM schema/adapter mapping.
7. Speckle Archicad connector/version workflow.
8. Solibri vs BIMcollab independent checks.
9. LiteLLM when model endpoints are ready.
10. Strata/Qwen local inference benchmark.

## New gate

No new non-trivial subsystem may enter implementation without a one-page Existing Solution Audit containing:
- problem definition;
- at least 3 search channels unless the space is inherently narrow;
- candidates;
- evidence/source links;
- capability matrix;
- license/cost;
- integration/runtime implications;
- decision: REUSE/WRAP/ADAPT/COMPOSE/BUILD_GAP_ONLY/BUILD_CUSTOM.

This gate applies to both architecture-domain code and infrastructure code.
