# Architectural AI checkpoint 19 — change propagation, design intent, optimization, detail reuse and substitution

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Executive conclusion

The "remaining unique core" shrank again.

This pass specifically attacked the parts we still assumed were probably ours:
- causal/change graph;
- design intent;
- design decision memory;
- minimum-disruption redesign;
- multidisciplinary optimization;
- construction detail selection/generation;
- reuse of office/project history;
- product/material substitution;
- cross-engineering orchestration.

Result:

**Most of the algorithms and semantic models already exist.**

The likely SBIM value is now increasingly:
1. connect them to Archicad 29;
2. feed them Russian requirements/project semantics;
3. choose which engine executes which task;
4. keep canonical project identity and provenance;
5. define project-specific priority/impact weights and architectural policies.

---

# 1. Cambridge Advanced Modeller 2 — direct match for our change-propagation problem

The University of Cambridge already provides **CAM 2**, a desktop tool specifically for:
- dependency modelling;
- change modelling;
- process modelling;
- visual analytics.

CAM is free for:
- research;
- teaching;
- evaluation.

Commercial evaluation is also allowed; commercial-use conditions require contact.

## Change Prediction Method (CPM)

CAM's Change Modelling toolbox implements the **Change Prediction Method**.

The model is a dependency structure matrix (DSM):
- nodes = components/subsystems;
- edges = dependencies;
- each dependency has:
  - probability/likelihood that a change propagates;
  - impact if it propagates.

CAM then performs stochastic multi-step propagation and produces:
- Change Propagation Tree;
- In/Out Risk Portfolio;
- combined propagation likelihood/impact;
- path analysis;
- multi-initiator change analysis.

This is almost exactly the conceptual tool we were describing when the user said:
"a wall move always affects area, can affect slabs, structure, windows, adjoining zones, floors, nodes, etc."

## Important scaling nuance

CAM's tutorial recommends a model with fewer than ~50 manually managed components/subsystems because populating probability/impact links becomes costly, and propagation path computation grows quickly.

Therefore CAM is **not** the live per-element hot graph for 5,000+ BIM objects.

Best role:

```
detailed Project Graph
        ↓ aggregation
architectural/system dependency classes
        ↓
CAM CPM
        ↓
change propagation risk / critical subsystems
```

Examples of CAM-level nodes:
- structural grid;
- façade module;
- wet-core stack;
- vertical circulation;
- room program cluster;
- slab system;
- MEP riser system;
- envelope system;
- loading/logistics;
- fire compartments;
- daylight façade;
- cost;
- LCA.

## Integration

CAM:
- imports/exports CSV;
- supports plugins/modules;
- provides custom palettes/model types;
- provides simulation/analysis framework;
- can be extended in Java;
- supports distributed simulation experiments.

This means we can first **use CAM as the reference/validation engine** for our change-impact model rather than invent CPM.

### Decision

**P0 RESEARCH TOOL / ALGORITHM REUSE.**

Do not invent change-propagation theory.

Possible production choices:
- use CAM externally for deep L0/L1 change-risk analysis;
- or reimplement its known CPM/DSM method in our existing graph runtime after validation.

If reimplemented, status is:
`REIMPLEMENT_KNOWN_METHOD`, not invention.

---

# 2. Lattix — industrial DSM/dependency platform for larger graphs

Lattix is a commercial architecture/dependency analysis platform built around DSMs.

Current capabilities include:
- scalable dependency matrices;
- system hierarchy;
- impact analysis;
- architecture rules;
- layering;
- cycle detection;
- partitioning/clustering;
- conceptual architecture diagrams;
- custom data import from Excel/LDI;
- systems-engineering/SysML model analysis.

This is relevant because CAM is research-friendly but intentionally works best with coarse models.

Lattix has industrial experience on very large dependency systems.

### Decision

**REFERENCE / OPTIONAL COMMERCIAL BENCHMARK.**

Do not buy by default.
First test CAM + our graph.
Lattix is useful to validate whether our dependency graph requirements are actually generic systems-engineering requirements rather than new AEC algorithms.

---

# 3. Design Intent Ontology — we do not need to invent our own base intent ontology

The existing **Design Intent Ontology (DIO)** already defines a generic semantic model for:

- Design Intent
- Design Goal / Issue
- Design Requirement
- Constraint
- Assumption
- Heuristic
- Alternative Solution
- Mandated Solution
- Evaluation
- Evidence
- Argument
- Justification
- Design Decision
- Design Artifact
- Status

Relationships include:
- hasAlternativeSolution;
- hasMandatedSolution;
- hasConstraint;
- hasEvidence;
- hasJustification;
- usesAssumption;
- usesHeuristic;
- contradicts;
- refines;
- leadsTo;
- governsDesign;
- fulfillsRequirement.

