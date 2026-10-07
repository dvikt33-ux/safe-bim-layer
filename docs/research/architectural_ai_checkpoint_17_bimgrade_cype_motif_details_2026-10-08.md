# Architectural AI checkpoint 17 — whole-system candidates, Russian compliance, free engineering suite and detail intelligence

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Executive conclusion

The reuse surface shrank again.

This pass found three especially important additions:

1. **BIM Grade** — a current IFC-native code-compliance platform that explicitly says its engine already runs on Russian design documentation. Its public architecture independently converges on several mechanisms we recently designed: compliance-as-CI, coverage gates, proof-carrying findings, cross-domain joins and bitemporal code history. This is now a P0 technical/demo audit before we build large parts of the compliance runtime.

2. **CYPE / BIMserver.center** — a huge existing Open BIM engineering ecosystem. Several relevant apps are completely free, including CYPE Architecture, IFC Builder, Open BIM Site, Open BIM Layout, CYPE Construction Systems and CYPEURBAN. Paid engineering apps have a 30-day evaluation route and academic Campus licensing. This stack can remove major chunks of custom urban-planning, construction-system, fire, lighting, HVAC, plumbing, electrical, quantity and documentation work.

3. **Motif Design** — launched publicly in September 2026 as an agent-native, open, collaborative BIM platform built by former Autodesk/Revit leadership. It is not an AC29 replacement today, but it is another strong signal that much of the long-term "AI-native BIM" vision is becoming a product category rather than unique SBIM invention.

Other important findings:
- **usBIM** already bundles/coordinates IFC viewer/federation/BCF/bSDD/IDS and offers checker/clash/compare/editor/4D modules.
- **BIMsmith Detail Shelf** now provides AI search over thousands of manufacturer construction details.
- **Augmenta ACP 2.0** is a production AI-native electrical VDC design/coordination environment with real-time clash and iterative redesign; mechanical/plumbing are publicly listed as coming next.
- **OpenConstructionERP** is a rapidly evolving open-source/self-hosted 4D/5D/BOQ/BIM takeoff platform with REST/API ambitions; useful for sandbox audit, but its self-reported capabilities require verification before dependency.

---

# 1. BIM Grade — extremely close to our Russian compliance architecture

## Current public claims verified on the live site

BIM Grade currently describes itself as an IFC-native automated building-code compliance engine.

Its current site states:
- every IFC version can be checked like a software build;
- every verdict carries evidence;
- the engine is already running on **Russian design documentation**;
- it uses domain-specialized reviewers/agents;
- a Coverage Gate prevents a "ready" result while mandatory checks remain uncovered;
- findings are typed joins over IFC entities with provenance back to source facts;
- bitemporal source closure allows a prior review to be replayed against rules as they stood at the submission date;
- architecture, structure and MEP are joined in the audit;
- it accepts IFC/PDF, a jurisdiction rule pack, reviewer agents, coverage gate and evidence pack;
- the public example reports 4,820 IFC entities and 312 rules in a demo run.

The company page identifies:
- Agonist Inc (USA);
- Agonist Development AB (Sweden);
- OOO Proektologiya (Russia);
- founder/architect Alexander Brichkin.

The current page says a Swedish BBR/PBL rule pack is the first Western target, while the engine runs on Russian documentation today.

## Why this is strategically important

Several mechanisms overlap almost directly with recent SBIM architecture:

SBIM idea | BIM Grade public concept
---|---
Active Rule Pack | Jurisdiction rule pack
coverage / audit debt | Coverage Gate
provenance | proof-carrying correlation
historical norm replay | bitemporal source closure
IFC entity bindings | cross-domain typed joins
model release audit | compliance as a build step
independent domain review | 18 domain reviewers

This means we must not blindly build a complete compliance runtime until BIM Grade has been technically audited.

## What remains unknown

No public API documentation or public pricing was found in this pass.

Need direct technical questions:
1. Russian rule coverage: which SP/GOST/FZ/PZZ and project types?
2. Source licensing/provenance?
3. Is rule representation exportable?
4. Can external/custom Russian rules be loaded?
5. API/webhook/MCP?
6. Incremental/delta checking or full IFC run only?
7. Can findings return exact IFC GUID + geometry evidence?
8. Can it run locally/on-prem?
9. Does it expose rule dependency/version graph?
10. Can it operate as a checker invoked by our Project Compiler rather than as a closed UI?
11. Pricing/student/pilot availability?
12. Can it check our current SP 464 / SP 118 fixtures?

### Decision

