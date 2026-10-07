# Architectural AI checkpoint 18 — Russian compliance reuse, CYPE engineering stack, agent-native BIM

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Executive conclusion

The reuse-first audit found another major Russian overlap with SBIM:

# Проектология / zdanie.ai

This is currently the strongest Russian-specific compliance product discovered in the audit.

Its deployed "Audit" module already:
- parses Russian project documentation from PDF / DWG / IFC;
- checks against PP RF No. 87, SP, GOST and SanPiN;
- uses a multi-agent critic/orchestrator across architecture, structure, MEP, fire, accessibility and other project sections;
- returns clause-linked findings;
- uses a Coverage Gate so a "ready" state cannot silently ignore mandatory checks;
- has a versioned normative database;
- is validated on a paid real-project pilot;
- has a working REST API + webhooks according to its current integrations page.

This overlaps with a large amount of the compliance runtime we were preparing to build.

However, the company's own public offer explicitly says it does not guarantee that its normative database always contains every current edition. Therefore it **cannot replace our authoritative normative-source federation/currentness layer**.

The best current role is:

```
official/current Russian sources
        ↓
SBIM source/applicability layer
        ↓
Active Rule Pack / audit scope
        ↓
Проектология / BIM Grade / Tangl / Solibri / other executors
        ↓
evidence/findings
        ↓
SBIM project impact/healing
```

This is a much smaller custom problem.

---

# 1. Проектология / zdanie.ai — P0 Russian compliance audit

## Confirmed current product state

Public current product pages state that the platform shares a core consisting of:
- versioned regulatory database;
- 18-agent LLM orchestrator;
- PDF / DWG / IFC project-document parser;
- SPDS formatter.

The deployed "Audit" module is described as validated on real paid project documentation in Troitsk.

The audit covers project-document sections including:
- PZ;
- PZU;
- AR;
- KR;
- IOS 1-7;
- environmental;
- fire safety;
- accessibility;
- safe operation;
- estimate;
- engineering surveys;
- construction organization;
- civil defense/emergency measures.

The current zdanie.ai page says findings cite both:
- the exact regulation;
- the location/context in the project documentation.

The platform uses a Coverage Gate that blocks a "ready" result while mandatory checks remain uncovered.

## Integrations

The current integrations page distinguishes deployed vs planned integrations.

Marked **working today**:
- REST API;
- webhooks.

Marked **in preparation**:
- MCP server;
- BCF server;
- government XML;
- hot folder / email / Telegram;
- Renga plugin;
- nanoCAD plugin;
- Pilot-BIM connector;
- Autodesk Construction Cloud webhooks;
- ONLYOFFICE/R7 plugin.

This is important:
we do **not** need to wait for MCP if the REST API is usable now.

Potential short-term integration:
`SBIM -> REST -> Audit -> webhook -> findings`.

## Public pricing

Current "Audit" pricing page:
- Trial: free, 7 days / 2 documents / 200 pages;
- Simple: 3,900 RUB/month, 1 seat / 500 pages;
- Pro: 9,900 RUB/month, 3 seats / 3,000 pages;
- Team: 19,900 RUB/month, 10 seats / 10,000 pages;
- Enterprise/on-prem higher.

The zdanie.ai landing page separately advertises a beta/access offer with different trial limits (7 days, 10 documents, 600 pages).

Therefore:
**do not hard-code trial limits**; confirm current account terms when registering.

## Critical limitation from legal offer

The public offer explicitly states:
- the product is a decision-support tool, not expertise;
- absence of a finding does not prove compliance;
- presence of a finding does not itself prove a violation;
- the platform does not guarantee complete/accurate reports;
- the platform does not guarantee its normative database always contains all current editions;
- the user must verify the applicable edition.

This confirms our earlier source-federation architecture is still necessary.

## P0 API questions

Before building more compliance code, obtain/test:

