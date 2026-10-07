# Architectural AI checkpoint 22 — floor-plan intelligence, spatial logic and precedent memory reuse

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Context carried forward

This checkpoint explicitly incorporates the completed parallel-chat result:

- `architectural_ai_checkpoint_20_fast_project_compiler_layered_runtime_2026-10-08.md`
- commit `846c6eeafe7430227a63f441046bfe57965c86bb`
- `layer-reuse-decision-matrix-v0.7.yaml`
- commit `bf2c8761ad2d683d16631083e55e0f8bf9d6af8b`

Therefore this pass does **not** reopen the already-fixed decisions:
- AC29 first;
- HOT/WARM/COLD project state;
- LIGHT/MEDIUM/HEAVY execution;
- semantic provider arbitration;
- Coverage Signature;
- Approved Construction Primitives;
- donor-detail-first policy;
- heavy algorithms reused instead of invented.

This pass attacks the remaining "architectural logic" gap:
- floor planning;
- room adjacency;
- circulation;
- daylight-facing rooms;
- egress;
- program mix;
- firm precedent reuse;
- spatial intelligence;
- learning from previous projects.

---

# 1. FloorPlan6 / FloorPlan4 — extremely important AC29-native/open precedent

A new high-priority find is the open `poolpet/floorplan6` / `poolpet/floorplan4` family.

## FloorPlan6

Current public state:
- Python 3.10+;
- Archicad outline input through Tapir;
- OR-Tools CP-SAT;
- Shapely;
- NetworkX;
- PyQt;
- apartment layout generation;
- floor layout generation;
- WT 2002 Polish Building Code constraints;
- native export back to Archicad;
- active development;
- 80/80 unit tests + regressions reported for the stable apartment stage.

Current Stage 4 features include:
- exact/strict area constraints;
- room minimums and maximums;
- facade/daylight requirements;
- corridor/hub topology;
- adjacency;
- room proportions;
- variant scoring;
- door/wall/zone output;
- irregular outlines including L-shapes/trapezoids in the documented workflow.

Current Stage 3 includes:
- stairwell count;
- corridor generation;
- Dijkstra-based walking-distance verification.

Architecture is intentionally split:
- algorithm layer in Python;
- Archicad bridge separately;
- tests and render/debug loop;
- C++ retained only as a native UI/bridge reference.

This is almost exactly the implementation strategy we independently converged on.

## FloorPlan4

`poolpet/floorplan4` is a native Archicad 29 C++ Add-On.

It already demonstrates:
- modeless Archicad palette;
- boundary reading;
- CP-SAT constrained apartment layouts;
- wall/door/zone creation in Archicad;
- MPZP plot analyser;
- independent solver library vs AC UI/bridge separation.

This is an unusually relevant reference because its target is **Archicad 29**, not Revit.

## Lessons especially relevant to SBIM

FloorPlan6's own documented history reports that:
- an all-C++ approach made geometry/rule iteration slow and error-prone;
- moving solver/geometry logic back to Python improved visual debugging and regression discipline;
- OR-Tools in Python is clearer for direct rule-to-constraint mapping;
- native C++ should remain focused on AC UI/bridge/performance.

This strongly reinforces our current architecture:
`fast native AC interaction + Python/solver sidecars + strict readback/tests`.

## License warning

- FloorPlan6: AGPL-3.0.
- FloorPlan4: GPL-3.0.

Therefore:
- code can be studied and tested;
- algorithms/patterns are valuable references;
- copying/linking into a differently licensed SBIM codebase requires deliberate license compatibility review.

### Decision

**P0 SOURCE/METHOD AUDIT.**

Do not write a new apartment/floor solver before reproducing FloorPlan6 on a real AC29 test outline.

---

# 2. Finch is substantially more relevant to Archicad 29 than earlier research showed

Earlier research treated Finch mainly as a Rhino/Grasshopper route.

Current Finch documentation now includes a **beta Archicad plugin v1.0.8 supporting Archicad 28 and 29** and dedicated current tutorials for:
- generating plans inside Archicad;
- assigning plans to Archicad zones;
- downloading/importing Finch projects into Archicad.

The current Archicad tutorial shows:
- exterior walls identified for daylight;
- generated unit-plan alternatives;
- walls/doors generated;
- space types returned as Archicad Zones.

Another import tutorial states imported results include:
- walls;
- doors;
- Zones;
- floor plates.

There is an inconsistency with an older/current FAQ page that still says Archicad support through Grasshopper.
The dedicated plugin download page and Archicad tutorials are more specific/recent and therefore require hands-on verification.