**P0 REQUEST-ACCESS / TECHNICAL AUDIT.**

Do not assume it replaces the normative graph, but it may replace a large amount of compliance execution/audit infrastructure.

---

# 2. CYPE ecosystem — an entire engineering/openBIM stack already exists

CYPE has a very broad Open BIM suite connected by BIMserver.center.

This is not one checker. It is a modular engineering ecosystem covering:
- architecture;
- site;
- urban regulations;
- construction systems;
- fire;
- smoke/FDS;
- HVAC;
- electrical;
- plumbing;
- lighting/daylight;
- acoustics;
- thermal/energy;
- structural analysis;
- connections;
- quantities/cost;
- drawings;
- IFC.

## Free apps relevant to us

### CYPE Architecture
Completely free.
- native architectural modeling;
- openBIM project connection;
- direct links to construction systems, quantities, urban planning, structural analysis and layouts.

### IFC Builder
Completely free.
- creates/maintains IFC buildings;
- can build from DWG/DXF/PDF/image references;
- openBIM handoff to energy, acoustic, structural and MEP tools.

### Open BIM Site
Completely free.
- site coordinates;
- maps;
- topographic surfaces;
- parcels/buildings.

### Open BIM Layout
Completely free.
- plans;
- elevations;
- sections;
- axonometrics;
- dimensions;
- layouts from BIM models.

### CYPE Construction Systems
Completely free.

This is highly relevant to the user's complaint that details/construction systems cannot be postponed to the end.

It explicitly models:
- façade systems;
- party/basement walls;
- roofs/screeds;
- exterior doors/windows/skylights;
- partitions;
- floor slabs;
- suspended ceilings;
- thermal breaks;
- interior doors/windows/skylights.

A construction system can contain:
- layer structure;
- layer thickness;
- material;
- density;
- thermal properties;
- reusable saved systems.

It links those systems to architectural BIM elements and warns about thickness mismatch between the assembly and the host BIM element.

It generates descriptive/construction reports and exposes layers in 3D.

This is close to a reusable **Construction System Registry + host compatibility checker**.

### CYPEURBAN
Completely free.

This may be one of the most useful discoveries of this pass.

CYPEURBAN lets users define or import municipal urban-planning checks and evaluate them against BIM.

Built-in check categories include:
- plot area/free/green area;
- frontage and depth/front ratio;
- inscribed diameter;
- floor count;
- building/cornice/ridge/fence/façade heights;
- height based on street width/adjacent buildings;
- setbacks;
- buildable depth;
- overhangs;
- building/dwelling/patio checks;
- parking;
- habitability;
- site/building occupancy-like metrics.

It can compare regulation values with model values and export the urban regulatory BIM/checks to IFC.

### Why CYPEURBAN matters for Russia

It does not ship Russian PZZ by default, but it offers a ready **urban-rule execution engine** into which our normalized Russian PZZ/GPZU rules may be compiled.

Potential architecture:

```
PZZ / GPZU / heritage / site normative adapter
            ↓
SBIM normalized urban rules
            ↓
CYPEURBAN custom municipality checks
            ↓
IFC project
            ↓
urban compliance report
```

Before writing our own setback/height/buildability/parking checker, test whether our rules can be expressed in CYPEURBAN.

---

# 3. CYPE engineering apps remove more custom solver work

## CYPEFIRE
Open BIM fire-design/check tool:
- compartmentation;
- evacuation;
- exterior propagation;
- extinguishers/detectors;
- fire loads;
- evacuation routes;
- fire-fighter intervention elements.

It can import building/space geometry from an Open BIM project.

## CYPEFIRE FDS
Wraps NIST Fire Dynamics Simulator for:
- fire evolution;
- smoke;
- temperature;
- smoke exhaust;
- fire scenarios.

We should never build a CFD fire engine.

## CYPELUX
Lighting/daylight tool:
- normal/emergency lighting;
- daylight factor;
- glare (UGR);
- location/orientation;
- multiple CIE sky models;
- imported glazed openings;
- customized requirement thresholds;
- LEED daylight checks.

This is another alternative/complement to Ladybug/Radiance.

## CYPEHVAC / CYPEPLUMBING / CYPELEC
Existing Open BIM MEP-design stack.

CYPEHVAC can:
- import architecture;
- use thermal-load results;
- design HVAC equipment/networks;
- export reports, drawings, BoQ;
- use manufacturer catalogues;
- share IFC/glTF.

CYPE has a much larger family for water, sewerage, electrical, cable routing and switchboards.