DIO is linked to **W3C PROV**.

This is strikingly close to our proposed DDR / Design Intent graph.

## Revised intent architecture

Do NOT define:
`SBIMDesignIntent, SBIMAlternative, SBIMEvidence, ...`
from zero.

Instead:

```
DIO
+ PROV-O
+ BCF
+ IFC/BOT/bSDD
+ OPM temporal state
+ custom SBIM architectural predicates
```

Custom predicates can be limited to domain concepts such as:
- PRESERVE_FACADE_RHYTHM;
- KEEP_WET_CORE_STACK;
- ALIGN_STRUCTURAL_GRID;
- PRESERVE_PRIMARY_AXIS;
- STACK_LOAD_BEARING_WALL;
- MAINTAIN_PUBLIC_SERVICE_SEPARATION;
- PRESERVE_MODULE;
- MAINTAIN_MINIMUM_DISRUPTION.

### Decision

**ADAPT DIO, DO NOT INVENT BASE DESIGN-INTENT ONTOLOGY.**

---

# 4. Decision interaction itself is already formalized in systems-engineering research

Existing research defines a **Decision Interaction Ontology** for:
- hierarchical decision networks;
- horizontal and vertical interactions;
- reusable/executable decision workflows;
- multiple interaction patterns among decisions.

There is also older Design Rationale / Kuaba / IBIS / NDR research.

Consequence:
our project-decision graph should be an **AEC specialization of known decision-rationale patterns**.

Our custom work:
- bind decisions to BIM GUIDs, normative IDs and analysis outputs;
- define architectural significance/priority;
- connect accepted decisions to validity envelopes.

Not custom:
- basic decision/rationale ontology.

---

# 5. Recent BIM research already formalizes design intent as something continuously verifiable

Recent building-design research explicitly represents design intent as:
- argument;
- goal;
- substitutions/variables;
- domain/product-level formulas;

and re-runs intent verification when the BIM model changes.

Other recent "Cloud BIM" research proposes:
- discipline-specific models;
- knowledge graphs;
- semantic links across disciplines;
- AI recognition of geometry/topology/relationships;
- automatic maintenance of cross-model consistency;
- enriched design intent.

This is extremely close to our original "global project causal graph" concept.

### Decision

Use this research as reference architecture.
Do not claim the semantic-consistency concept is unique.

---

# 6. OpenMDAO — mature engine for coupled multidisciplinary design

OpenMDAO is an open-source framework for multidisciplinary design, analysis and optimization.

Its purpose is specifically to couple numerical models of complex engineering systems and optimize them together.

Relevant capabilities:
- hierarchical coupled systems;
- design variables;
- constraints;
- multiple analysis components;
- analytic/finite derivatives;
- sparse coupled models;
- feasibility search;
- solver/optimizer integration.

A current feature can explicitly try to find a feasible design point by minimizing constraint violations.

## Why this matters

We were preparing our own orchestration logic like:

```
wall move
 -> area
 -> daylight
 -> structure
 -> energy
 -> cost
 -> MEP
 -> compliance
 -> rank
```

OpenMDAO already provides the generic MDO coupling framework.

Potential deep-analysis architecture:

```
OpenMDAO Problem
 |
 +-- Geometry/Archicad component
 +-- CYPE urban component
 +-- Ladybug/Honeybee component
 +-- structural FEA component
 +-- LCA component
 +-- cost component
 +-- compliance component
 |
 -> hard constraints
 -> performance objectives
 -> feasible candidates
```

### Decision

**P0/P1 PROTOTYPE FOR DEEP PROJECT COMPILER.**

Do not write a generic multidisciplinary optimization engine.

---

# 7. pymoo / Optuna / Wallacei — candidate ranking/search is commodity

For multi-objective search:

## pymoo
Open source and implements:
- NSGA-II / NSGA-III;
- MOEA/D;
- GA;
- differential evolution;
- CMA-ES;
- PSO;
- Pareto decision support.

## Optuna
Supports constrained multi-objective optimization and efficient samplers.

## Wallacei
Existing Grasshopper evolutionary multi-objective engine with:
- Pareto exploration;
- clustering;
- population analytics;
- solution reconstruction.

Because Archicad 29 has a Grasshopper Live Connection, Wallacei can potentially be used for geometry-driven design exploration without custom optimizer code.

### Decision

Our code should define:
- variables;
- hard constraints;
- objectives;
- architectural disruption penalty.

It should **not implement optimization algorithms**.

---

# 8. Minimum-disruption redesign now has an obvious known-method stack

We already found Design Healing.

Combining this pass, the minimum-disruption problem has a ready architecture:

