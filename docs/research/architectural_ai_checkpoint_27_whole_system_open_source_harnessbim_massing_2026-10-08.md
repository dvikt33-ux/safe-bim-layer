# Architectural AI checkpoint 27 — open-source whole-system audit: HarnessBIM, Massing, jurisdiction-specific agent teams

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Executive conclusion

The answer to the user's earlier question "has someone already built the whole project?" is now:

**Several teams are already building very large fractions of it, including open-source systems.**

The two most important findings are:

1. **HarnessBIM** — Apache-2.0, IFC-canonical, agentic Text-to-BIM, multi-discipline, verifier-first, MCP, project store, plugin/checker architecture.
2. **Massing** — MIT, IFC-native authoring + viewer + drawings + issues + clash + 4D/5D + code prechecks + generative zoning/building/service-core + field/GC/deal workflows.

Neither is a drop-in replacement for our AC29 system.

But together they eliminate any justification for inventing a generic:
- BIM agent harness;
- IFC authoring backend;
- generic verifier suite;
- generic project store;
- generic openBIM gateway;
- generic issue/BCF layer;
- generic model version/diff framework;
- generic cost/QTO/4D/5D scaffolding;
- generic browser BIM viewer;
- generic Text-to-BIM agent architecture.

The project should treat these repositories as **code/method mines and benchmark systems**, then keep only the AC29/Russia/architecture-specific gap.

---

# 1. HarnessBIM — closest open-source agentic architecture to our original SBIM concept

Repository:
`ReverseZoom2151/harnessbim`

Observed state:
- license: Apache-2.0;
- project version: 0.0.1;
- created: 2026-07-10;
- repo explicitly labels itself early-stage research;
- deterministic path is claimed built/tested;
- frontier-quality LLM generation is explicitly NOT claimed as proven.

This honesty distinction matters.

## Architecture

HarnessBIM already implements the same broad layered structure we independently derived:

```
interfaces
  CLI / Python / MCP / HTTP
        ↓
agent harness
  LangGraph / checkpoints / HITL
        ↓
discipline agents
  brief / architecture / structure / MEP / coordinator
        ↓
knowledge + memory + tools + verification
        ↓
LLM provider router
        ↓
BimBackend abstraction
        ↓
IFC4 canonical model
```

Core invariant:
agents use a generic BIM backend/IR rather than hard-coding one authoring vendor.

This is directly relevant to our provider registry.

---

# 2. HarnessBIM verifier already contains much of our generic QA architecture

Current repository contains real source modules for:

- schema validation;
- IDS;
- clash;
- code;
- structural;
- MEP;
- egress;
- proofs;
- relation checking;
- BCF export.

The checker suite has a common `run(target) -> CheckReport` pattern.

This is extremely close to our desired generic checker adapter.

## Egress example

The current egress module:
- builds a walkable graph;
- distinguishes circulation spaces;
- links rooms to corridors and exits;
- uses shortest path;
- tracks travel distance;
- estimates occupant load and exit capacity;
- explicitly marks assumptions and "not assessable" states.

This is valuable code/method reference for LIGHT/WARM screening.

It is not a Russian regulatory authority and uses illustrative/default IBC-family assumptions.

### Decision

**Do not build a generic OSS verifier suite from zero.**

Evaluate whether HarnessBIM checkers can be:
- called as sidecar services;
- adapted behind our ACCORD-like checker protocol;
- reused for tests/benchmarks;
- selectively copied under Apache-2.0.

---

# 3. HarnessBIM's Archicad backend is NOT a live Archicad backend

This is a critical correction.

The repository does contain:
`src/harnessbim/backends/archicad_backend.py`.

But its own source explicitly says:
- no Archicad installation is required;
- authoring is delegated to IfcOpenShell;
- Archicad integration is an **IFC4 round-trip**;
- its conformance tier is `RELAXED`;
- complex profiles/composites/material properties can be lossy;
- promotion to strict conformance requires real Archicad fixtures.

Therefore HarnessBIM does **not** replace:
- our native AC29 reader/observer;
- Tapir/HuskyBIM/Archicad-MCP live writer;
- Archicad transaction/readback.

### Best role

