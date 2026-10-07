# Architectural AI checkpoint 15 — free/open project backbone, spatial logic, LCA and model CI/CD

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29

## Executive conclusion

The reuse surface shrank again.

This pass found credible existing solutions for four more major SBIM areas:

1. **Free/open BIM project backbone / issue management** — OpenProject BIM Community Edition.
2. **Model version/event automation** — Speckle + Automate.
3. **Architectural spatial logic / visibility / circulation analysis** — depthmapX / Space Syntax tools.
4. **Lifecycle/carbon analysis directly from Archicad 29** — One Click LCA plugin.
5. **Product-data semantics** — ETIM MC + bSDD, reducing the need for a custom manufacturer-property ontology.

This means we should not build:
- a project-management/BCF server;
- a generic model-CI/CD event system;
- a space-syntax engine;
- an LCA engine;
- a generic product parameter dictionary.

---

# 1. OpenProject BIM — free self-hosted alternative to a custom CDE for the MVP

OpenProject Community Edition is:
- open source;
- self-hosted;
- free of charge;
- unlimited users/projects;
- REST API;
- Docker/on-prem capable.

Its BIM module supports:
- IFC2x3 / IFC4 model upload;
- multiple IFC models;
- integrated web viewer;
- BCF issue creation/import/export;
- BCF API 2.1;
- issues integrated with normal work packages/tasks;
- Gantt/boards/assignments around BIM issues.

OpenProject explicitly states that the BIM functionality can be used free in the Community Edition.

## Why this matters

We previously treated Catenda as the likely mature CDE reference, but Catenda's pricing is project-value based and unsuitable for a solo/student MVP.

OpenProject gives us a credible **zero-cost project/issue/document/task backbone**.

Potential AC29 flow:

```
Archicad 29
   ↓ IFC / BCF
OpenProject BIM
   ↓
tasks / issues / viewpoints / schedule
   ↓ REST / BCF API
SBIM / ChatGPT
```

## Limitations

OpenProject is not:
- a live Archicad execution layer;
- a project semantic graph;
- a normative engine;
- a sophisticated IFC modification platform.

It is best considered:
**free project coordination + issue/task/CDE-lite layer.**

### Decision

**P0/P1 FREE PROTOTYPE CANDIDATE.**

Before building our own project issue/task server, test OpenProject BIM.

---

# 2. Speckle — model data hub + event-driven automation already implements "CI/CD for BIM"

Speckle currently supports Archicad 27, 28 and 29 through its connector.

Its Archicad connector turns model data into connected data-rich assets and exposes:
- properties;
- classifications;
- material quantities;
- cross-tool exchange/analytics.

## Speckle Automate

Automate is explicitly described by Speckle as **CI/CD for 3D/AEC models**.

A new model version can trigger functions for:
- QA;
- code compliance;
- integrity checks;
- logical analysis;
- clashes;
- reports;
- diagrams;
- deliverables.

The Automate SDK provides the trigger context:
- project ID;
- model ID;
- version ID;
- server URL;
- automation/run/function IDs.

Functions are packaged and deployed as repeatable automation units.

Webhook/event workflows are already part of the platform.

## Why this matters

Our planned:
`model revision -> dirty event -> run checks -> persist results`

already exists at a generic model-data level.

We still need our AC29 live event bridge for sub-second authoring feedback if no external connector exposes it, but for:
- publication events;
- milestone audits;
- model-version checks;
- CI-style regression;

Speckle can eliminate substantial custom infrastructure.

## Important current limitation

Speckle Automate is version/event based and stateless by design.

It is **not a complete ordered workflow/DAG engine** by itself. Current community guidance for chained flows uses model/version state patterns or external workflow orchestration.

Therefore:
- use Automate for independent checks/functions;
- use Process Compose/Temporal or our thin orchestration policy if strict multi-step sequencing becomes necessary.

### Decision

**REUSE for model-version CI/CD and cross-tool data.**
Do not write a generic model automation platform from scratch.

---

# 3. depthmapX / Space Syntax — a ready engine for circulation, visibility and spatial hierarchy

depthmapX is open-source multi-platform spatial network analysis software used in architecture and urban design.

It supports:
- visibility graph analysis;
- isovists;
- network/graph analysis;
- agent-based analysis;
- building-scale through city-scale spatial analysis.

At building scale it can derive:
- visual accessibility;
- connectedness;
- integration/depth-like metrics;
- intervisibility graphs;
- movement-related spatial structure.

The QGIS Space Syntax Toolkit also provides a front-end for spatial-network/statistical analysis.

## Why this matters to the "architect's logic" problem

A major user concern is that AI must understand:
- corridor quality;
- dead ends;
- visual connections;
- awkward zoning;
- public/private/service circulation;
- spatial hierarchy;
- entrances/frontages and pedestrian movement.

Not all of this should be encoded as hand-written heuristics.

Space Syntax provides quantitative architectural metrics that can become features in our candidate ranking.

Example:

