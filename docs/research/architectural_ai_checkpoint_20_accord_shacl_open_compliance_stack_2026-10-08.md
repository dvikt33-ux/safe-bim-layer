# Architectural AI checkpoint 20 — open compliance architecture already exists: ACCORD, AEC3PO, BCRL, SHACL, DigiChecks

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Executive conclusion

Another part of the supposed "SBIM custom core" has now been substantially de-risked.

We should **not invent a proprietary Rule IR, compliance ontology, compliance microservice protocol or regulation-execution orchestrator from scratch** before reproducing and testing the open work from:

- ACCORD;
- AEC3PO;
- BCRL;
- RASE;
- SHACL;
- IDS;
- bSDD;
- DigiChecks;
- D-COM;
- related open semantic-compliance research.

The ACCORD architecture is remarkably close to the architecture we independently converged on:

```
human regulation
    ↓
rule formalisation / NLP
    ↓
machine-readable rule language
    ↓
semantic rule repository
    ↓
term-to-data / term-to-process mapping
    ↓
capability registry
    ↓
orchestrator
    ↓
specialist checking microservices
    ↓
asynchronous results / evidence / BCF
```

This is nearly the same as our recent:

```
Russian normative sources
    ↓
CanonicalRequirement
    ↓
Rule IR
    ↓
Active Project Rule Pack
    ↓
router
    ↓
CYPE / Solibri / Tangl / engineering solvers / spatial services
    ↓
findings
```

The key project-specific work now shifts further toward:
- Russian legal applicability/currentness;
- normalization from Russian official sources into an open rule representation;
- project-specific causal/change semantics;
- design intent and ranking;
- Archicad 29 bindings.

---

# 1. ACCORD already built the generic compliance orchestration architecture

ACCORD (Horizon Europe, 2022–2025) produced an open semantic framework for automated building permitting/compliance.

Its current documentation includes:

- AEC3PO compliance/permitting ontology;
- Building Compliance Rule Language (BCRL);
- Rule Formalisation Process;
- Rule Formalisation Tool (RFT);
- AI/NLP rule extraction;
- semantic rules storage;
- Building Codes and Rules API;
- Data API;
- Results API;
- IDS Repository;
- microservice orchestration;
- compliance checking microservices;
- integration strategies.

This is not merely a conceptual article. Public source repositories and API specifications exist.

## Architectural overlap

ACCORD explicitly separates:

1. **rules**;
2. **data requirements**;
3. **data/model retrieval**;
4. **checking microservices**;
5. **orchestration**;
6. **results/evidence**;
7. **process/permitting**.

This is the separation we need.

### Decision

Use ACCORD as the baseline/reference architecture for the normative execution layer.

Our architecture must justify every incompatible custom abstraction.

---

# 2. AEC3PO already models most entities we were about to put into Rule IR

The public `Accord-Project/aec3po` repository defines the Architecture, Engineering, Construction Compliance Checking and Permitting Ontology.

It already models:

## Documents
- Document;
- DocumentSubdivision;
- sections/tables/images/etc.;
- internal/external references.

## Statements
- Statement;
- DefinitionStatement;
- CheckStatement;
- Checklist;
- Category;
- Certificate;
- Boolean;
- Numerical;
- Human-evaluated statements.

## Data requirements
- DataRequirement;
- IDS.

## Evidence
- Evidence and evidence formats.

## Check methods
- CheckMethod;
- BooleanCheckMethod;
- ComponentCheckMethod;
- SHACLCheckMethod;
- CompositeCheckMethod;
- FunctionCheckMethod.

## Feature of interest
- FeatureOfInterest;
- Property;
- PropertyKind;
- QuantityKind.

## Execution/results
- CheckingAct;
- ProcessVerifier;
- ComplianceVerificationReport;
- ValidationResult;
- Severity.

## Design/model
- Design;
- BIM Model;
- Phase;
- Element;
- Classification.

## Legal/permitting
- legal verifier;
- state/private verifier;
- permitting actors/stages.

It aligns with external standards/ontologies including:
- ELI;
- QUDT;
- ifcOWL;
- Function Ontology;
- SKOS;
- DUL;
- lifecycle/stage ontologies.

