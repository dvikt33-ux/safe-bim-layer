# Architectural AI checkpoint 23 — AC29 control plane, facade/opening logic and dependent-element automation

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Context carried forward

This checkpoint incorporates:
- parallel-chat Fast Project Compiler checkpoint 20;
- open compliance/semantic graph checkpoints 20–21;
- floor-plan/spatial/precedent checkpoint 22.

No architectural reset is proposed. The goal remains:
**minimum human time to a verified, architecturally coherent AC29 project.**

This pass attacked:
- the AC29 execution/control plane;
- documentation automation;
- window/door placement logic;
- façade/window optimization;
- dependent construction elements;
- equipment/MEP coordination;
- local AC29 productivity tools.

---

# 1. Archicad-MCP (alesdev88) is a major new AC29 reuse candidate

Repository:
`alesdev88/Archicad-MCP`

Current observed release documentation: v0.7.1.
License: MIT.
Target: Archicad 29 on Windows/macOS.

This project is much more mature and safety-oriented than a generic MCP wrapper.

## Current documented capabilities

### Curated QA
- delivery-readiness YAML rules;
- pass/fail scores;
- failing element GUIDs;
- highlight failures;
- create issues;
- IFC readiness.

### Live model operations
- find elements;
- search definitions;
- element data;
- create elements;
- move/delete;
- selection;
- project info;
- attributes;
- issues/BCF;
- publish.

### Full command gateway
Current documentation reports a verified command surface of:
- 309 official + Tapir commands;
- 138 classified reads;
- 171 classified writes.

Anything unrecognized is treated as a write for safety.

### Write safety
- curated writes are dry-run by default;
- destructive operations require explicit confirmation;
- scripts plan a changeset before applying;
- writes/readback are separated.

This is directly compatible with our transaction-oriented design.

### Property/classification definitions
The server can update:
- property definitions;
- classification systems/items;
- defaults;
- expressions;
- classification availability;
- enum options;

while preserving GUIDs where semantics allow.

This could remove a large amount of template-definition automation code.

### Teamwork
- reserve/release elements;
- reports indirect reservations;
- integrates with Tapir.

### GDL pipeline
It can:
- ingest OBJ/3DS meshes;
- create HSF;
- compile with Archicad LP_XMLConverter;
- build GSM library parts;
- deploy/reload/place;
- render a preview;
- remove the test instance unless kept.

This means a generic "external object -> Archicad object" pipeline already exists.

### Schedule scheme tooling
Archicad does not expose schedule-scheme authoring through the standard JSON/Tapir path.
This project uses the existing Archicad XML export/import round-trip to:
- read schedule scheme;
- edit columns/bindings;
- validate property/GDL/builtin bindings;
- preserve unknown XML fields conservatively.

Criteria editing remains limited because undocumented numeric codes are still being mapped.

## Critical AC29 warning

The project documents that Archicad 29's `GetPropertyValuesOfElements` can crash Archicad, even for a small request.

This is strategically important for us.

We already have a proven native C++ Model Dump/read path that read:
- full geometry;
- properties/materials;
- stories/host relationships;
- evaluated bodies/faces;

without relying on that fragile JSON property call.

### Revised AC29 read/write split

Preferred until benchmarked otherwise:

```
READ / PROJECT STATE
  our native C++ Model Dump / minimal observer
  +
  safe targeted APIs

WRITE / TOOL EXECUTION
  Archicad-MCP / Tapir / HuskyBIM
  with dry-run/readback
  +
  native C++ only for proven gaps
```

This may be safer than forcing one provider to own both read and write.

## Decision

**P0 AC29 CONTROL-PLANE BENCHMARK.**

Before extending our generic control server, compare:
- HuskyBIM;
- Archicad-MCP;
- Archi Automate;
- Tapir;
- our native Add-On.

Use shared acceptance tests, not tool-count marketing.

---

# 2. Tool count is not the selection metric

Different systems expose capabilities at different granularities.

A provider with 700 narrow tools is not automatically more capable than one with:
- curated semantic operations;
- a full generic command gateway;
- safe changesets;
- readback;
- scripting;
- full vendor API access.

Provider score must remain:

1. semantic fidelity;
2. safety/transaction/readback;
3. coverage;
4. latency;
5. stability;
6. openness/license;
7. maintenance;
8. cost.

Tool count is diagnostic only.

---

# 3. AC29 documentation automation is more reusable than assumed

## Native Archicad
Current Archicad already has:
- Interactive Schedules;
- editable schedule fields that update model data;
- automatic exterior dimensioning;
- opening dimensions;
- view/layout placement.