1. API docs and authentication.
2. Rate/page/file limits.
3. Supported formats through API: PDF / DWG / DXF / IFC / archives.
4. Webhook payload schema.
5. Exact finding schema.
6. Does IFC output include GUID / element ID / coordinates / viewpoint?
7. Can API scope checks to changed sections/entities?
8. Can custom rules / custom normative pack be supplied?
9. Can the rule/normative database be queried separately from full-document audit?
10. Are exact normative editions/hashes exposed in API results?
11. Is there a delta/rerun API?
12. Can reports/findings be cached/exported legally?
13. On-prem/student/pilot options.
14. Exact coverage of SP 464 / SP 118 / SP 59 / SP 1.
15. BCF and MCP roadmap timing.

## Benchmark

Use our already manually verified SP 464 fixtures as golden truth.

If Проектология catches the same issues with good provenance, we can stop building a generic Russian multi-document compliance runtime.

---

# 2. BIM Grade — international sibling / architectural reference

BIM Grade publicly describes:
- IFC/PDF input;
- jurisdiction rule packs;
- automated checks as a "build step";
- domain-specialized agents;
- Coverage Gate;
- proof-carrying findings;
- typed cross-domain IFC joins;
- bitemporal rule/source history;
- replay of historical checks against the regulation state at submission date.

Its site explicitly states the engine currently runs on Russian design documentation and that the international version targets Sweden/DACH/US.

This independently validates many concepts we recently derived ourselves:
- compliance CI;
- coverage completeness;
- evidence/provenance;
- cross-domain joining;
- bitemporal normative state.

### Decision

Treat BIM Grade + Проектология as one P0 product family for technical audit.

---

# 3. CYPE — major free engineering reuse opportunity

CYPE is not merely another checker.

Its BIMserver.center ecosystem already covers:
- architecture;
- site;
- urban regulations;
- construction systems;
- fire;
- lighting/daylight;
- HVAC/plumbing/electrical;
- structural workflows;
- quantities/cost;
- layouts;
- IFC/Open BIM exchange.

Several key apps are completely free.

## CYPEURBAN — free generic urban regulation executor

CYPEURBAN allows users to create/load custom municipal regulations and check BIM models.

Current check families include:
- plot area/free/green area;
- frontage/depth/diameter;
- floor count;
- total/cornice/ridge/façade heights;
- height related to road width or adjacent buildings;
- floor/free heights;
- building size/depth;
- setbacks;
- overhangs;
- occupancy;
- buildability;
- dwelling/room minimums;
- patios;
- parking counts/areas/dimensions/heights.

This is exactly the kind of generic geometry-rule executor we would otherwise have written for PZZ/GPZU.

### Proposed Russian use

```
PZZ / GPZU / heritage / local planning sources
        ↓
SBIM normalized urban rules
        ↓
CYPEURBAN custom regulation
        ↓
IFC model
        ↓
urban compliance results
```

We should test expressiveness before writing our own setback/height/buildability/parking engine.

## CYPE Construction Systems — free assembly system registry

This free app already models:
- construction-system type/description;
- material layers;
- layer thickness/density;
- thermal properties;
- envelope and partition systems;
- floor slabs;
- ceilings;
- thermal breaks;
- doors/windows/skylights;
- reusable/exportable assemblies.

It links the assembly to architectural BIM elements and warns when the assembly's total thickness differs from the host architectural element.

It also generates construction/descriptive reports and 3D layer representations.

This directly addresses one of the user's key points:
**construction details/systems cannot be postponed until the end because they influence dimensions and architecture.**

Potential role:
- early construction-system library;
- assembly thickness/material constraints;
- host compatibility checks;
- feed thermal/acoustic/fire engines.

### Decision

**P0 FREE TEST after AC29 template stabilization.**

---

# 4. CYPE engineering modules — do not build our own engineering engines

The ecosystem also includes:
- CYPEFIRE;
- CYPEFIRE FDS using NIST FDS;
- CYPELUX for daylight/lighting/glare;
- CYPEHVAC;
- CYPEPLUMBING;
- CYPELEC;
- structural tools;
- Open BIM Quantities;
- Open BIM Site;
- Open BIM Layout;
- IFC Builder.

Licensing:
- several apps are free;
- paid apps have evaluation access;
- Campus licensing exists for participating educational institutions.

Since the user is a student, the university/Campus route should be checked before purchasing engineering software.

---

# 5. usBIM — another modular openBIM suite