This directly removes a large amount of ontology design work.

### Critical insight

AEC3PO revolves around the **statement/regulation and how it is checked**, not merely around building elements.

That is exactly the direction needed for Russian SP/GOST rules.

### Decision

**ADAPT AEC3PO rather than invent a base SBIM compliance ontology.**

Potential custom extension:
`sbim-ru:`
- Russian legal force/applicability;
- dated/undated normative references;
- mandatory/voluntary status;
- supersession/amendment;
- official Registry Requirement ID;
- Russian jurisdiction/site applicability;
- our project-specific causal bindings.

---

# 3. BCRL already covers the logic that our proprietary Rule IR was meant to express

The ACCORD rule formalisation methodology uses:

- RASE markup;
- BCRL expressions;
- bSDD term mapping;
- AEC3PO semantic representation.

## RASE categories

RASE identifies:
- Requirement;
- Application;
- Selection;
- Exception.

This is especially relevant to Russian norms, where a requirement rarely exists as a context-free number.

Example conceptual form:

```
APPLICATION:
  building type / use / height / area / jurisdiction

SELECTION:
  which branch of requirement applies

EXCEPTION:
  explicit exclusions

REQUIREMENT:
  value / relation / formula / qualitative condition
```

This is much closer to real normative logic than a flat:
`ROOM_AREA >= 18`.

## BCRL expression examples already support

- simple properties;
- comparisons;
- units;
- object classifications;
- existential relationships;
- universal quantification;
- adjacency;
- containment;
- formulas;
- combinations of logical expressions.

Examples in ACCORD documentation include patterns like:
- width > 1.2 m;
- object type == House;
- wall exists and is external;
- all adjacent spaces have property X;
- contained lifting device meets multiple requirements;
- formula-based slope checks.

### Decision

Our internal "Rule IR" should be renamed/reframed as a **Russian compiler target**, not a brand-new language.

Candidate target:
- BCRL/AEC3PO for general rule semantics;
- IDS for information-presence/value requirements;
- SHACL for graph/data validation;
- SPARQL for graph computations/queries;
- external microservices for geometry/engineering;
- human-evaluated status where no deterministic check exists.

---

# 4. ACCORD already solved the "how does a rule call an engineering program?" abstraction

This is one of the most important findings.

ACCORD classifies execution context into three broad categories:

1. **Simple data lookup**
   - value can be retrieved directly from a model/data source.

2. **Process result**
   - value requires a specialist calculation such as energy analysis;
   - an external microservice is invoked.

3. **Cannot be checked automatically**
   - requires human evaluation.

This is almost exactly the architecture we derived for:
- Archicad properties;
- CYPE;
- FEA;
- Ladybug/Honeybee;
- daylight;
- LCA;
- spatial GIS;
- qualitative architectural review.

## bSDD mapping

Terms are mapped to bSDD:
- classes;
- properties;
- units;
- equivalent terms.

For computed terms, the property can be associated with a process/application URI.

### Consequence

We should not encode specialist computations directly into every normative rule.

A rule should reference a semantic term, whose resolution says:

```
Width
  -> direct BIM lookup

DaylightFactor
  -> Honeybee/CYPELUX microservice

StructuralUtilization
  -> FEA microservice

DistanceToBoundary
  -> GIS/geometry microservice

ArchitecturalCompatibility
  -> HUMAN_OR_AI_REVIEW
```

This makes the checking engine replaceable and fast.

---

# 5. ACCORD already specifies the microservice capability registry/router we were designing

The ACCORD "Orchestrating Microservices" component:

1. maintains a list of available compliance microservices;
2. queries each service for its capabilities;
3. parses the BCRL ruleset;
4. determines execution order;
5. resolves terms through bSDD;
6. selects a capable microservice;
7. calls the service;
8. integrates results.

This is almost exactly the proposed SBIM tool router.

## Integration strategies

ACCORD defines two modes:

### Strategy A
Central orchestrator:
- parses rules;
- invokes several loosely-coupled microservices;
- combines results.