## Archicad-MCP
Adds:
- schedule XML read/edit/validate workflow;
- publish;
- issue/BCF automation;
- property/classification-definition edits.

## SimpleAddon AC29

A current AC25–29 suite provides focused automation for:
- section/elevation associative dimensions;
- zone labels with automatic updates;
- exact window/door positioning;
- travel-distance documentation;
- gutters/downspouts;
- ridge tiles;
- roof supports;
- layer control.

The bundle has a 7-day trial.

### Important conclusion

Do not implement an all-purpose documentation engine.

Build only semantic orchestration around:
- native schedule/dimension functions;
- existing focused plugins;
- XML schemes;
- Publisher.

---

# 4. Window and door placement should be split into geometry + architectural/façade constraints

The user's criticism was correct:
a window cannot be "moved until daylight passes" in isolation.

A window affects:
- room daylight/view;
- façade rhythm;
- masonry/module;
- pier width;
- structural lintel zone;
- MEP/equipment conflicts;
- furniture/equipment;
- exterior appearance;
- adjacent windows and floors.

Likewise a door affects:
- room circulation;
- leaf swing;
- clearances;
- accessible maneuvering;
- furniture/equipment;
- escape route;
- wall usable length.

## Existing AC29 placement utility

SimpleAddon's current AC29 `Set Window & Door Position` can:
- place/move openings at an exact offset from a wall corner;
- center an opening on a wall segment.

This is a useful commodity execution primitive for our "module-safe placement" layer.

### Role

Do not ask AI for arbitrary XY.

AI/solver produces a semantic placement:
- host wall;
- anchor side;
- module-safe offset;
- opening width/height;
- sill/head;
- hand/facing;
- required pier envelope.

Execution can then use an existing placement primitive or native API.

---

# 5. Façade/window optimization is already a mature research field

Recent 2026 work removes the need to invent the performance algorithms.

## ViewOpt (Building and Environment 2026)

A current framework optimizes window-view quality across façades using:
- 3D urban context;
- computer vision;
- rule-based methods;
- Bayesian optimization;
- deep reinforcement learning;
- coordinated window decisions across multiple units.

This is directly relevant to preserving façade-wide coherence instead of optimizing one room/window independently.

## Multi-objective window/façade studies

Current 2026 studies jointly optimize:
- window geometry;
- daylight;
- glare;
- energy;
- thermal comfort;
- PV/shading.

Another modular-façade study reports surrogate models reducing repeated environmental-evaluation time by about 90%, combined with NSGA-II.

## Multi-agent window optimization

CAADRIA 2026 research explicitly combines:
- human design intent;
- environmental performance;
- window placement/dimensions;
- simulation;
- multi-agent reasoning.

### Decision

Do not implement our own daylight/energy/window optimizer.

Use:
- Honeybee/Radiance/EnergyPlus/CYPELUX;
- existing optimization engines;
- project-specific façade grammar/intent constraints.

---

# 6. Façade grammar should be a project constraint, not an after-the-fact aesthetic score

The correct window workflow is:

```
room requirement
  daylight / view / ventilation / egress
       |
       v
candidate opening envelope
       |
       +--> masonry/module/pier constraints
       +--> structural/lintel constraints
       +--> equipment/furniture clearance
       +--> façade grammar
       +--> cross-floor alignment
       +--> environmental simulation
       |
       v
feasible opening candidates
       |
       v
rank by architectural intent + performance
```

Façade grammar can include:
- horizontal datum bands;
- vertical axes;
- bay/module;
- opening family/type;
- allowed width/height families;
- symmetry or deliberate asymmetry;
- sill/head lines;
- solid/void ratios;
- corner rules;
- historic-context constraints;
- cross-storey stacking.

This should become part of Design Intent / ACP semantics.

---

# 7. Dependent construction elements should be explicit reactive dependents

A useful current precedent comes from production BIM plugins such as BIMix Lintels:
- openings determine lintel span;
- lintel bearings are parameterized;
- conflicts with columns/wall ends are checked;
- when the door/level changes, the lintel follows;
- rerunning replaces rather than stacks duplicates.

Although this implementation is Revit-specific, the architectural pattern is exactly correct.

## SBIM dependency pattern

```
Door/Window
   ↓ dependent
Lintel / header / reveal / sill / flashing / finish / insulation return
```

Dependent objects should have:
- `host/source GUID`;
- `derivation recipe`;
- `allowed envelope`;
- `replace-not-duplicate policy`;
- `invalidation trigger`.