## Finch architectural intelligence already overlaps heavily with our roadmap

Current public documentation includes:

### Story/floor logic
- generation around existing circulation;
- generated cores;
- generated corridors + cores;
- egress-distance constraints;
- stairwell counts;
- stairwell attractors;
- core/corridor dimensions;
- wall widths;
- unit widths;
- passage widths;
- iterative scoring.

### Unit/program logic
- target unit mix;
- program allocation;
- size accuracy;
- grid-line alignment;
- daylight access;
- squareness;
- adjacency;
- minimum unit width;
- mirrored/symmetric plan logic.

### Firm memory
Finch's Adaptive Plan Library can:
- store previous unit plans;
- adapt one plan to many new shapes;
- lock walls;
- define extend-only constraints;
- preserve minimum dimensions;
- search/match a user's plan library.

Enterprise generation explicitly uses:
- the firm's private plan library;
- firm design style;
- rules;
- region;
- accessibility;
- daylight;
- custom tags;
- furniture;
- learned/generated alternatives based on that library.

This is almost exactly our proposed:
`verified donor project -> adapt -> validate -> reuse`.

### Linked repetition
Identical plans can be grouped so edits propagate to linked units.

This is directly relevant to repeated-storey/apartment logic and may remove a large amount of copy/update automation.

## Current pricing

Public 2026 pricing:
- Free: editing/performance feedback;
- Basic: €79/month, 14-day trial, early-stage generation;
- Enterprise: from €14,500/year for 3 seats, including AI floor-plan generation, firm-wide plan library, code/compliance and custom integrations.

### Decision

**P0 TRIAL/PLUGIN AUDIT.**

Even if Enterprise is too expensive for current use, the AC29 plugin + Basic/free workflows may still be valuable for:
- direct plan import/export;
- plan-library reuse;
- unit/floor generation benchmark;
- architectural-quality reference.

---

# 3. FloorPlan6 + Finch form a much more realistic near-term plan-intelligence stack

These systems complement rather than duplicate each other.

## FloorPlan6 strengths
- open source;
- AC29-specific;
- explicit constraint solver;
- code/rule transparency;
- easy Russian rule adaptation conceptually;
- direct algorithm access;
- low monetary cost.

## Finch strengths
- polished UX;
- adaptive firm plan library;
- direct AC29 beta plugin;
- multi-floor/unit algorithms;
- daylight/grid/egress metrics;
- linked units;
- mature interactive generative workflow.

## Proposed role split

```
Russian hard rules / custom typologies
        ↓
FloorPlan6-style CP-SAT / OR-Tools
        ↓
candidate layouts
        |
        +--> TopologicPy spatial metrics
        +--> daylight / circulation / egress
        +--> intent/precedent score
        ↓
Archicad 29

Optional commercial accelerator:
Finch adaptive plan library / generation
```

No need to train a custom floor-plan neural network first.

---

# 4. TopologicPy can replace much of our custom "architectural spatial logic" engine

The current `wassimj/topologicpy` project is now much broader than a geometry library.

It explicitly targets:
- architectural space planning;
- building analysis;
- circulation/navigation;
- topology;
- graph analysis;
- semantics;
- AI/ML.

Current code/ontology includes:
- AdjacencyGraph;
- VisibilityGraph;
- CirculationGraph;
- ConnectivityGraph;
- KnowledgeGraph;
- GraphRAG;
- PyTorch Geometric integration;
- topology -> graph conversion;
- subgraph matching;
- shortest-path operations;
- ontology/RDF support;
- BOT/Brick/IFC alignment.

A current public example demonstrates a building represented simultaneously as:
- geometric adjacency graph;
- movement/access graph;
- sightline graph;

and evaluates:
- chokepoints;
- communities;
- blind spots;
- user-group/security separation.

This is directly applicable to our required logic:
- public/staff/service route separation;
- corridor quality;
- blind corners;
- access hierarchy;
- room adjacency;
- door-mediated access;
- visual connections.

### Decision

Use TopologicPy as the default **WARM/HEAVY spatial intelligence library** before implementing custom adjacency/circulation/visibility algorithms.

Custom code should be limited to:
- extraction from Archicad/IFC;
- project-specific semantic labels;
- project-specific scores/constraints.

---

# 5. Plan generation itself is now clearly a mature product/research category

Additional current evidence:

## Architechtures

Current product:
- residential generative design;
- real-time BIM;
- unit/program/area control;
- below-grade parking;
- cost;
- project metrics;
- local-rule customization;
- IFC/DXF/XLSX output;
- LOD 200+ BIM.

