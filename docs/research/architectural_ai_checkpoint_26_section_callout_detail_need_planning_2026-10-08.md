# Architectural AI checkpoint 26 — automatic section, callout and detail-need planning

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Context carried forward

This checkpoint continues the current architecture without reopening prior decisions:

- AC29 first;
- HOT/WARM/COLD state;
- LIGHT/MEDIUM/HEAVY execution;
- Coverage Signatures;
- Construction System Envelope (CSE);
- Documentation Contract / Sheet Recipe;
- AC29 native + Tapir as primary documentation executor;
- current SPDS baseline: GOST R 21.101-2026 + correction set, GOST 21.501-2018.

The problem in this pass:

**How does the system decide which building sections, wall sections, elevations, fragments and details are actually necessary, and where should the cutting planes/callouts be placed, without either missing critical construction information or generating hundreds of redundant views?**

---

# 1. Russian SPDS already gives machine-usable section-placement seeds

## GOST 21.501-2018

Current rule text says section lines are generally placed so that the section includes characteristic elements such as:

- window openings;
- exterior gates/doors;
- stairwells;
- elevator shafts;
- balconies;
- loggias;
- similar vertically informative conditions.

The same standard requires sections to communicate:
- grids/axes;
- level relationships;
- openings/holes/niches by height;
- characteristic structural/envelope levels;
- wall thickness where needed;
- multi-layer construction composition;
- detail/fragment references.

This is not enough to uniquely determine all section lines, but it provides **hard seed targets** for a candidate generator.

## GOST R 21.101-2026

The current standard contains an extremely useful anti-overproduction rule:

If a part of a plan/elevation/section needs more detailed representation, local views/details/fragments are added.

But:
**if all necessary information can be shown in the main image, a callout/detail should not be created.**

This gives the Documentation Compiler a formal minimization principle:

```
create additional view
ONLY IF
required information remains unresolved at the parent view's scale/content
```

This should become a hard documentation policy.

---

# 2. A 2026 research method already learns where architects put section lines

A current open-access Computer-Aided Civil and Infrastructure Engineering paper:

**"A deep learning-based framework for automated section line generation in BIM models"**

proposes two stages:

1. **AutoLabel**
   - automatically derives section-line labels from existing 2D drawings;
   - reduces the manual labeling burden.

2. **AutoSection**
   - learns section-line placement patterns;
   - predicts section lines;
   - a Dynamo parametric algorithm then generates the BIM section view.

Reported evaluation:
- 199 residential/commercial 2D drawings;
- 3,184 images after augmentation;
- AutoLabel average SSIM: 92.7%;
- average AutoLabel runtime: 1.87 s/drawing;
- AutoSection average SSIM: 95.39%.

## Why this matters

The part we thought was "architect intuition that cannot be formalized" is already learnable from historic documentation.

A future office-specific model can learn:

```
past accepted floor plans
        +
their real section markers
        ↓
AutoLabel-style dataset
        ↓
office section-line predictor
```

## Important limitation

Do **not** let the predictor become the final authority.

Its training corpus may differ by:
- country;
- project type;
- firm;
- drawing phase;
- building scale;
- local SPDS practice.

Therefore its role should be:

**candidate generator / prior**, followed by deterministic coverage validation.

### Decision

**REUSE METHOD; DO NOT INVENT SECTION-LINE ML FROM ZERO.**

Training our own model is deferred until deterministic + precedent methods prove insufficient.

---

# 3. SWAPP shows that view/callout selection is already productionized

Current SWAPP documentation product explicitly claims it can generate:

- callouts;
- enlarged plans;
- interior elevations;
- views;
- sheets;
- dimensions/tags;
- arrangement/decluttering;

and can reapply the documentation logic after design changes.

It also says its output is grounded in the firm's own production history and standards.

This is currently the strongest commercial evidence that:

**"which views/callouts does this project need?" is already a production AI category.**

### Decision

Keep SWAPP as:
- P0 enterprise benchmark/demo;
- source of acceptance criteria;
- possible future dependency if API/access/cost fit.

Do not start a generic ML view-selection platform before a serious SWAPP evaluation.