This is more robust than treating every detail component as independent geometry.

### AC29 sources for implementation

- native objects/GDL;
- ACP;
- PARAM-O;
- existing roof/accessory plugins;
- custom native gap only where required.

---

# 8. Existing AC29 accessories reinforce the "reactive dependent" strategy

Current SimpleAddon AC29 examples include:

- gutter follows selected roof/edges;
- downspout derives size/position from gutter + fixing point;
- ridge tiles derive placement from selected roof;
- roof supports derive placement along a polyline;
- zone labels update when source zones change;
- travel distance updates when the path changes.

Graphisoft Accessories/Goodies historically provide similar derived modeling patterns, e.g. wall framing around openings.

These are concrete examples of a broader architecture:
**source object → derived/dependent object → automatic update.**

We should generalize the semantic dependency model, not reimplement every accessory.

---

# 9. Equipment should remain requirement-driven; geometry is a second step

dRofus already maintains:
- room requirements;
- room templates;
- equipment requirements;
- equipment planning;
- Archicad/Revit integration;
- validation of design vs requirement.

Therefore the architectural order should be:

```
room function
  ↓
required equipment set
  ↓
equipment dimensions + access/maintenance envelopes
  ↓
fit/layout test
  ↓
only if no feasible arrangement:
     substitute equipment
     OR adjust room/wall
```

This matches the user's stated influence hierarchy:
equipment movement/replacement is normally cheaper than moving a wall.

### Candidate resolution order

1. move/reorient equipment;
2. choose equivalent smaller/different product;
3. change door swing/position if legal and architecturally acceptable;
4. modify non-critical internal partition;
5. modify high-impact wall only after impact analysis.

This should be encoded into repair cost/priority, not left to an LLM's intuition.

---

# 10. MEP constructability reasoning is also becoming reusable

A July 2026 Automation in Construction paper implements:
- MEP scene graphs;
- textual MEP rules -> knowledge graph;
- graph matching/reasoning;
- multi-agent checking;

and reports 92% accuracy on practical project cases.

Other current research handles:
- automated pipe routing under clearance constraints;
- multi-objective plant-room coordination;
- modular corridor MEP optimization.

### Consequence

Our MEP architecture should remain:

```
requirements/system semantics
       ↓
existing MEP solver / native AC29 / CYPE / future specialized engine
       ↓
graph-based constructability audit
       ↓
SBIM change impact
```

Not:
"GPT manually routes every pipe."

---

# 11. New AC29 productivity shortlist

After the template/workstation layer is stable, a focused AC29 trial batch should include:

## Control/execution
- Archicad-MCP v0.7.x
- HuskyBIM
- Archi Automate

## Architectural layout
- FloorPlan6
- Finch AC29 beta

## Spatial logic
- TopologicPy

## Focused productivity
- SimpleAddon:
  - Set Window & Door Position
  - Travel Distance
  - Place Dimensions
  - Zone Label
  - selected roof accessories only if useful

Do not install every plugin permanently.
Each must pass a measured workflow benchmark.

---

# 12. Revised AC29 execution architecture hypothesis

```
                     USER / GPT
                        |
                semantic operation
                        |
                  provider registry
        +---------------+----------------+
        |               |                |
        v               v                v
 Archicad-MCP        HuskyBIM       focused add-ons
 / Tapir gateway                        |
        |                               |
        +---------------+---------------+
                        |
                   ARCHICAD 29
                        |
             safe native read/observer
                 Model Dump / GUID
                        |
                 Coverage Signatures
```

The native Add-On becomes smaller:
- reliable hot-state read;
- event/dirty tracking;
- exact geometry/provenance;
- only write gaps that external layers cannot execute reliably.

This is a much better return on the two weeks of native work than deleting it:
the work becomes the trustworthy sensor/kernel instead of the whole automation platform.

---

# 13. New roadmap removals

Custom implementation is blocked pending reuse benchmark for:

- generic AC29 MCP/control server;
- generic Archicad API gateway;
- generic schedule-scheme editor;
- generic GDL mesh-to-object pipeline;
- generic exact opening-position UI;
- generic travel-distance annotation tool;
- generic section/elevation dimension tool;
- generic roof gutter/ridge accessory placement;
- daylight/window environmental optimization algorithm;
- MEP generic constructability graph algorithm.

Likely custom remains:
- safe AC29 hot-state observer/read kernel;
- semantic opening constraints/module logic;
- façade grammar/intent;
- Russian masonry/module tables;
- repair-cost hierarchy;
- cross-provider orchestration;
- project causality/invalidation.
