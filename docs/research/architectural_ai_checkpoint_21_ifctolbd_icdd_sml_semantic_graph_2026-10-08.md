# Architectural AI checkpoint 21 — canonical identity/provenance can also reuse open standards and IFCtoLBD MCP

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Executive conclusion

The next supposedly custom subsystem also shrank sharply.

We do **not** need to invent from scratch:
- an external semantic representation of IFC;
- a generic IFC-to-knowledge-graph converter;
- a generic IFC semantic MCP;
- generic model evidence/provenance queries;
- generic SHACL-on-IFC graph validation;
- generic IFC revision-diff graph;
- a custom linked-document container;
- a completely new cross-document/object linking standard.

The strongest existing stack found in this pass is:

- persistent IFC GUIDs / IFC external references;
- EN 17632 Semantic Modelling and Linking (SML);
- ISO 21597 Information Container for Linked Document Delivery (ICDD);
- BOT / OPM / bSDD / PROV-O;
- **IFCtoLBD v2.54.1 with its current MCP server**;
- IIB.ICDD / RUB ICDD platform.

This suggests that our "Canonical Project Graph" should be a **thin project-specific link layer over persistent source identifiers and semantic standards**, not a second universal BIM database.

---

# 1. IFCtoLBD has evolved into an almost ready semantic BIM service

The current open-source `jyrkioraskari/IFCtoLBD` repository is version 2.54.1 (2026) and Apache-2.0.

It converts:
- IFC STEP;
- IFC/XML;
- IFC/JSON;

into Linked Building Data/RDF.

Outputs include:
- Turtle;
- JSON-LD;
- other RDF serializations;
- ICDD packages.

It can be automated via:
- desktop;
- CLI;
- Java library;
- Python examples;
- **MCP server**.

This is much more than an academic converter.

---

# 2. IFCtoLBD MCP already implements many services we planned for the SBIM semantic layer

The current MCP documentation exposes tools for:

- capability discovery;
- load/reuse IFC models;
- model summary;
- RDF entity inspection;
- class counts;
- property/predicate inspection;
- guarded SPARQL queries;
- attributable property evidence;
- SHACL validation;
- structured validation explanation;
- revision comparison;
- geometry extraction;
- RDF export;
- resource cleanup.

It supports local stdio MCP on Windows.

## Security/runtime details are already mature

The MCP implements:
- read/write path roots;
- guarded read-only SPARQL;
- row/query time limits;
- stable error codes;
- loaded-model session reuse;
- model caps;
- no guessed property conversions;
- explicit states like:
  - found;
  - not_found;
  - ambiguous;
  - incomplete.

This is exactly the kind of safety discipline we were preparing to write ourselves.

### Decision

**P0 local prototype after AC29 template stabilization.**

Do not build a generic semantic IFC MCP server.

---

# 3. IFCtoLBD conversion profiles already map closely to our intended layers

Current profiles include:

- `core`
- `properties-simple`
- `properties-opm`
- `evidence`
- `geometry-envelope`
- `geometry-full`
- `bim-gis`
- `compliance`
- `revision-ready`
- `geometry-external`
- `supply-chain`
- `sustainability`

This is almost a ready multi-layer Project Kernel view.

## Mapping to SBIM

```
SBIM need                       IFCtoLBD profile
-------------------------------------------------------
topology                        core
properties                      properties-simple
temporal/property semantics     properties-opm
normative evidence              evidence
fast spatial approximation      geometry-envelope
deep geometry analysis          geometry-full
site/geospatial                 bim-gis
norm checks                     compliance
version/change audit            revision-ready
large geometry offloading       geometry-external
product data                    supply-chain
LCA/EPD                         sustainability
```

We should not duplicate these view concepts unless Archicad-live latency requires a separate compact hot state.

---

# 4. Evidence/provenance is already first-class

The `evidence` profile and `get_property_evidence` can return traceable information for a model element/property including:

- IFC GUID or RDF identifier;
- original value;
- original unit;
- normalized value;
- IFC datatype;
- RDF datatype;
- source entity;
- source path;
- warnings;
- conversion version.

This is directly relevant to the user's requirement that the system must not invent numbers.

A design decision can cite the exact model evidence used.

### Consequence

Our Project Graph should **reference evidence URIs**, not copy arbitrary AI-parsed values without provenance.

---

# 5. SHACL checking is already bundled

IFCtoLBD MCP currently provides versioned SHACL packs including:

- core BOT;
- properties/units;
- geometry/CRS;
- sensors;
- fire/accessibility;
- supply-chain identifiers;
- sustainability declarations.