---

# 4. Draftwright is an unusually relevant open-source reference for view planning and coverage

Repository:
`pzfreo/draftwright`

License:
AGPL-3.0.

It targets mechanical/technical drawings rather than architecture, so it is not a drop-in product for AC29.

But architecturally its internal design is extremely relevant.

## Existing concepts

Draftwright already implements a **drawing compiler**:

```
recognized/declared model features
       ↓
drawing requirements
       ↓
view planning
       ↓
page/scale selection
       ↓
annotation placement
       ↓
coverage lint
       ↓
repair/export
```

Current documentation includes:

- semantic feature recognition;
- section A-A automatically triggered when hidden internal geometry cannot be communicated adequately;
- demand-guided annotation planning;
- view blocks with real footprints;
- coverage lint;
- fidelity/legibility/completeness diagnostics;
- section/detail escalation;
- requirement-driven view planning work;
- automatic semantic view selection work.

Most importantly:
**coverage lint is independent of rendering.**
An upstream omission should not be able to disappear simply because the resulting sheet "looks clean."

That is exactly the architecture our Documentation Compiler needs.

## License caution

AGPL source cannot simply be copied into a differently licensed project without a deliberate license decision.

Use:
- method;
- architecture;
- test ideas;

before code reuse.

### Decision

**HIGH-VALUE METHOD/ARCHITECTURE REFERENCE.**

---

# 5. Direct LLM view selection should not be our primary algorithm

A 2026 DFKI/University of Paderborn technical-drawing study connects multimodal LLMs directly to CAD through MCP.

The agent can:
- select views;
- place them;
- inspect visual results;
- iteratively refine.

But the study reports that current multimodal LLMs still struggle to match human drafting decisions in:
- view selection;
- layout quality.

### Consequence

Do not give GPT a blank plan and ask:
"where should I cut?"

Use GPT for:
- intent interpretation;
- explanation;
- unusual-condition review;
- tie-breaking.

Final view planning should be:
- requirements-driven;
- feature-aware;
- coverage-audited;
- solver-backed;
- optionally informed by learned office priors.

---

# 6. Existing detail products solve the next stage once a callout condition is known

## PiAxis

Current PiAxis is Revit-only, but its workflow is exactly relevant to our future AC29 detail layer.

It:
- reads the active model/callout context;
- searches the firm's past detail library;
- finds closest matching approved details;
- compares wall layers/materials/project conditions;
- adapts the old detail;
- resizes components;
- completes annotations;
- flags uncertain items for review.

It also allows firm leaders to mark a smaller "Verified Details" set.

This strongly supports our donor-detail-first architecture.

## BIMLOGIQ / Revit tools

Other current Revit tools can already mass-create:
- wall sections;
- correctly oriented sections;
- auto-sized crop regions;
- room interior elevations.

This confirms that **view materialization after the target wall/room is chosen is commodity automation**.

### Decision

Custom intelligence should focus on:
- deciding a view/detail is needed;
- choosing the relevant condition;
- validating information coverage;

not on generic section creation mechanics.

---

# 7. Proposed new object: Information Obligation (IO)

The Documentation Compiler needs an intermediate semantic object between the BIM model and the drawing view.

Example:

```yaml
obligation_id: IO-AR-SECTION-023
kind: vertical_relationship
severity: hard
source:
  type: GOST_21_501_2018
  clause: ...
affected_entities:
  - Stair_GUID
  - Slab_GUID
  - Roof_GUID
required_facts:
  - floor_levels
  - stair_landings
  - roof_relationship
acceptable_view_types:
  - building_section
minimum_scale: 1:100
satisfied_by: []
status: UNSATISFIED
```

Other IO kinds:

- opening_vertical_geometry;
- stair/core relationship;
- elevator shaft;
- floor-level change;
- roof ridge/valley/parapet;
- atrium/double-height;
- structural grid/transfer;
- façade stepback;
- balcony/loggia;
- expansion/deformation joint;
- accessible ramp;
- wet-core stack;
- plant/equipment room;
- fire compartment boundary;
- envelope interface;
- unusual CSE junction;
- penetration/opening interface;
- architectural design-intent condition.