```
violation / user change
       ↓
detailed Project Graph
       ↓
CAM/DSM change-risk analysis
       ↓
relevant subgraph / impact cone
       ↓
Design Healing candidate variables
       ↓
OpenMDAO / pymoo / OR-Tools / Z3
       ↓
hard-feasible alternatives
       ↓
distance-from-original + intent score
       ↓
Pareto / ranked candidates
```

None of the generic algorithms above need to be invented.

Our unique part is only:
- project-specific dependency construction;
- weights;
- architectural-intent scoring;
- translation of candidate changes into Archicad operations.

This is a major reduction in custom algorithmic risk.

---

# 9. Detail intelligence — even this is largely known

## NADIA

Published architectural-detailing research already implements:
- natural-language design detailing;
- explicit separation of wall-layer specification from layer creation;
- LLM-BIM chaining;
- engineering-rule guidance;
- automatic detailed wall creation.

Reported tests include:
- 240 / 1,920 wall-detailing tasks;
- ~83% average logically coherent detail generation;
- ~98.5% compliance accuracy for the tested thermal requirement.

This is not production-ready, but the method exists.

## Generalized LLM-Augmented BIM framework

The same research line proposes a generic sequence:

`interpret → fill → match → structure → execute → check`.

This is almost exactly the agent pipeline we have been designing.

### Decision

For future detail-generation code:
**copy known interaction architecture, adapt to Archicad 29, do not invent a new agent chain.**

---

# 10. BIM Library Transplant — learn detailing from previous projects instead of encoding everything

A 2024 framework does almost exactly what we need for "teach AI how this architect/office details projects".

Method:
1. extract high-LOD objects from a donor BIM model;
2. match them with low-LOD objects in a recipient model;
3. transplant/replace recipient content.

The published Revit implementation uses an ML classifier for matching.

Reported results:
- detail-time reduction approximately 60–70%;
- matching accuracy roughly 65–80%.

## Importance for SBIM

Instead of building a universal detail generator first:

```
verified old Archicad projects
          ↓
Detail / object donor library
          ↓
semantic + geometric matching
          ↓
new low-LOD project
          ↓
candidate transplant
          ↓
Russian rule / interface checks
          ↓
accepted project detail
```

This is far more aligned with how architects actually work:
reuse successful previous solutions and adapt them.

### Decision

**HIGH-VALUE RESEARCH METHOD.**
Reimplement for Archicad only after searching for a ready office-history/detail system.

---

# 11. Ready products already cover detail retrieval

## ARKI
Current AEC product category:
- visual AI search across a firm's historical Revit / AutoCAD / PDF data;
- searchable/reusable detail archive;
- live BIM insertion through its Revit route.

Role:
reference/product option for "firm memory".

## BIMsmith Detail Shelf
- thousands of manufacturer details;
- AI-powered detail discovery.

## ARQYN
Current product claims:
- drawing issue detection;
- relevant detail matched to each issue;
- downloadable detail in PDF/JPEG/DWG.

This means the problem:
"find the right existing detail for this condition"
is already a product category.

## Russian strategy

Use:
- TechExpert TPD;
- verified internal Archicad donor projects;
- manufacturer Russian details;
- BIMsmith/details as international references.

Build:
- applicability;
- matching;
- Russian compliance filters;
- Archicad placement/parametric adaptation.

Not:
- global detail archive/search.

---

# 12. Product substitution — search/filter/compare already exists

## NBS Source

NBS Source already supports:
- free product-data access;
- structured manufacturer data;
- technical/property filtering;
- certification/sustainability filtering;
- product comparison;
- specification link;
- BIM content.

NBS explicitly describes generic BIM objects being used early and later replaced by manufacturer-specific objects.

It also has an Archicad plugin for model ↔ specification coordination.

This is almost the lifecycle we described:
`generic placeholder -> requirements known -> manufacturer product substitution`.

## BIMsmith Forge

BIMsmith Forge is free and provides:
- 500,000+ Revit material records according to current help pages;
- complete wall/floor/ceiling/roof assembly configuration;
- generic vs manufacturer layer selection;
- filters such as fire rating/STC;
- system starters;
- product updates/discontinuation tracking.

It is Revit-centric, so not our direct AC29 runtime.

But its product/assembly selection model is reusable as an architectural pattern.

## Russia

For Russian projects:
- ETIM/bSDD semantics;
- BIMLIB;
- BIMobject;
- TechExpert TPD;
- manufacturer catalogues.

### Revised substitution engine

```
required class
 + dimensions
 + performance
 + certifications
 + fire/acoustic/thermal
 + project region
 + geometry clearance
 + cost/carbon constraints
        ↓
catalog adapters
        ↓
filter
        ↓
rank
        ↓
candidate product/assembly
        ↓
Archicad replacement + impact audit
```