```
candidate plan
  ↓
topology / circulation graph
  ↓
depthmapX metrics
  ↓
SBIM architectural score
  ↓
compare alternatives
```

## Limits

Space Syntax does not decide:
- Russian code compliance;
- structural feasibility;
- architectural style;
- construction details.

It is a **metric/analysis engine**, not the architect.

### Decision

**REUSE / integrate metrics.**
Do not invent visibility-graph / isovist / spatial-integration algorithms.

---

# 4. One Click LCA — Archicad 29 already has a current plugin

One Click LCA currently provides a dedicated Archicad 29 plugin.

The plugin exports Archicad bill-of-material data into the LCA platform.

This directly covers a major part of:
- embodied carbon;
- lifecycle environmental assessment;
- material impact comparison.

## Why this matters

If SBIM generates alternatives, environmental performance should be one candidate score.

We should not build:
- EPD database;
- carbon-factor database;
- lifecycle calculation engine;

from scratch.

Use One Click LCA or another established LCA engine.

Potential flow:

```
Archicad alternative
   ↓ BOM
One Click LCA
   ↓
carbon/environment result
   ↓
SBIM candidate score
```

## Limitation

Requires suitable One Click LCA account/license for project import/calculation.

### Decision

**REUSE if licensing fits.**

For a free/open fallback, Ladybug/Honeybee handles environmental simulation but is not an EPD/LCA database replacement.

---

# 5. ETIM MC + bSDD — manufacturer/product semantics already have a standard path

ETIM MC standardizes modeling/product parameters and is being published through bSDD.

ETIM's own material states that:
- modeling classes are linked to IFC 4.3;
- ETIM product classes can connect supply-chain data to BIM;
- ETIM xChange provides JSON product-data exchange;
- bSDD publishes the semantics.

## Why this matters

We were at risk of inventing a giant custom product-property schema for:
- equipment;
- doors;
- fixtures;
- MEP components;
- manufacturer products.

Instead use:
- IFC for model object;
- bSDD/ETIM for semantics;
- BIMobject/BIMLIB/manufacturer APIs for actual products;
- our custom record only for project-specific selection/verification.

### Decision

**ADAPT STANDARD PRODUCT SEMANTICS.**

Custom:
- project suitability;
- normative/project bindings;
- substitution logic;
- approval/version state.

Not custom:
- global product parameter ontology.

---

# 6. dRofus remains the strongest room/program requirement system

A further pass confirms dRofus explicitly supports requirements at:
- function/program level;
- room data sheet level;
- room templates;
- groups;
- unique room data.

It now describes itself as a continuous structured foundation from planning through operations with:
- room/asset requirements;
- BIM validation;
- change tracking/version history;
- standards/compliance criteria.

This means our custom Room Program DB should remain paused until dRofus evaluation is complete.

---

# 7. Revised free/low-cost AC29 infrastructure

A surprisingly capable low-cost stack can now be assembled:

```
ARCHICAD 29
  |
  +-- HuskyBIM / Archi Automate / minimal custom bridge
  |
  +-- Speckle connector
  |      -> model versions
  |      -> Automate QA / analytics
  |
  +-- IFC/BCF
         -> OpenProject BIM Community
         -> issues/tasks/project coordination

INFORMATION
  -> BIMQ
  -> dRofus
  -> Russian normative federation

ANALYSIS
  -> Archicad native Collision/MEP/SAF
  -> Solibri / IfcOpenShell
  -> Ladybug/Honeybee
  -> depthmapX
  -> structural FEA
  -> LCA platform

PRODUCTS
  -> bSDD / ETIM
  -> BIMobject / BIMLIB
```

This is approaching the user's desired condition:
**assemble mature components and write minimal glue/semantics.**

---

# 8. What this pass removes from our roadmap

Mark as `REUSE_FIRST / CUSTOM_BLOCKED`:

- BIM issue/task server;
- BCF server;
- generic IFC viewer;
- generic model CI/CD runner;
- generic version-trigger automation framework;
- isovist/visibility graph engine;
- generic space-syntax calculations;
- LCA database/calculation engine;
- global manufacturer/product parameter ontology.

---

# 9. What remains plausibly unique

After fifteen checkpoints, the core is becoming clearer:

```
Russian legal/normative applicability
             +
canonical IDs across all systems
             +
architecture-specific causal dependencies
             +
design-intent invariants
             +
invalidation/escalation logic
             +
candidate ranking/healing
             +
cross-tool transaction policy
```

Even these should continue to undergo product/code/research audits before we claim uniqueness.

---

# 10. Next high-value searches

Do not code yet.

Next reuse passes should focus on:
1. architectural design rationale / decision-management systems;
2. automated detail selection / construction-system libraries;
3. cost/5D/QTO and procurement APIs;
4. automated permits / planning/zoning systems;
5. façade/daylight/window optimization systems;
6. structural/MEP/fire-engineering AI assistants;
7. BIM object substitution / manufacturer-equivalence engines;
8. schedule/documentation automation under Archicad specifically.

Each of these may remove another custom subsystem.