The service:
- returns standard SHACL reports;
- retains report resources;
- exposes structured findings by severity/focus node;
- does not mutate the source model during validation.

This lines up directly with checkpoint 20's SHACL decision.

### Decision

For semantic graph checks:
**reuse IFCtoLBD + SHACL engine before writing our own RDF validation runtime.**

Russian-specific SHACL shapes become our custom input, not our custom engine.

---

# 6. IFC revision comparison is already supported

The current MCP has a `revision-ready` profile and a `compare_revisions` tool.

Stable comparison uses:
- same project/model scope;
- stable identifiers;
- previous and current loaded revisions.

It produces:
- added/removed statement counts;
- change resources as RDF.

This may replace part of the planned generic semantic diff/change-store.

## Important limitation

This is **IFC revision comparison**, not a live Archicad event stream.

Our AC29 hot path may still need:
- Archicad observer/event bridge;
- current PLN revision;
- sub-second dirty marking.

But once an IFC snapshot is produced, the semantic revision layer is commodity.

### Decision

Split architecture:

```
LIVE HOT STATE
  Archicad observer / current PLN
  minimal custom

SNAPSHOT / DEEP STATE
  IFCtoLBD revision-ready
  reuse
```

---

# 7. IFC GUID already supplies the primary stable BIM-object identity

buildingSMART specifies that the IFC GUID for rooted semantic objects is intended to be persistent and must not change during an object's lifetime.

Temporary STEP line numbers such as `#123` are not stable and must never be treated as identity.

### Canonical identity implication

Do **not** invent a replacement ID for every BIM element if we already have:
- Archicad GUID;
- IFC GlobalId;
- stable external-system IDs;
- semantic URIs.

Instead use a link record:

```yaml
ProjectEntity:
  project_uri: https://.../entity/...
  archicad_guid: ...
  ifc_global_id: ...
  lbd_uri: ...
  provider_refs:
    drofus: ...
    bimq: ...
    tangl: ...
    normative: ...
```

The project URI identifies the concept in our project graph, while source IDs remain authoritative in their own systems.

---

# 8. IFC External References already provide standard links to outside information

IFC supports external references to:
- classifications;
- documents;
- libraries;

using:
- URI/location;
- external item identification;
- human-readable name.

bSDD itself documents standard mappings from bSDD URIs into IFC and IDS.

### Consequence

Whenever a product/classification/normative/document reference can travel in normal IFC/bSDD/IDS structures, use those structures.

Do not hide all semantics in private SBIM property blobs.

---

# 9. EN 17632 Semantic Modelling and Linking is directly relevant to our project graph

EN 17632 SML exists specifically for semantic modelling/linking across built-environment information.

The public CROW-hosted resources expose:
- normative SKOS terminology;
- RDFS/OWL classes and properties;
- SHACL;
- SPARQL endpoint;
- downloadable Linked Data.

DigiChecks itself builds on SML.

### Decision

Before defining a new generic relation such as:
- hasPart;
- contains;
- connectedTo;
- hasState;
- isInformationAbout;
- hasProperty;

check EN 17632/SML first.

Custom SBIM relations should be reserved for genuinely project-specific semantics such as:
- CHANGE_CAUSES;
- INVALIDATES;
- PRESERVES_INTENT;
- CONFLICTS_WITH_INTENT;
- REQUIRES_RECHECK;
- FIX_CANDIDATE_FOR.

---

# 10. ISO 21597 ICDD already standardizes cross-document and cross-model link containers

ICDD was designed to bundle arbitrary heterogeneous documents while preserving links between:
- files;
- models;
- individual elements/parts inside those files.

Payloads may include:
- IFC;
- PDF;
- XLSX;
- DWG;
- images;
- other files.

The linkset is represented semantically using RDF.

This is extremely relevant to our project because we want to connect:

```
Archicad/IFC element
 ↔ normative clause
 ↔ detail drawing
 ↔ product
 ↔ calculation
 ↔ decision
 ↔ issue
 ↔ report
```

ICDD means we do not need to invent a portable "SBIM project evidence bundle" format.

### Potential role

At project milestones:

```
Compiled Project Kernel
 + IFC
 + normative evidence
 + detail documents
 + reports
 + DDRs
 + semantic linksets
     ↓
ICDD package
```

This produces an auditable portable exchange/archive.

---

# 11. IIB.ICDD is already an MIT implementation

The public `philhag/IIB.ICDD` project provides a .NET library for ISO 21597 containers.

It supports:
- open;
- create;
- validate;
- edit;
- export;
- SPARQL;
- SHACL.

