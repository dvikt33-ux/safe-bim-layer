# Architectural AI checkpoint 16 — Russian BIM platform discovery, design-decision memory and 5D

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29

## Executive conclusion

This pass found another high-priority "we were about to rebuild parts of this" platform:

# **Tangl**

Tangl is a Russian BIM data/validation/5D ecosystem with:
- IFC and proprietary-model processing;
- model storage;
- geometry + metadata buckets;
- browser/desktop viewing;
- automated model validation;
- collisions/minimum-distance checks;
- attribute/value checks;
- project/product/normative checks;
- EIR-style requirements;
- quantity and cost analysis;
- 4D/5D functions;
- open APIs and Swagger;
- developer SDK;
- Russian cloud/on-prem deployment.

For the Russian project context, Tangl is potentially as important as HuskyBIM was for Archicad execution.

This must be deeply audited before we build:
- a Russian BIM model cloud/backend;
- generic model checking;
- generic requirement-check trees;
- quantity/cost extraction;
- 5D logic;
- an IFC model viewer;
- some project-data APIs.

---

# 1. Tangl SDK is an actual developer platform, not only a closed application

Official Tangl developer documentation currently exposes Swagger for:

- Auth Server
- Platform Server
- Cache Server
- Tangl Value Server
- Tangl Control Server

Tangl provides:
- REST APIs;
- Viewer API;
- model storage/data API;
- element metadata buckets;
- element geometry buckets;
- identifier system;
- model import;
- Value analysis export through OData;
- demo application;
- demo account/client credentials workflow;
- public developer examples on GitHub.

SDK positioning explicitly includes:
- a calculation core;
- a 3D viewer;
- cloud storage or on-prem deployment;
- open API;
- custom web/desktop application development.

This is far closer to our planned "project engine/backend" than previously recognized.

## Decision

**P0 TECHNICAL AUDIT.**

Do not implement a generic BIM data backend until Tangl SDK is benchmarked against Qonic/Speckle/IfcOpenShell.

---

# 2. Tangl Control overlaps heavily with our validation/checking layer

Tangl Control currently describes automated checks for:

## Geometry
- collisions;
- minimum distances.

## Information
- parameter existence;
- parameter filling/value rules.

## Product/normative/project rules
- apartment-program checks;
- normalized element counts per area/volume;
- equipment characteristics depending on building location/context;
- configurable additional checks.

Tangl says the Control approach can check up to ~90% of EIR-type information requirements.

Its internal workflow is already structured around:
- iterative element selection;
- classification/selection directories;
- checkpoints;
- check schemes;
- collision matrices;
- project/folder/model-specific rule assignment.

This is remarkably close to our planned:
`selection predicate -> applicable rules -> check -> result -> issue`.

## Important caveat

Public material does not prove it can express the full semantic/legal logic we want:
- dated normative references;
- exceptions/specializations;
- cross-document legal applicability;
- architectural intent;
- graph-based change propagation.

Therefore Tangl Control is not our complete normative brain.

But it may be an excellent **execution engine for compiled checks**.

Potential architecture:

```
Russian Normative Graph
        ↓
SBIM Rule Compiler
        ↓
Tangl Control check schemes
        ↓
IFC model
        ↓
violations / report
```

### Decision

**TEST AS A RULE EXECUTOR, NOT AS LEGAL AUTHORITY.**

---

# 3. Tangl Space gives us a free Russian IFC/RVT viewer + collision environment

Tangl Space is explicitly free.

Current public material says it supports:
- BIM model storage;
- viewing;
- sharing;
- RVT / IFC uploads;
- collision checking;
- unlimited model/collision checks in the stated free service;
- browser/mobile access.

For our immediate solo/student project this is a very useful zero-cost candidate.

## Decision

Before installing/custom-building another local model viewer:
**TEST TANGL SPACE.**

---

# 4. Tangl Value overlaps with 5D / cost / quantities

Tangl Value covers:
- quantity calculation;
- project cost estimation;
- bill-of-work/resource extraction;
- comparison between design alternatives;
- Excel export;
- integration with estimating software;
- ERP integration;
- 4D/5D planning;
- project schedule linkage;
- plan-vs-fact analysis.