Again, custom work is the requirement compilation and project-fit score, not catalog/database/search infrastructure.

---

# 13. BHoM deserves a deeper role than previously assigned

The **Buildings and Habitats object Model** is already an open-source transdisciplinary AEC integration architecture.

Core structure:
- object model;
- Engine;
- Adapter;
- UI.

Its own documented philosophy is explicitly:
**do not reinvent external engineering tools; create adapters and shared object models.**

That is almost exactly our revised SBIM strategy.

Current ecosystem includes adapters/toolkits for:
- Revit;
- ETABS;
- SAP2000;
- Robot;
- RFEM;
- GSA;
- Rhino;
- Speckle;
- IES;
- Ladybug Tools;
- LCA/carbon;
- SQL/HTTP/Excel/Grasshopper and more.

Recent BHoM releases also include:
- Diffing Engine;
- Verification Engine;
- adapter push priorities;
- Versioning Toolkit.

## Critical limitation

No active Archicad toolkit was verified.

Therefore BHoM is not our AC29 executor.

But it may be an excellent **engineering-domain interchange layer behind Archicad**.

Potential architecture:

```
Archicad 29
  ↓ IFC / Speckle / Grasshopper / thin adapter
BHoM objects
  ├ structural tools
  ├ environmental tools
  ├ LCA
  ├ verification/diff
  └ engineering data
```

### Decision

**P0/P1 ARCHITECTURE AUDIT.**

Before writing many engineering adapters, inspect whether BHoM already has the target software adapter.

---

# 14. Revised causal/intent stack

We no longer need one enormous new "mega graph" implementation with custom semantics for everything.

Proposed composition:

## Object/topology state
- IFC
- BOT
- bSDD
- OPM
- BHoM objects where useful

## Decision / intent
- DIO
- PROV-O
- BCF
- immutable DDR pattern

## Change propagation
- DSM / CPM method
- CAM as reference tool
- Project Graph exact dependencies

## Compliance
- Russian canonical requirements
- existing compliance executors

## Optimization
- OR-Tools/Z3 for exact discrete constraints
- OpenMDAO for coupled analysis
- pymoo/Optuna/Wallacei for multi-objective exploration

## Repair
- Design Healing method

The true custom graph edges should only represent relationships that no standard covers.

---

# 15. What is newly removed from our custom roadmap

Block custom implementation pending reuse tests for:

- generic change-propagation risk algorithm;
- generic DSM engine/UI;
- base Design Intent ontology;
- base Design Decision ontology;
- generic multidisciplinary optimization engine;
- generic multi-objective optimization;
- generic detail-search engine;
- universal detail archive;
- generic product-search/comparison engine;
- generic assembly configurator;
- generic office-history detail retrieval;
- generic engineering adapter framework.

---

# 16. Highest-value new experiments

## CHANGE-01 — Cambridge Advanced Modeller

Install CAM 2 separately after AC29 template priority is closed.

Create a coarse 20–40 subsystem model from our project:
- façade;
- structural grid;
- slabs;
- cores;
- wet rooms;
- daylight windows;
- MEP risers;
- fire compartments;
- room program;
- construction systems.

Run CPM for:
- move wall;
- enlarge room;
- resize window;
- change structural span.

Compare predicted propagation with our manually expected dependency chains.

## INTENT-01 — DIO prototype

Represent one real architectural decision:
"maintain façade rhythm while enlarging a tenant zone."

Use:
- requirement;
- issue;
- alternatives;
- constraints;
- evidence;
- mandated solution;
- design decision;
- affected BIM artifacts.

Check whether DIO + custom architectural predicates can represent it without a new ontology.

## MDO-01 — OpenMDAO prototype

One variable:
window width.

Coupled outputs:
- daylight;
- façade intent penalty;
- thermal/energy;
- module compatibility;
- room requirement.

Find a feasible candidate.

If this works, the deep-project compiler can use a mature MDO substrate.

## DETAIL-01 — donor library transplant

Take:
- one high-detail Archicad wall/window junction from an existing verified project;
- one low-detail recipient condition.

Define matching features:
- wall system;
- opening type;
- thickness;
- fire/thermal requirement;
- orientation/interface.

Test whether donor-detail retrieval can replace generating a detail from zero.

---

# Strategic conclusion

After checkpoint 19, even the supposedly unique core is no longer one new algorithm.

The likely product architecture is:

**existing semantic standards + known systems-engineering methods + existing BIM/engineering/compliance software + a thin Archicad/Russian/project-specific orchestration layer.**

The true invention burden is now much lower.

That is exactly the direction we want.