### Strategy B
One self-contained checker:
- receives rule/code;
- handles all checks internally.

This maps perfectly to our actual tools:

Strategy A:
- CYPEURBAN + Honeybee + FEA + spatial API + Archicad data.

Strategy B:
- Проектология;
- BIM Grade;
- Tangl Control;
- Solibri for a whole rule set.

### Decision

Do not invent the basic orchestration protocol.

Adopt the **capability-registry + specialist microservice** pattern and extend only where project transactions/healing require more than compliance checking.

---

# 6. ACCORD Results API is already a concrete protocol for external checker integration

The public OpenAPI specification in `Accord-Project/API-Development` defines an asynchronous Results API.

A checking microservice exposes:

## Capability metadata
- name;
- description;
- operator;
- supported model formats;
- supported terms/checks.

## Check request
Can contain:
- building-code references;
- model URLs;
- additional data;
- entity IDs to restrict scope;
- webhook URL;
- supporting-file webhook.

## Execution
- asynchronous job ID;
- status endpoint.

## Results
- JSON;
- BCF;
- result per entity;
- true / false / unknown;
- tolerance/miss value;
- supporting evidence.

This is extremely close to what we would need to wrap:
- Проектология;
- BIM Grade;
- CYPE;
- Solibri;
- Tangl;
- our own narrow geometry checks.

### Strong recommendation

Create **SBIM Checker Adapter** around the ACCORD Results API shape rather than a new proprietary interface.

Vendor-specific adapters translate:
`ACCORD-like request ↔ vendor API`.

This would make compliance engines replaceable.

---

# 7. ACCORD Building Codes and Rules API already solves versioned immutable rule distribution

The public OpenAPI spec includes:

- list hosted building codes;
- latest version retrieval;
- explicit version retrieval;
- jurisdiction;
- classification;
- language;
- execution vs visualisation forms;
- explicit vs summary rule format;
- GraphQL query;
- IDS retrieval;
- new version upload.

Most importantly:

**published building-code versions are immutable.**
A changed code creates a new version.

This is exactly the correct pattern for our Russian normative database.

### Consequence

Do not model "SP 464.yaml" as one mutable file.

Model:

```
jurisdiction = RU
classification = SP_464_1325800_2019
version = edition/change-state/hash
immutable = true
effective interval = ...
official source refs = ...
```

A new amendment generates a new immutable compiled ruleset.

Project audit references the exact version.

This naturally supports historical replay.

---

# 8. Rule Formalisation Tool already exists and its source is public

The ACCORD Rule Formalisation Tool is a web tool for domain experts.

It integrates:
- RASE;
- AEC3PO;
- BCRL.

It supports:
- manual tagging;
- automatic NLP-assisted tagging/formalisation.

Its role is exactly what we were planning as a future "norm editor".

### Code/licensing caution

The source repository is public, but the repository-level software license was not clearly confirmed in this pass.

Do not copy code until licensing is clarified.

The methodology/data models can still be used as architectural references.

---

# 9. ACCORD-NLP and CODE-ACCORD remove much of the generic regulation-NLP research burden

## ACCORD-NLP

Public package:
`pip install accord-nlp`

Apache-2.0 license.

It provides:
- entity extraction;
- relation extraction;
- information extraction;
- sentence → knowledge graph;
- pretrained models;
- synthetic data augmentation.

The repo was still updated in 2026.

## CODE-ACCORD

Open annotated regulation corpus:
- English regulations;
- Finnish regulations;
- entities;
- relations;
- train/test splits;
- HuggingFace datasets.

This is not Russian training data.

But it gives us:
- label designs;
- annotation methodology;
- model benchmark;
- extraction pipeline;
- synthetic augmentation pattern.

### Russian adaptation

Instead of inventing a regulation NLP pipeline:

1. adapt ACCORD labels/relations to Russian;
2. bootstrap with LLMs;
3. create a small gold Russian dataset from already manually verified SP clauses;
4. fine-tune/evaluate only if LLM extraction is insufficient.

This can drastically reduce annotation/research effort.

---