Its API supports analysis-result extraction, including OData workflows.

This means our project should not build a generic 5D engine.

## Russian alternative: 5D Смета

Another Russian product, `5D Смета`, already:
- reads IFC;
- automates quantities/cost per BIM element;
- exports to ARPS-compatible estimating workflows;
- links cost information to planning;
- offers a 30-day full trial.

### Decision

For Russian cost estimation:
**compare Tangl Value vs 5D Смета before custom implementation.**

Our custom scope:
- deciding when cost re-evaluation is triggered;
- binding cost impact into candidate ranking;
- comparing alternatives;
- project-specific cost constraints.

Not:
- raw quantity takeoff or generic estimate engine.

---

# 5. Tangl is directly targeting 2026 Russian digital approvals/expertise workflows

Current Tangl materials explicitly discuss:
- mandatory IFC/XML delivery for Moscow AGR/RNS 2026 workflows;
- checking BIM model readiness;
- matching indicators between XML and IFC;
- automated model checking;
- preparation for expertise.

A 2026 case study describes using Tangl to:
- standardize IFC/Revit/Excel data;
- calculate quantities/resources/technical-economic indicators;
- prepare and validate models for AGR.

This is strategically important because our Russian normative/approval layer does not have to be isolated from existing Russian BIM infrastructure.

## Decision

Audit whether Tangl already encodes:
- current Moscow IFC requirements;
- XML/TEP mappings;
- KSI classifications;
- model delivery requirements;
- expert-check templates.

If yes, reuse these as **project-delivery rule packs** while our normative graph handles legal/source causality.

---

# 6. Design decision memory is becoming an established pattern

A new 2026 literature/product cluster strongly validates another core SBIM concept:

A model's geometry/history alone is insufficient; project systems need to record:
- problem/question;
- assumptions;
- alternatives considered;
- evidence;
- chosen decision;
- rationale;
- approval;
- model action;
- affected outputs;
- superseded decisions.

Recent research on rejected/non-selected architectural decisions proposes explicit decision-memory artefacts because BIM typically preserves accepted state but loses rejected options/rationale.

Earlier TUM work similarly models:
- design episodes;
- explanation tags;
- constraints;
- design decision rationale linked to BIM.

Snaptrude's current "BIM Design Decision Log" guidance uses almost the same model.

## Consequence for SBIM

We should formalize a **Design Decision Record (DDR)** instead of storing vague AI chat memory.

Proposed minimal entity:

```yaml
decision_id:
status: proposed|accepted|rejected|superseded
problem:
scope:
assumptions:
hard_constraints:
soft_constraints:
alternatives:
selected_option:
rationale:
evidence:
affected_entities:
affected_outputs:
approver:
project_revision_before:
project_revision_after:
supersedes:
confidence:
```

This is not a new invention; it adapts established decision-rationale/ADR ideas to architectural BIM.

### Decision

**BUILD THIN DOMAIN ADAPTATION, NOT A NEW DECISION-MEMORY THEORY.**

Use:
- BCF for issue/viewpoint references;
- model GUIDs for affected elements;
- normative IDs for evidence;
- immutable/superseding decision records.

---

# 7. Spatial quality already has quantitative engines

depthmapX / Space Syntax provides:
- visibility graphs;
- isovists;
- spatial-network analysis;
- agent-based movement analysis;
- building and urban scales.

This should supply metrics for:
- visibility;
- spatial depth;
- circulation hierarchy;
- entrance/frontage analysis;
- awkward disconnected zones.

This is especially relevant to the user's complaint that AI plans lacked architectural logic.

It does not replace architectural judgement, but it gives the ranking engine objective spatial features.

---

# 8. LCA / carbon already has an Archicad 29 connector

One Click LCA has a current Archicad 29 plugin.

It exports bill-of-material information from the active Archicad model to the LCA platform.

Therefore:
- lifecycle-carbon database;
- EPD matching;
- generic carbon calculation;

must not become custom SBIM subsystems.

Use LCA results as candidate-ranking inputs.

---