The building may have thousands of elements, but only tens/hundreds of **documentation obligations**.

---

# 8. Candidate section generation should be multi-source

Do not search the infinite plane space blindly.

Generate candidates from:

## A. Normative seeds

Cut through:
- stairs;
- elevators;
- characteristic openings;
- balconies/loggias;
- level changes;
- structural/envelope conditions required by current documentation rules.

## B. Geometry/topology seeds

Generate cuts through:
- major axes;
- cores;
- atria;
- double-height zones;
- roof changes;
- massing steps;
- structural system transitions;
- long/short principal directions.

## C. CSE/interface seeds

Cut through:
- wall-slab-roof transitions;
- façade/slab interfaces;
- parapets;
- foundation transitions;
- special opening families;
- joints where a verified detail family changes.

## D. Precedent/office seeds

Retrieve section patterns from:
- accepted past projects;
- donor drawing sets;
- office documentation standards.

## E. Learned seed

AutoSection-style predictor.

## F. User locks

Architect-selected views remain immutable unless explicitly released.

---

# 9. Every candidate section gets a Coverage Vector

For each candidate cut, compute which Information Obligations it actually explains.

Example:

```text
Candidate S17
  stair_vertical_relationship      = covered 1.0
  roof_ridge                       = covered 1.0
  elevator_shaft                   = 0
  facade_stepback                  = 0.8
  wet_stack                        = 0.6
  opening_head_sill_levels         = 1.0
```

Coverage can be:
- binary for hard facts;
- weighted for visibility/clarity;
- conditional on scale/depth.

Candidate quality should consider:

- number/weight of obligations covered;
- uniqueness of information;
- construction risk;
- normative importance;
- design-intent importance;
- vertical complexity;
- model-change frequency;
- visual clarity;
- amount of irrelevant clutter;
- redundancy with already selected views;
- page/sheet cost.

---

# 10. Final view selection is a weighted set-cover / maximum-coverage problem

This is not an LLM problem.

We already use OR-Tools elsewhere.

A section set can be selected by a CP-SAT / weighted set-cover formulation.

## Hard constraints

Every HARD Information Obligation must be covered by at least one accepted document view.

```
for every IO_hard:
  sum(view_covers[IO_hard]) >= 1
```

## Objective

Minimize approximately:

```
number_of_views
+ redundant_coverage
+ sheet_area_cost
+ visual_clutter
+ unusual_cut_penalty
```

while maximizing:

```
soft_IO_coverage
+ architectural_clarity
+ construction_information_value
+ precedent_similarity
```

This follows both:
- architectural practice;
- the general technical-drawing principle of using the **minimum sufficient** set of views.

### Decision

**REUSE OR-TOOLS; DO NOT BUILD A NEW OPTIMIZER.**

---

# 11. View hierarchy should escalate only when information remains unresolved

Recommended hierarchy:

```
PLAN / ELEVATION
       ↓ unresolved vertical/detail information?
BUILDING SECTION
       ↓ interface still ambiguous?
WALL / LOCAL SECTION
       ↓ fine construction condition unresolved?
DETAIL / CALLOUT
       ↓ component-specific fabrication need?
COMPONENT SECTION / SHOP-DRAWING REFERENCE
```

This implements GOST R 21.101-2026 5.5.3 directly:

**Do not create an additional detail if the parent image already communicates all required information.**

This is also the cure for document bloat.

---

# 12. Detail Need Detector should operate on the CSE interface graph

Every constructible detail is fundamentally an interface condition.

Example:

```
Facade_CSE
  INTERFACE
Slab_CSE
  INTERFACE
Window_CSE
```

The Detail Need Detector forms a condition signature:

```yaml
interface_signature:
  host_system: POROTHERM_X
  opening_system: WINDOW_FAMILY_A
  facade_finish: BRICK_1NF
  slab_edge: MONOLITHIC_RC
  insulation: ...
  fire_requirement: ...
  climate_condition: ...
  geometry:
    jamb:
    sill:
    head:
```

Then:

1. Search verified detail family.
2. Search Russian manufacturer/TPD source.
3. Search donor project detail.
4. Adapt if within applicability envelope.
5. If none fits, create a new detail task.

The view/callout is therefore generated because an **unresolved interface obligation exists**, not because "architects usually put a bubble here."

---

# 13. Detail deduplication should be semantic

Ten geometrically identical conditions should not create ten separate details.

Use a normalized Detail Condition Signature.

If:

```
signature(A) == signature(B)
```

then:
- one verified detail can serve multiple callout markers;
- project references point to the same detail.

If a project-specific difference affects:
- fire;
- moisture;
- structural interface;
- dimensions;
- product;
- geometry envelope;

the signatures diverge and a separate detail becomes necessary.

This can dramatically reduce documentation noise.

---

# 14. Architectural elevations are simpler than sections but still need coverage planning

Base elevation candidates:
- each distinct external façade orientation / façade plane family;
- not merely four compass directions.

Additional façade fragments become necessary when:
- articulation cannot be legibly shown at base scale;
- finish family changes;
- significant level change;
- recessed/returned façade is occluded;
- historic/context condition needs independent documentation;
- CSE/detail family changes.

Again:
use parent-view coverage first, fragment only when information remains unresolved.

---

# 15. AC29 implementation audit: straight sections are already executable

Direct Tapir source audit confirms current `CreateSections` accepts:

- startCoordinate;
- endCoordinate;
- depth;
- name;
- floorIndex.

So straight section creation is already directly automatable.

Current `CreateInteriorElevations` accepts a chain of room boundary nodes and creates linked interior-elevation segments.

## Current gaps observed in this pass

### Jogged/complex building sections
Current Tapir `CreateSections` schema is two-point/straight-line.

If the selected architectural section needs a jogged cutting plane:
- first check whether another existing provider exposes it;
- otherwise this may justify a small native/Tapir extension.

### Linked Detail/Callout marker creation
Tapir currently exposes independent Detail databases.
A fully linked Archicad detail/callout-marker creation path was not verified in this pass.

Treat as:
`GAP_NOT_YET_PROVEN`,
not immediate custom work.

### General exterior Elevation creation
A generic `CreateElevations` Tapir command was not verified in this pass.

Again:
audit provider/API surface before implementing.

---

# 16. New Coverage objects

## View Coverage Signature

```yaml
view_id:
view_type:
source_project_revision:
cut_geometry_hash:
view_depth:
scale:
covered_IO_ids:
coverage_weights:
unresolved_IO_ids:
redundant_with:
precedent_source:
prediction_source:
locked_by_user:
status:
  VALID
  DIRTY_GEOMETRY
  DIRTY_REQUIREMENT
  DIRTY_DETAIL_INTERFACE
  REDUNDANT
  INCOMPLETE
```

## Detail Coverage Signature

```yaml
detail_id:
interface_signature_hash:
detail_family:
source:
  manufacturer
  donor
  office_standard
  new
applicability_envelope:
covered_IO_ids:
verification_status:
referenced_from:
status:
```

These integrate with the existing Document Coverage Signature.

---

# 17. Proposed two-stage section planner

## LIGHT/WARM — deterministic

Use every design iteration.

1. Detect Information Obligations.
2. Generate candidate cut seeds.
3. Reuse accepted existing sections where valid.
4. Run coverage scoring.
5. Solve minimum sufficient section set.
6. Dirty only changed views.

Expected runtime:
seconds, not minutes.

## HEAVY — learned/precedent

Run:
- project setup;
- major scheme change;
- milestone;
- explicit request.

Add:
- historical section predictor;
- multimodal office precedent;
- more expensive visual quality analysis;
- SWAPP/enterprise comparison if available.

The heavy stage suggests improvements but does not bypass the coverage gate.

---

# 18. Practical experiment SECTION-NEED-01

Use one real AC29 project with at least:
- two or more storeys;
- stair;
- roof change;
- several window/door conditions;
- one balcony/loggia or projection;
- one structural/level transition if available.

## Phase A — manual gold set

The architect selects the minimal set of sections considered sufficient.