```
LIVE AC29
  our native sensor + existing write providers
        ↓ IFC snapshot
HARNESSBIM
  open verifier / project store / test harness / external generation
```

This separation is important.

---

# 4. HarnessBIM already implements generic state/version/plugin architecture

Current source tree contains:

- persistent project store;
- versioning/diff;
- plugin registry;
- MCP server;
- backend abstraction;
- live session abstraction;
- reconciliation;
- capability routing;
- checker plugins;
- BCF;
- RAG/memory;
- design-spec related infrastructure;
- training/evaluation paths.

The repo also has a substantial test suite around:
- backend conformance;
- authoring;
- dimensions;
- carbon/energy;
- query;
- copilot;
- verification;
- tool/MCP behaviour.

### Decision

Before implementing a generic:
- project store;
- checker registry;
- BIM backend abstraction;
- tool registry;
- agent harness;

first perform a code-level reuse audit against HarnessBIM.

---

# 5. Massing is the largest open-source "almost everything" platform found so far

Repository:
`ibuilder/massing`

Observed state:
- license: MIT;
- created: 2026-06-14;
- pushed: 2026-10-02;
- ~122 GitHub stars / 51 forks observed;
- large active codebase;
- third-party copyleft components are kept behind documented boundaries.

The platform covers a huge surface:

- IFC model viewer/federation;
- authoring round-trip;
- walls/slabs/columns/beams/roofs/windows/doors;
- versioning + undo/redo;
- BCF/issues;
- clash;
- IDS;
- QTO;
- 4D;
- 5D/cost;
- drawings/sheets;
- room/window/door schedules;
- code prechecks;
- MEP connectivity;
- structural analytical model;
- embodied carbon;
- CDE/openCDE-like workflows;
- documents;
- field/mobile;
- cost/procurement/GC;
- as-built/turnover;
- generative zoning -> IFC;
- unit layouts;
- parking;
- façade;
- service core;
- MCP/AI surfaces.

This is much closer to a **full open AEC platform** than a small BIM utility.

---

# 6. Massing is valuable but must not be mistaken for architect-grade logic

A direct source audit is important.

Its current service-core generator is real code, but intentionally coarse.

Observed implementation uses heuristics such as:
- core width/depth derived as fractions/caps of floor plate;
- one elevator inserted as a box;
- one stair inside the core;
- a second egress stair at a remote corner;
- fixed/simple MEP risers;
- coarse ceiling mains/diffusers;
- IBC-oriented assumptions.

This is useful as:
- deterministic starter geometry;
- test fixture;
- code pattern;
- interface/provenance example.

It is **not** evidence that the hard architectural problem of service-core planning is solved at expert level.

### Important lesson

Feature count is not architectural intelligence.

For every large AI/AEC repository we must distinguish:

```
FEATURE EXISTS
vs
FEATURE IS ARCHITECT-GRADE
vs
FEATURE IS NORMATIVELY TRUSTWORTHY
```

This becomes a formal audit rule.

---

# 7. What Massing can realistically save us

Because the root code is MIT, after file-level/third-party review it is a serious source of reusable implementation patterns for:

- IFC authoring recipes;
- GUID-stable edits;
- versioned model operations;
- project browser;
- drawings/sheets;
- schedules;
- QTO;
- cost mappings;
- version diff;
- BCF;
- openCDE surfaces;
- viewer;
- selection/query;
- authoring guards;
- 4D/5D data bindings;
- model-health reporting;
- deterministic AI command planning patterns.

## What it should NOT replace

- AC29 native source of truth;
- Russian normative authority;
- Russian SPDS;
- our architectural CSE/Design Intent;
- architect-grade spatial/core/detail logic;
- strict native Archicad composites/profiles/favorites behaviour.

### Role

**P0 CODE-MINING / REFERENCE PLATFORM**, not "switch from Archicad to Massing."

---

# 8. Agentic BIM Team proves the jurisdiction-specific architecture pattern

Repository:
`louistrue/agentic-bim-team`
License: MIT.

Current workflow:

```
Swiss address
   ↓
Swiss zoning API
   ↓
georeferenced site IFC
   ↓
architect agent
   ↓
IFC design
   ↓
parallel specialist review:
 structural / MEP / façade-energy / fire
   ↓
BCF
   ↓
architect fix
   ↓
repeat until convergence
```