# 10. SHACL is a serious candidate for the deterministic graph validation layer

A 2024 comparative study evaluated:
- Solibri;
- IDS;
- JSON Schema;
- XSD;
- OWL;
- SWRL;
- SPARQL;
- SHACL.

For Linked Data validation, SHACL was judged particularly suitable because it is standardized for validation input/output and designed for validation use cases.

A September 2026 Advanced Engineering Informatics paper proposes:
- machine-readable standards;
- ISOProps ontology;
- semantic information requirements;
- SHACL;
- direct validation of Linked Building Data;
- automated workflows that reduce repeated manual rule modelling when standards change.

Another 2024 study demonstrates:
- compliance ontology;
- external FEA solver;
- IFC enrichment;
- SHACL checks;
- structural code verification.

This proves a key point:

**SHACL can validate graph/property/relational constraints while specialist engineering remains in external solvers.**

### Recommended layered execution

```
IDS
  simple information requirements

SHACL
  graph/property/cardinality/relationship validation

SPARQL
  computed graph queries / derived values

BCRL/AEC3PO
  regulation semantics, applicability, logic and execution mapping

external microservices
  geometry, daylight, FEA, fire, MEP, LCA, etc.

human/AI review
  qualitative/non-machine-checkable clauses
```

This is much better than one giant custom rule engine.

---

# 11. DigiChecks independently reaches the same semantic architecture

The public `semmtech/digichecks-ontology` repository is CC-BY and provides a top-level permit ontology based on EN 17632 / Semantic Modelling and Linking.

It models:
- projects;
- permits;
- requirements;
- verification;
- decisions;
- documents;
- locations.

It aligns with:
- PROV;
- GeoSPARQL;
- SKOS;
- DC Terms;
- other standards.

Most importantly, its public repository contains real SHACL pilot rules for:
- Austrian zoning;
- Austrian building height;
- required documents;
- Spanish cases;
- UK cases.

There are valid/invalid example datasets.

That means open, reusable patterns for **zoning and permit rules in SHACL already exist**.

This matters directly for our Russian:
- PZZ;
- GPZU;
- territorial zoning;
- height/setback checks.

Before writing our own graph validation form, reproduce a DigiChecks zoning pilot and then translate one Russian rule into the same pattern.

---

# 12. CHEK confirms that the standards-based digital permit stack is an ecosystem, not a one-off research prototype

The completed Horizon Europe CHEK project delivered a toolkit for:
- BIM + GIS;
- machine-readable rules;
- automated compliance;
- digital permitting;
- open standards;
- OpenAPI-style integration.

Its 2026 standards deliverable reports contributions to:
- IFC;
- IDS;
- CityJSON;
- LOIN;
- OGC approaches;
- cross-project harmonisation among CHEK, ACCORD and DigiChecks.

### Strategic implication

We should not build a closed Russian-only technology stack.

We should build a **Russian semantic/compiler layer compatible with the emerging international open permit/compliance architecture.**

This preserves future interoperability.

---

# 13. D-COM shows ACCORD is part of a longer lineage

The older D-COM Digital Compliance Ecosystem already defined:
- Compliance Document Architecture;
- machine-readable Compliance Document format;
- APIs.

ACCORD extends/refines this work.

This reinforces the reuse decision:
our project should not create yet another incompatible compliance document format.

---

# 14. Revised Russian normative architecture after checkpoint 20

```
OFFICIAL RUSSIAN SOURCES
  Стройкомплекс
  Росстандарт
  Минстрой
  pravo
  PZZ/GPZU/GIS
        |
        v
SOURCE ADAPTERS / CURRENTNESS / LEGAL APPLICABILITY
        |
        v
Russian canonical requirement
        |
        v
RASE + AEC3PO / BCRL compiler
        |
        +---- IDS (information requirements)
        |
        +---- SHACL (semantic/data constraints)
        |
        +---- SPARQL (derived graph queries)
        |
        +---- PROCESS TERM
                 |
                 v
          capability registry
                 |
      +----------+-----------+---------+
      |          |           |         |
      v          v           v         v
    CYPE      Solibri      Tangl     FEA/LCA/
   engines     / IFC      Control    daylight/etc.
      |
      +-------------+
                    v
          ACCORD-like Results API
                    |
           JSON / BCF / evidence
                    |
                    v
              SBIM project graph
                    |
           impact / healing / DDR
```