Current Pro price:
- $49/month billed annually;
- 7-day trial.

This is a realistic low-cost benchmark for early residential design even without native AC29 integration.

## qbiq

Commercial space planning already includes:
- program generation;
- multi-floor plans;
- daylight/privacy/efficiency metrics;
- structured Revit/CAD output;
- quantity takeoff;
- iterative edits;
- custom planning engines.

September 2026 Agentic SpacePlan adds:
- real-time alternatives;
- architect-directed AI;
- explicit preservation of design intent as layouts evolve.

This directly challenges the idea that "preserve intent while AI modifies the plan" is a unique product problem.

## Higharc

Its 2026 Generative Building Model represents BIM-native building information as structured tokens rather than pixels.

The stated objective is to preserve:
- geometry;
- BIM relationships;
- downstream buildability.

Higharc Studio uses:
- 1,000+ settings;
- rules-based layout automation;
- live plan/BIM/downstream updates.

This is an important architecture reference:
if we ever train a generative architectural model, use **structured semantic building tokens**, not raster floor-plan images.

## TestFit MCP

TestFit now exposes an MCP connector to:
- ChatGPT/Codex;
- Claude;
- other local clients.

The AI handles language; TestFit's deterministic engine generates the site plan.

This is exactly our desired "LLM routes to deterministic architectural engine" pattern.

Current limitation for us:
- Site Solver starts around $15,000/year;
- therefore not an immediate solo dependency.

### Decision

Do not build general early-stage site/layout generation until the open/low-cost stack has been benchmarked.

---

# 6. Plans2BIM removes another AC29 conversion problem

Graphisoft's current partner-solutions catalog lists Plans2BIM as compatible with Archicad 26–29.

Workflow:
- upload PDF/PNG/JPEG architectural plan;
- set scale;
- AI detects;
- produces walls/windows/doors/spaces/slabs;
- edit properties;
- export IFC/DXF and quantities.

### Role

Use for:
- legacy/reference-plan ingestion;
- converting scanned/2D precedents to structured BIM candidates.

It does not solve architectural design logic, but it can reduce manual model recreation for donor/reference projects.

---

# 7. Office/project knowledge retrieval already has production products

## Nomic

Current Nomic platform is now AEC-specific and can:
- index drawings/specs/RFIs/project docs;
- search project archives;
- return cited answers;
- find past technical precedents;
- find details/assemblies/systems from previous projects;
- search architecture/structure/MEP together;
- review drawings;
- inspect IFC;
- perform quantity/property/space queries;
- surface cross-document conflicts.

It explicitly positions completed projects as a reusable institutional knowledge base.

Current individual pricing:
- free trial/limited use;
- $20/month Individual;
- $20 included AI usage per month.

Important account constraint:
Individual signup requires a work/company email; generic personal-email providers are not accepted.

### Why this matters

Our own "firm precedent RAG" should be blocked until Nomic is tested.

A very practical future workflow:

```
current design condition
      ↓
Nomic precedent search
      ↓
past details / assemblies / decisions / specs
      ↓
candidate donor solution
      ↓
SBIM Russian norm + geometry validation
      ↓
apply/adapt in Archicad
```

### Decision

**P1 LOW-COST TRIAL** before writing a custom multimodal project-history RAG system.

---

# 8. 2026 research confirms that "architectural logic" can be decomposed rather than entrusted to one giant model

## Multi-agent DRL space planning

A 2026 Journal of Building Engineering paper reports:
- multi-agent deep reinforcement learning;
- program-based layout generation;
- adjacency;
- orientation;
- energy efficiency;
- alternative generation in ~74 seconds;
- adaptation to changed design goals through fine-tuning.

This is a method reference, not a runtime dependency.

## Graph-rule floor planning

A 2026 Computers & Graphics paper:
- accepts adjacency/non-adjacency constraints;
- interior/exterior room conditions;
- circulation requirements;
- generates multiple dimensioned housing layouts.

Again, a direct precedent for deterministic/graph-driven layout generation.

## Architectural Spatial Knowledge Graphs

A very recent 2026 hospital-design study combines:
- authoritative regulations;
- information extraction;
- spatial knowledge graph;
- controlled updating;
- QA;
- BIM-assisted compliance.

This independently confirms our layered knowledge-graph architecture.

## Early-stage LLM + knowledge graph

Automation in Construction 2026 work extracts design logic from multimodal precedent cases and applies a knowledge graph for early-stage design assistance.