The project is simple compared with our target, but strategically important.

It proves the "national adapter" concept:

- country-specific zoning;
- country-specific codes;
- one IFC substrate;
- specialist reviewers;
- BCF feedback;
- iterative repair.

### Russian analogy

```
Russian site + PZZ/GPZU
   ↓
our authoritative source adapters
   ↓
Archicad/IFC project
   ↓
specialist engines
   ↓
BCF/evidence
   ↓
AC29 repair orchestration
```

This is now an established pattern, not a speculative architecture.

---

# 9. openbimrs is interesting infrastructure, but not a current priority

`openbimrs/openbim` is an AGPL Rust ecosystem targeting modular openBIM standards:
- STEP;
- IFC;
- IDS;
- BCF;
- ICDD;
- CDE;
- LOIN;
- MVD;
- ISO 23387 data templates;
- EPD;
- GAEB.

However its own README explicitly says many crates remain scaffolds or partial implementations.

### Decision

Do not migrate the current Python/IfcOpenShell stack to Rust.

Keep openbimrs as:
- future standards library watch;
- architecture/typing reference;
- possible performance path later.

---

# 10. Revised whole-system role map

## Keep AC29 live layer

```
Archicad 29
  + native Model Dump / observer
  + Tapir / Archicad-MCP / HuskyBIM
```

## Reuse whole-system open layers

```
HarnessBIM
  generic verifier
  generic checker registry
  generic project/version concepts
  agent/backend patterns
  benchmark harness

Massing
  IFC authoring recipe library
  viewer/project/data patterns
  drawings/QTO/4D/5D/openCDE implementation ideas
  generic openAEC platform components
```

## Keep custom thin core

```
Russian source authority/currentness
+ applicability
+ AC29 live identity/readback
+ construction-system grammar
+ architectural intent/style
+ causal/invalidation graph
+ repair priority
+ view/detail information obligations
+ provider arbitration
```

---

# 11. New rule: whole-system code-mining pass before subsystem implementation

Before writing a generic subsystem, search not only products/research but also:

1. HarnessBIM;
2. Massing;
3. IfcOpenShell/Bonsai;
4. Tapir/Archicad-MCP;
5. ACCORD;
6. relevant domain product;
7. open source reference implementations.

Classification:

- `REUSE_CODE`
- `REUSE_PROTOCOL`
- `REUSE_ALGORITHM`
- `REUSE_TEST`
- `REFERENCE_ONLY`
- `CUSTOM_GAP_PROVEN`

No major subsystem starts directly at `CUSTOM`.

---

# 12. Highest-value tests

## HARNESSBIM-01

On a local sandbox:

1. install deterministic `ifc,verify` extras;
2. generate its sample office;
3. run all checker outputs;
4. inspect BCF;
5. import generated IFC into Archicad 29;
6. compare what survives;
7. export back from AC29;
8. compare semantic loss;
9. run our Model Dump;
10. evaluate whether HarnessBIM verifier can consume our AC29 IFC export.

Success:
HarnessBIM becomes an external verifier/benchmark without becoming the live authoring authority.

## MASSING-01

Run the open stack or desktop build in isolation.

Test only:
- one blank IFC;
- one wall/window/slab edit;
- version diff;
- BCF;
- QTO;
- drawing;
- one generative service-core example.

Do not test the entire GC/finance platform.

Success:
identify reusable modules worth extracting/adapting.

## WHOLE-STACK-01

Same simple brief through:
- HarnessBIM;
- Massing generative path;
- FloorPlan6/our AC29 path.

Compare:
- geometry quality;
- semantic correctness;
- code/check coverage;
- editability in AC29;
- human correction time.

Primary metric:
**human minutes to a verified usable AC29 result.**

---

# Strategic conclusion

We now have direct evidence that the market/open-source ecosystem is converging on the same category from several directions.

The correct strategy is no longer:
"build SBIM as a new full BIM/AI platform."

It is:

**use mature/open whole-system components as reference and reusable infrastructure, while owning only the Archicad-29/Russian/architectural-semantic kernel that those systems do not solve.**