## Open BIM Quantities
Extracts quantities and BoQ from IFC using configurable measurement rules, with automatic updates when the linked model changes.

### Licensing

CYPE explicitly offers:
- permanent free apps;
- 30-day evaluation access for paid apps;
- Campus licensing for students/teachers if the educational institution has an agreement.

Given the user is currently a student, **CYPE Campus availability is worth checking before buying engineering software**.

### Decision

**P0/P1 SUITE EVALUATION.**
Install only the smallest useful subset after checking overlap with Archicad 29 native MEP/SAF and our other candidates.

---

# 4. usBIM — another modular openBIM platform worth comparing with Tangl/Qonic/Solibri

The ACCA usBIM ecosystem already provides a large number of components.

Included/free current base apps include:
- IFC/BIM viewer;
- point cloud viewer;
- model federation;
- BCF;
- GIS;
- chat/meet;
- document tools;
- calendar;
- bSDD editor;
- IDS editor;
- BIM object library;
- light online estimating.

Additional modules include:
- clash detection;
- IFC checker;
- IFC editor/refactor;
- model compare;
- 4D/Gantt;
- facility;
- IoT;
- CDE;
- data-quality;
- geotwin.

## usBIM.checker

Current feature set:
- IFC data validation;
- rule/checklist creation;
- property existence/value validation;
- add/modify/delete IFC properties;
- Excel property import;
- classification;
- IFC export;
- report of mismatch against required values.

It explicitly targets EIR / information requirement checking.

It offers a one-month trial.

## usBIM.IDS / bSDD

usBIM provides:
- free IDS editor;
- bSDD-oriented dictionary tooling;
- IDS validation modules.

## Decision

Before standardizing on one openBIM checker/companion, compare:
- Tangl;
- Qonic;
- usBIM;
- Solibri;
- IfcOpenShell;
- Speckle.

Do not install all permanently.

---

# 5. BIMsmith Detail Shelf — mature detail discovery already exists

BIMsmith's Detail Shelf contains thousands of manufacturer-provided construction details.

The June 2026 update added AI-powered detail search and expanded manufacturer content.

Its data model is **detail-first**, not product-first:
- one detail can connect to several products;
- one product can connect to several details.

Available content includes formats such as:
- DWG;
- PDF;
- Revit in the broader library/context.

This is relevant to our detail-selection problem.

## Correct role

Do not treat BIMsmith details as automatically valid for Russian projects.

Use as:
- precedent/detail discovery;
- manufacturer-approved assembly source;
- candidate library;
- semantic model for `Detail ↔ Products ↔ Conditions`.

Combine with:
- TechExpert TPD for Russian typical details/series;
- local verified details;
- manufacturer Russian technical albums.

### New detail architecture

```
detail need / interface condition
        ↓
detail search adapters
   TechExpert TPD
   BIMsmith Detail Shelf
   manufacturer libraries
   internal verified library
        ↓
candidate details
        ↓
Russian norm / material / geometry / fire / thermal filters
        ↓
project-selected detail
        ↓
DDR + Project Graph bindings
```

We should code the **selection/applicability layer**, not the global detail archive.

---

# 6. Augmenta — AI MEP design is becoming productized

Augmenta ACP 2.0 (June 2026) is a production AI-native electrical VDC design environment.

Current public capabilities include:
- electrical routing;
- underground routing;
- automated model population;
- real-time clash detection;
- iterative coordination/re-design.

The company explicitly says mechanical and plumbing automation are coming next.

This does not currently look like an Archicad-first fit, and it is North-America/VDC oriented, but it changes our roadmap assumption:

**AI-generated coordinated MEP is not a subsystem we should invent from first principles.**

For AC29:
- use native MEP Designer;
- evaluate CYPE engineering apps;
- use openBIM exchange;
- keep Augmenta as benchmark/future external solver.

---

# 7. OpenConstructionERP — potentially useful open-source 4D/5D substrate, but audit claims carefully

OpenConstructionERP is currently a very active AGPL/self-hosted project positioning itself as:
- BOQ;
- CAD/BIM takeoff;
- 4D scheduling;
- 5D costing;
- AI cost matching;
- requirements/quality;
- REST/API-extensible modular platform.

Current repository/docs claim support for RVT/IFC/DWG/DGN pipelines and cost/carbon workflows.

## Caution

Most capability evidence in this pass comes from the project's own repository/site.

The project is evolving extremely quickly and multiple forks/search results expose inconsistent version/capability numbers.

Therefore it is not yet a trusted dependency.