This is now the preferred direction.

---

# 15. What remains genuinely Russian/custom after this discovery

## Keep custom

1. Source adapters for Russian official/commercial/open normative systems.
2. Russian legal force/applicability and temporal logic.
3. Mapping official requirement IDs/clauses into AEC3PO/BCRL.
4. Russian terminology/bSDD dictionary mappings where absent.
5. Russian rule-extraction gold dataset and validation.
6. Project causal/change graph.
7. Architectural design-intent specialization.
8. Candidate/healing ranking.
9. Cross-tool transaction planning.
10. Archicad 29 deep/event gaps.

## Stop treating as custom invention

- base compliance ontology;
- base rule language;
- base regulation markup semantics;
- generic rule repository API;
- generic immutable rule-version pattern;
- generic checker capability registry;
- generic compliance orchestrator;
- generic async checker/results API;
- generic BCF result format;
- generic semantic validation engine;
- generic regulation NLP pipeline;
- generic permit ontology.

---

# 16. New implementation gate

Before implementing any proprietary `RuleIR`, `CheckService`, `RuleRepository` or `ComplianceRouter` type, require a written incompatibility proof against:

- AEC3PO;
- BCRL;
- SHACL;
- IDS;
- ACCORD APIs.

Default decision is now:
**ADAPT OPEN STANDARD / GAP EXTENSION.**

---

# 17. Highest-value experiment: RULE-OPEN-01

After AC29 template priority is closed, use one already verified Russian rule from SP 464.

Pipeline:

1. Source exact Russian requirement from our verified fixture.
2. Mark it in RASE:
   - Application;
   - Requirement;
   - Selection;
   - Exception.
3. Serialize as AEC3PO/BCRL YAML-LD.
4. Map terms to bSDD/custom Russian dictionary.
5. Decide execution type:
   - lookup;
   - process result;
   - human review.
6. If simple data rule:
   - compile to SHACL or IDS.
7. If geometry/process rule:
   - route through one external checker mock/adapter.
8. Return result through ACCORD Results API schema.
9. Bind result to an Archicad/IFC entity ID.
10. Export BCF/evidence.
11. Change the norm edition.
12. create immutable new rule version and confirm project invalidation.

## Success criterion

If one realistic Russian SP rule can complete this path without loss of required semantics, then our proprietary Rule IR should be abandoned in favor of the open stack.

---

# 18. Second experiment: RUS-NLP-01

Use 50–100 previously manually verified Russian norm clauses.

Compare:
- cloud LLM extraction;
- ACCORD-NLP adapted extraction;
- hybrid LLM + RASE validation.

Measure:
- entity extraction;
- applicability;
- exception extraction;
- numerical values/units;
- relation extraction;
- false hard-rule conversion;
- source traceability.

Goal:
determine whether Russian rule normalization can be mostly automated without building a new NLP framework.

---

# 19. Licensing caution

Not all public ACCORD repositories have an obvious repository-level software license file.

Confirmed in this pass:
- `accord-nlp` — Apache-2.0;
- `RegulationTransformationTool` — Apache-2.0;
- DigiChecks ontology — CC-BY.

For:
- AEC3PO source repo;
- ACCORD API implementation/spec repo;
- Rule Formalisation Tool;

public availability does **not automatically mean unrestricted reuse**.

Before copying source into SBIM:
- verify license or obtain permission;
- otherwise implement against the published concepts/specifications independently.

---

# Strategic conclusion

This is one of the most consequential reuse findings so far.

The open AEC compliance research ecosystem has already implemented the generic architecture we were about to design:

**rule semantics + rule repository + data mapping + external processes + capability-based routing + asynchronous checking + evidence/results.**

The project should now become even thinner:

**Russian legal/source compiler + project/architectural causal intelligence + Archicad integration**, sitting on top of open compliance standards and existing specialist engines.