License: MIT.

The related RUB ICDD platform is also MIT and provides a web application for:
- upload;
- validation;
- editing;
- export;
- IFC viewing;
- JSON-LD;
- REST access.

The public platform is a development/research environment, not production infrastructure, but the code is reusable.

### Decision

If we need portable semantic project bundles:
**reuse ICDD libraries/platform patterns.**

---

# 12. Cross-domain SHACL checking in ICDD has already been benchmarked

Published research demonstrates:
- cross-domain linked building data in ICDD;
- SHACL inference;
- semantic link validation;
- performance benchmarking;
- optimized inferred link graphs.

This means even cross-domain linked-data validation is not greenfield.

### Consequence

Our performance work should benchmark existing SHACL/ICDD techniques rather than assume a graph solution will be too slow.

Use:
- compact hot graph for interactive AC29;
- semantic RDF graph for deep/release analysis.

---

# 13. Revised two-speed Project Graph architecture

The project no longer needs one monolithic graph trying to satisfy every latency and semantic requirement.

## HOT PROJECT GRAPH

Purpose:
- milliseconds;
- live Archicad actions;
- dirty cone;
- element dependencies;
- validity envelopes.

Implementation:
- compact IDs/bitsets/adjacency;
- only needed high-priority dependencies;
- no heavy RDF reasoning in the wall-move hot path.

## SEMANTIC PROJECT GRAPH

Purpose:
- deep reasoning;
- rule/evidence traceability;
- cross-tool links;
- normative relations;
- change audit;
- milestone/release analysis.

Implementation:
- IFCtoLBD;
- RDF;
- BOT/OPM/SML;
- bSDD;
- DIO/PROV;
- AEC3PO;
- SHACL/SPARQL;
- ICDD milestone containers.

This matches the user's original intuition:
heavy analysis upfront / periodically, fast lightweight operation during design.

---

# 14. Revised canonical identity principle

Old risk:
"Create a universal SBIM GUID and duplicate every object."

New principle:
**federated persistent identity + semantic links.**

Identity sources:
- Archicad GUID;
- IFC GlobalId;
- normative canonical URI/requirement ID;
- bSDD URI;
- product/manufacturer ID;
- dRofus/BIMQ/provider ID;
- document/detail URI.

SBIM keeps:
- a project URI;
- mappings between source identities;
- revision/effective intervals;
- confidence/provenance.

It does not replace source identities.

---

# 15. What is newly removed from custom roadmap

Block custom implementation pending reuse tests for:

- IFC → RDF converter;
- generic semantic IFC MCP;
- generic SPARQL model query service;
- generic SHACL validation service;
- generic IFC revision semantic diff;
- generic property-evidence service;
- portable linked project package format;
- cross-document linkset format;
- generic built-environment semantic relation ontology;
- replacement identity scheme for IFC elements.

---

# 16. Highest-value experiment: SEMGRAPH-01

After the AC29 template priority is complete:

1. Export the same current Archicad 29 model twice.
2. Load v1 in IFCtoLBD using:
   - evidence;
   - revision-ready;
   - compliance profiles.
3. Query:
   - one wall;
   - one window;
   - one slab;
   - one room/zone-equivalent object.
4. Validate with core SHACL.
5. Modify one wall/window in Archicad.
6. export v2.
7. compare revisions.
8. verify:
   - IFC GlobalId persistence;
   - element matching;
   - changed properties;
   - topology changes;
   - material/property evidence.
9. Attach one normative requirement URI and one design-decision URI.
10. package IFC + RDF + evidence into ICDD.
11. query the cross-links.

## Success criteria

If identity and revision links survive the real AC29 round trip:
- the semantic/deep Project Graph can be based on this open stack;
- custom graph storage remains only for the live hot dependency graph.

---

# 17. Important risk

Archicad IFC exporter behavior must be empirically verified.

Standards say IFC GlobalId is persistent for the lifetime of an object, but:
- exporter settings;
- copy/recreate operations;
- deleted/recreated elements;
- complex generated subelements;

may affect identity in practice.

Therefore the standard does not replace the live AC29 GUID readback tests.

We need a real GUID mapping benchmark.

---

# Strategic conclusion

Checkpoint 21 removes another major class of infrastructure.

The likely project architecture now has two graph layers:

**a tiny, optimized, custom live causal graph** for authoring speed,

plus

**a standards-based semantic graph** built from IFCtoLBD/SML/OPM/bSDD/AEC3PO/DIO/PROV/SHACL for deep reasoning and audit.

This is substantially simpler and safer than building one giant proprietary mega-graph.