ACCA's usBIM ecosystem already contains:
- IFC viewer/federation;
- BCF;
- GIS;
- bSDD tools;
- IDS tools;
- BIM object library;
- checker;
- clash;
- compare;
- IFC editor;
- refactor;
- 4D/Gantt;
- CDE/FM/IoT modules.

The checker can validate:
- IFC property existence;
- property values;
- checklists;
- classifications;

and can edit/export IFC properties.

### Decision

Do not choose a universal openBIM backend by feature list.

Benchmark:
- Tangl;
- Qonic;
- usBIM;
- Speckle;
- Solibri/IfcOpenShell;
- OpenProject BIM.

Keep only the smallest combination that gives reliable AC29 workflow.

---

# 6. Motif Design — important category evidence, not an AC29 dependency

Motif Design launched publicly in September 2026 as an agent-native collaborative BIM platform.

Current public positioning includes:
- associative/parametric BIM;
- AI agents operating directly on the model;
- browser/cloud collaboration;
- open/queryable data model;
- custom object types/properties/behaviors;
- Revit/Rhino live links;
- IFC.

No live Archicad connector was verified.

### Decision

**WATCH / reference / future demo**, not current AC29 stack.

Its existence reinforces that we should not attempt to build an entire new agent-native BIM authoring application.

---

# 7. Detail and product selection — reuse catalogues, build applicability only

The latest detail/product sweep confirms a better architecture:

Sources:
- TechExpert TPD — Russian typical projects/details/series;
- BIMsmith Detail Shelf — manufacturer construction details + AI search;
- BIMobject / BIMLIB;
- manufacturer technical catalogues;
- ETIM / bSDD semantics.

Our code should only handle:
- project applicability;
- interfaces;
- Russian code checks;
- geometry compatibility;
- fire/thermal/acoustic requirements;
- substitutions;
- version/approval state;
- decision record.

Do not build the global detail/product archive itself.

---

# 8. Revised AC29 minimal-code stack

```
                         CHATGPT
                            |
                     SBIM thin router
                            |
               +------------+------------+
               |                         |
               v                         v
          ARCHICAD 29                 REQUIREMENTS
      HuskyBIM / Archi Automate       BIMQ / dRofus
      native gap bridge               Russian source federation
               |                         |
               +------------+------------+
                            |
                     SBIM THIN CORE
     IDs / legal applicability / causal edges / intent
     DDR / validity envelopes / invalidation / ranking
                            |
     +----------+-----------+---------+----------+
     |          |           |         |          |
     v          v           v         v          v
Проектология  CYPEURBAN   Tangl     Solibri   analysis
 / BIM Grade  / systems   /Qonic    /IFC      engines
```

This is far smaller than the initial custom architecture.

---

# 9. Custom implementation newly blocked pending reuse tests

Do not build yet:
- generic Russian project-document audit engine;
- generic multi-agent norm-control runtime;
- generic compliance coverage gate;
- generic PZZ/GPZU geometry checker;
- generic construction-system/layer registry;
- host-vs-assembly thickness checker;
- generic daylight/fire/MEP/engineering solver;
- generic IFC property checker/editor;
- agent-native BIM authoring platform.

---

# 10. Updated P0 after AC29 template/workstation release

1. HuskyBIM
2. Archi Automate trial
3. Проектология / zdanie.ai API trial
4. Tangl Space + Control/SDK audit
5. CYPE free suite:
   - CYPEURBAN
   - CYPE Construction Systems
   - Open BIM Site
   - Open BIM Layout
   - IFC Builder
6. BIMQ
7. Qonic Free
8. usBIM free/trial
9. dRofus
10. Solibri/IfcOpenShell comparison

The goal is not to install all permanently.
The goal is to prove which minimum set covers the largest SBIM surface.

---

# Strategic conclusion

The project is converging on the right shape:

**SBIM should not be a BIM application and should not be a generic compliance platform.**

It should be the thin orchestration/semantic layer that connects:
- Archicad 29;
- Russian normative authority/currentness;
- existing compliance engines;
- existing urban/engineering solvers;
- existing requirement/template managers;
- existing openBIM state systems;
- existing detail/product libraries.

The custom code should remain only where it expresses project-specific causality, intent, applicability and change policy.