Record:
- lines;
- direction;
- reason for each section;
- information conveyed.

## Phase B — automatic obligations

Generate IOs from:
- GOST;
- geometry;
- CSE;
- design intent.

## Phase C — candidates

Generate:
- axis-aligned candidates;
- stair/core candidates;
- roof/level-transition candidates;
- opening/façade candidates;
- precedent candidates.

## Phase D — solver

Use OR-Tools to choose minimal sufficient view set.

## Metrics

- HARD IO coverage;
- number of generated views;
- overlap with architect gold set;
- obligations missed by human set;
- redundant automated sections;
- average information density;
- manual corrections needed;
- time.

Primary KPI:
**human minutes to accepted section set.**

---

# 19. Practical experiment AUTOSECTION-REFERENCE-01

Before training anything:

1. Collect 10–30 completed floor plans with accepted section markers from our own/student/office archive where legally usable.
2. Test automatic extraction of section markers from PDFs/DWG.
3. Compare extracted markers to ground truth.
4. Classify:
   - stair/core cuts;
   - longitudinal/transverse building cuts;
   - wall sections;
   - detail cuts.
5. Estimate whether an office-specific dataset is large/consistent enough for an AutoSection-style model.

No training sprint until this evidence exists.

---

# 20. Practical experiment DETAIL-NEED-01

Choose one façade bay containing:
- wall;
- slab;
- window;
- sill/head/jamb;
- insulation/finish.

Create all interface obligations.

Then test:

1. What is visible at 1:100?
2. What becomes clear at 1:50?
3. What still requires 1:20 wall section?
4. What still requires 1:5 detail?
5. Which repeated conditions can share one detail?
6. Which detail source can satisfy each condition:
   - TechnoNIKOL;
   - manufacturer;
   - donor project;
   - office verified library;
   - new detail.

Success criterion:
zero redundant callouts while every hard interface obligation is satisfied.

---

# 21. Practical experiment VIEW-IMPACT-01

Start from a valid section/detail set.

Change one item at a time:

- window size;
- wall position;
- stair geometry;
- roof geometry;
- structural grid;
- CSE wall system.

Verify:

- only dependent View Coverage Signatures become dirty;
- a new view is requested only if an obligation becomes unresolved;
- redundant existing views can be flagged;
- accepted detail references survive when their applicability envelope remains valid.

---

# 22. New roadmap removals after checkpoint 26

Custom implementation is BLOCKED pending demonstrated gap for:

- section-line ML from scratch;
- generic view-set optimizer;
- generic room interior-elevation creator;
- generic wall-section creator;
- generic firm-detail search engine;
- generic detail adaptation AI;
- generic technical-drawing LLM agent.

Reuse:
- AutoSection method;
- OR-Tools;
- Tapir;
- donor-detail system;
- SWAPP benchmark;
- PiAxis workflow pattern;
- Draftwright compiler/coverage architecture.

---

# 23. Custom scope that remains justified

1. Russian/SPDS Information Obligation compiler.
2. Project-specific obligation extraction from CSE/design intent/causal graph.
3. Candidate section/elevation seed generation.
4. Coverage scoring semantics.
5. Detail Condition Signature.
6. View/Detail Coverage Signatures.
7. AC29 provider gaps proven by tests.
8. Firm-specific training-data adapter only if a learned model becomes necessary.
9. Acceptance/regression benchmark against architect-selected view sets.

---

# Strategic conclusion

The correct problem is not:

> "teach GPT where architects usually draw section lines."

It is:

> "compile all information that must be communicated, generate plausible views, and select the minimum set of views that proves every required fact clearly."

The strongest architecture is therefore:

```
Verified Project Truth
       ↓
Information Obligations
       ↓
Candidate Views
  GOST / geometry / CSE / precedent / learned prior
       ↓
Coverage Matrix
       ↓
OR-Tools minimum sufficient view set
       ↓
Tapir / Archicad materialization
       ↓
Coverage Gate
       ↓
Details only for unresolved interfaces
```

This is more deterministic, more auditable and more architect-like than a free-form AI drawing generator.