## Pattern language extraction

CAADRIA 2026 work converts 56 architectural precedent cases into 101 recurring patterns describing:
- context;
- spatial relationships;
- intent;
- strategy.

This is especially important:
the elusive "architectural logic" can be represented as **explicit reusable patterns**, not only as latent neural behavior.

## MCP knowledge continuity

CAADRIA 2026 research already demonstrates:
- multimodal processing;
- RAG knowledge base;
- subagents;
- MCP middleware;
- CDE;
- BIM automation;
- quality inspection;

for maintaining experiential AEC knowledge.

### Decision

Our "architect's brain" should combine:
- hard constraints;
- spatial graphs;
- precedent retrieval;
- explicit pattern language;
- design intent;
- deterministic solvers;
- specialist analysis;

rather than relying on a single LLM to "think like an architect" from scratch.

---

# 9. Revised architectural-logic stack

```
PROJECT PROGRAM / REQUIREMENTS
  dRofus / BIMQ / Russian rules
            |
            v
HARD LAYOUT CONSTRAINTS
  OR-Tools / FloorPlan6 methods
            |
            v
CANDIDATE SPATIAL CONFIGURATIONS
            |
       +----+-----+
       |          |
       v          v
TopologicPy      analysis engines
adjacency        daylight
circulation      structure
visibility       egress
access           energy
       |          |
       +----+-----+
            v
PRECEDENT / PATTERN LAYER
  Finch adaptive library
  donor projects
  Nomic
  pattern-language knowledge
            |
            v
DESIGN INTENT / QUALITY SCORE
  DIO / DDR / project predicates
            |
            v
RANK / REPAIR / SELECT
  Design Healing
  OpenMDAO / pymoo / OR-Tools
            |
            v
ARCHICAD 29
```

This is a much more credible "architect logic" architecture than a general LLM directly drawing walls.

---

# 10. Updated P0/P1 priorities

## P0 — after AC29 template/workstation priority

1. **FloorPlan6 local source audit**
   - run its sample;
   - connect to AC29 test file;
   - compare rules/solver architecture with our needs;
   - do not merge AGPL code before license decision.

2. **Finch AC29 beta plugin**
   - confirm v1.0.8/current compatibility;
   - test zone -> plan -> wall/door/zone round-trip;
   - test Free/Basic functionality;
   - evaluate whether Basic adaptive-library workflow alone is useful.

3. **TopologicPy**
   - build adjacency/movement/visibility graphs from one exported floor;
   - verify public/staff/service path separation and chokepoint metrics.

4. **Plans2BIM**
   - test one source floor-plan image/PDF if a suitable plan is available;
   - verify GUID/IFC/geometry quality on import.

## P1

5. Nomic Free/Individual for precedent/detail search.
6. Architechtures 7-day benchmark for residential LOD 200+ generation.
7. Compare Finch vs FloorPlan6 vs Architechtures outputs using one shared acceptance brief.

---

# 11. Shared architectural-layout acceptance benchmark

Do not judge by screenshots.

Create one standard brief:

- fixed exterior envelope;
- fixed structural grid;
- fixed core/stairs;
- required room program;
- hard min/max areas;
- daylight-required rooms;
- public/service separation;
- wet-core stacking;
- egress/walking limits;
- wall module;
- no wall through window;
- door clearance;
- target façade rhythm;
- furniture/equipment fit;
- no unusable sliver spaces.

Evaluate each engine:

```
FloorPlan6
Finch
Architechtures
our own current planner
future research methods
```

Metrics:
- hard-rule violations;
- adjacency score;
- circulation length;
- daylight access;
- geometric fragmentation;
- structural-grid compatibility;
- façade impact;
- equipment fit;
- number of manual corrections;
- time to usable AC29 model.

Primary KPI remains:
**human minutes to verified usable architectural result.**

---

# 12. Roadmap removals after checkpoint 22

Custom implementation is now blocked pending reuse evidence for:

- generic apartment floor-plan solver;
- generic room adjacency solver;
- generic circulation graph engine;
- generic visibility graph engine;
- generic firm plan-library matching;
- generic architectural precedent RAG;
- generic 2D-plan-to-BIM conversion;
- first-pass AI floor-plan neural model;
- first-pass "architectural pattern extraction" pipeline.

Likely custom work remains:
- Russian rules and mappings;
- our exact architectural quality/intent predicates;
- AC29 hot causal graph;
- modular-construction dimensions;
- project-specific façade/structural/detail compatibility;
- integration adapters;
- ranking policy.