# 9. Open product semantics: ETIM MC + bSDD

ETIM MC now connects modeling classes to:
- IFC 4.3;
- ETIM product classes;
- bSDD;
- ETIM xChange JSON.

This creates a standards-based bridge:
`generic BIM component -> standardized technical attributes -> manufacturer product data`.

This is directly useful for our equipment/product substitution concept.

## Revised substitution architecture

```
Project requirement
    ↓
canonical component class
    ↓
bSDD / ETIM MC required technical attributes
    ↓
BIMobject / BIMLIB / manufacturer catalog
    ↓
candidate products
    ↓
normative + geometry + performance filters
    ↓
ranked substitution
```

Again: do not build a global manufacturer ontology.

---

# 10. OpenProject BIM + Speckle significantly reduce control-plane/backend work

## OpenProject BIM Community

Free/open/self-hosted:
- REST API;
- IFC viewer;
- multiple models;
- BCF issue management/API;
- project tasks/schedules/boards.

Use as free coordination/task/issue backend if useful.

## Speckle

Archicad 29 connector is current.
Automate is effectively CI/CD for AEC models:
- model-version trigger;
- QA;
- compliance;
- data analysis;
- clash/report/deliverable functions.

This can replace generic publication-level automation and event-driven model checks.

Live sub-second Archicad authoring events are still a separate requirement.

---

# 11. Updated Russian-first AC29 stack hypothesis

```
                         CHATGPT
                            |
                    semantic/orchestration
                            |
         +------------------+------------------+
         |                                     |
         v                                     v
     ARCHICAD 29                          REQUIREMENTS
 HuskyBIM / Archi Automate                BIMQ / dRofus
 minimal native gaps                      Russian norms
         |                                     |
         +------------------+------------------+
                            |
                    SBIM THIN CORE
      IDs / applicability / causal edges / intent
       decision records / invalidation / ranking
                            |
       +---------+----------+---------+---------+
       |         |          |         |         |
       v         v          v         v         v
     Tangl     Speckle    Qonic    Solibri   Analysis
 Control/5D   Automate   shadow    IFC/IDS   engines
       |
 Russian delivery/expertise workflows

Free project coordination option:
OpenProject BIM Community
```

The key point:
**Tangl deserves a place in the P0 comparison, not an afterthought.**

---

# 12. Immediate new tests

## TANGL-01 — free Space
Upload one real IFC from Archicad 29 and test:
- GUID preservation;
- property fidelity;
- composites/material metadata;
- stories;
- classifications;
- collision performance;
- report/issue export.

## TANGL-CONTROL-01
Using the same IFC:
- parameter existence check;
- parameter value rule;
- minimum distance;
- collision;
- one project/normative condition;
- report back to model workflow.

Compare with:
- Archicad native check;
- Solibri;
- IfcOpenShell.

## TANGL-SDK-01
Use demo developer environment:
- authentication;
- model metadata query;
- element ID scheme;
- geometry bucket;
- property bucket;
- analysis result API.

Assess whether Tangl SDK can replace any proposed SBIM backend service.

## COST-01
Same model through:
- Tangl Value;
- 5D Смета trial;
- Archicad quantities.

Compare:
- quantity fidelity;
- rule mapping effort;
- incremental re-analysis;
- export/API access.

---

# 13. Roadmap removals after this pass

Custom code now blocked pending tests for:

- Russian IFC backend/viewer;
- generic Russian BIM checker;
- collision service;
- EIR check engine;
- generic quantity extraction;
- generic 5D estimate engine;
- AGR model precheck workflow;
- global equipment/product property ontology;
- spatial visibility analysis.

---

# 14. Remaining core is becoming small but important

Likely custom SBIM kernel:

1. Russian legal/normative applicability graph.
2. Canonical cross-system IDs.
3. Architecture-specific causal graph.
4. Design Intent invariants.
5. Immutable Design Decision Records and supersession.
6. Validity Envelopes / invalidation.
7. Cross-tool transaction scheduling.
8. Candidate generation/selection policy.
9. Minimal Archicad 29 deep/event gaps after tool benchmark.

Everything else continues under reuse audit.