### Decision

**P1 SANDBOX AUDIT ONLY.**

Potential value:
- self-hosted free 4D/5D;
- plugin/module architecture;
- REST integration.

But for Russian cost data, Tangl Value / 5D Смета may be much more directly useful.

---

# 8. Motif Design — another near-whole AI-native BIM platform appeared in September 2026

Motif publicly launched Motif Design on 9 September 2026.

It describes itself as:
- agent-native BIM;
- genuine parametric/associative BIM;
- browser/cloud based;
- multi-user real-time collaborative;
- AI agents operate directly on the model;
- agents can model/evaluate/document;
- project/firm context persists;
- open/queryable data model;
- custom object types/properties/behaviors;
- Revit/Rhino live model links;
- IFC support;
- collaboration integrations.

The team is led by former Autodesk/Revit/AutoCAD leadership.

Current Design pricing starts around $150/month per active user and is annual; no free trial is currently offered for Motif Design.

## Current fit for us

Not current AC29 execution:
- no live Archicad connector was verified;
- Revit/Rhino/IFC are the published model connections.

But conceptually it is perhaps the clearest proof that the exact **agent-native BIM** category we thought we might invent is rapidly becoming commercial product.

### Decision

**WATCH / TECHNICAL DEMO, not AC29 dependency.**

---

# 9. BIM Grade + Motif changes our uniqueness claim again

We should now stop saying even this with confidence:

> "our unique core is compliance graph + agent-native project reasoning."

The safer classification is:

### Existing/productizing
- agent-native BIM;
- compliance CI;
- bitemporal rule history;
- evidence/provenance findings;
- cross-domain IFC joins;
- project/firm context;
- model agents;
- custom data schema;
- generated documentation;
- urban check engines;
- engineering solvers.

### Still plausibly SBIM-specific
- Russian-source federation across state/commercial/open sources;
- precise Russian legal applicability semantics;
- integration with **Archicad 29** today;
- mapping Russian requirements into multiple existing execution engines;
- unified architectural design-intent + change-impact policy;
- minimum-disruption healing across architecture/structure/MEP/details;
- our project-specific decision hierarchy and candidate ranking.

Even these must remain under reuse audit.

---

# 10. New P0 comparison set

We should now maintain separate evaluations rather than "one best app".

## A. AC29 live execution
- HuskyBIM
- Archi Automate
- our native Add-On/Tapir only for gaps

## B. Russian compliance execution
- BIM Grade
- Tangl Control
- Solibri
- IfcOpenShell
- Archicad native checks
- CYPEURBAN for urban rules

## C. OpenBIM data/state
- Tangl SDK/Space
- Qonic
- Speckle
- usBIM
- OpenProject BIM for tasks/issues

## D. Requirements/template
- BIMQ
- dRofus
- TechExpert requirements

## E. Engineering
- Archicad native MEP/SAF
- CYPE ecosystem
- Ladybug/Honeybee
- Dlubal/FEA
- CYPEFIRE/FDS

## F. Details/products
- TechExpert TPD
- BIMsmith Detail Shelf
- BIMobject
- BIMLIB
- ETIM/bSDD

## G. 4D/5D
- Tangl Value
- 5D Смета
- OpenConstructionERP
- Open BIM Quantities / CYPE

This is much healthier than making SBIM implement all seven categories.

---

# 11. Immediate practical tests after template stabilization

The user has fixed the priority that AC29 template/workstation should be completed first.

After that, the first software evaluation batch should be:

1. **HuskyBIM**
2. **Archi Automate trial**
3. **Tangl Space free**
4. **CYPE free suite**
   - CYPEURBAN
   - CYPE Construction Systems
   - Open BIM Site
   - Open BIM Layout
   - IFC Builder
5. **BIMQ trial/education**
6. **Qonic Free**
7. **BIM Grade request-access**
8. **usBIM free account/trial**

Do not permanently install every optional package until the test matrix proves it useful.

---

# 12. Roadmap removals after checkpoint 17

Custom implementation is now BLOCKED pending reuse evidence for:

- urban zoning/check engine;
- generic construction-system registry;
- construction-system layer reports;
- BIM thickness compatibility checks;
- fire CFD;
- daylight/lighting engine;
- generic openBIM property checker/editor;
- global detail archive/search engine;
- AI electrical routing engine;
- generic 4D/5D backend;
- compliance CI framework;
- agent-native BIM authoring platform.

The remaining code should keep shrinking toward adapters + semantics + project-specific causal logic.
