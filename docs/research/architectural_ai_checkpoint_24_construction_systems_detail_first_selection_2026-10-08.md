# Architectural AI checkpoint 24 — construction-system-first design, detail envelopes and early engineering selection

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Context

This checkpoint continues directly from:
- Fast Project Compiler / HOT-WARM-COLD / LIGHT-MEDIUM-HEAVY runtime;
- open compliance stack;
- semantic graph stack;
- floor-plan/spatial-logic reuse;
- AC29 control/facade/opening/dependent-element audit.

The specific question in this pass:

**How do we stop treating walls, slabs, roofs, façades, openings and junctions as abstract geometry, and instead select construction systems early enough that their real thickness, module, span, fire/acoustic/thermal performance and details constrain the architecture before it is frozen?**

## Executive conclusion

The system should not "draw geometry first and detail it later."

The correct hierarchy is increasingly clear:

```
project requirement
   ↓
construction-system candidates
   ↓
hard performance / code / structural / module filters
   ↓
real geometric envelope
   ↓
architectural layout + façade + grid
   ↓
junction/detail family
   ↓
specialist verification where needed
   ↓
instantiate native Archicad composites/profiles/GDL/Favorites
```

The core new entity should be an expanded **Approved Construction Primitive**:

# Construction System Envelope (CSE)

A CSE describes a valid family of constructible solutions, not one frozen wall object.

This keeps architectural geometry coupled to real construction from the beginning.

---

# 1. Archicad 29 already contains more envelope physics than we were treating as external

Current Graphisoft AC29 documentation confirms that the BIM already contains significant material/envelope semantics.

## Building Materials

Building Materials are global "super attributes" used by:
- elements;
- composites;
- complex profiles.

They contain:
- classification/properties;
- physical properties;
- thermal conductivity;
- density;
- heat capacity;
- energy/carbon-related material data used by energy evaluation workflows.

## Composites

Composites are ordered Building Material skins/layers used by:
- walls;
- slabs;
- roofs;
- shells.

This is already the natural native representation for many layered CSEs.

## Energy Evaluation / EcoDesigner STAR

Archicad 29 can derive energy-model geometry/material data directly from BIM.

Current workflows expose:
- Structures list;
- Openings list;
- U/R values;
- infiltration;
- solar absorptance;
- glazing/frame properties;
- orientation;
- glazed/opaque area;
- frame perimeter;
- shading;
- opening perimeter Psi;
- material physical properties.

EcoDesigner STAR adds detailed building-performance functions including **thermal-bridge analysis directly in Archicad**.

Graphisoft also documents BIM-to-BEM interoperability including:
- gbXML;
- IFC/Excel workflows;
- PHPP-related workflows.

### Strategic consequence

Before writing:
- basic U-value calculator;
- generic layer thermal calculator;
- generic opening heat-loss model;
- generic thermal-bridge database;

first benchmark native AC29 Energy Evaluation/EcoDesigner.

Our custom layer should compile project requirements into target ranges and trigger/verdict the native or specialist engine.

---

# 2. CYPE Construction Systems should be upstream of geometry, not downstream documentation

The free CYPE Construction Systems application already models:

- façade systems;
- party/basement walls;
- roofs;
- screeds/floors;
- exterior/interior doors/windows/skylights;
- partitions;
- floor slabs;
- suspended ceilings;
- thermal breaks.

Per system it stores:
- layers;
- thickness;
- material;
- density;
- thermal properties;
- reusable system definitions.

It can bind construction systems to BIM architectural elements and report when the system's true thickness conflicts with the architectural host thickness.

### Why this changes our architecture

A wall's thickness cannot remain a late styling parameter.

The selected system should establish a geometry constraint:

```
System:
  preferred thickness = 380 mm
  allowed = 360..420 mm
  module = ...
        ↓
Wall face / grid / clear room dimensions
        ↓
area recalculation
        ↓
opening/pier geometry
        ↓
floor/roof/detail interfaces
```

### Decision

**CYPE Construction Systems remains P0 free evaluation.**

Use it as:
- candidate construction-system registry;
- envelope/layer data source;
- host-thickness consistency checker;

unless a Russian/Archicad-native source covers the same system more directly.

---

# 3. TechnoNIKOL Navigator is much more important than a generic manufacturer catalogue

A deeper Russian-market pass found that TechnoNIKOL Navigator is effectively a construction-system platform.

Current Navigator content includes large system catalogues for:
- flat roofs;
- stylobates;
- floors;
- foundations;
- façades;
- walls/partitions;
- fire protection;
- sound insulation;
- other civil/industrial assemblies.

The platform also provides:
- system selection;
- technical calculations;
- system substantiation;
- technical-solution albums;
- unusual junction/detail selection;
- project-document review;
- estimates;
- BIM-library support.

## Direct Archicad relevance

Current TechnoNIKOL resources include Archicad-oriented downloads such as:
- system catalogue in Archicad PLA format;
- Building Materials/system catalogue;
- detail-element catalogue;
- component catalogue;
- node/detail albums as Archicad archive projects;
- parametric objects such as tapered insulation components.

The broader technical library contains hundreds of technical albums plus normative/support documents, certificates and approvals.

### Consequence

For roofs, façades, insulation, foundations and related nodes we should not create our own system/detail database first.

Preferred flow:

```
requirement
  ↓
TechnoNIKOL / other manufacturer system candidates
  ↓
verified technical album / certificate / system data
  ↓
CSE normalization
  ↓
Archicad native implementation
  ↓
node/detail bindings
```

### Decision

**P0 RUSSIAN AC29 SYSTEM LIBRARY AUDIT.**

This is probably one of the highest-value immediate reuse sources for our template/ACP library.

---

# 4. Knauf confirms that internal partitions should be selected by performance, not guessed thickness

Current Knauf Russia system pages expose quantified system performance.

Examples across current partition families include:
- system thickness ranges;
- acoustic isolation Rw;
- fire resistance EI;
- allowable heights;
- mass;
- component composition;
- fire/technical documentation.

This is exactly the correct candidate-selection model:

```
required:
  EI >= target
  Rw >= target
  height >= project floor height
  thickness <= architectural envelope
        ↓
find actual system family
```

not:

```
"make this internal wall 100 mm because that looks normal"
```

### Decision

Build provider adapters/normalized CSE facts from verified manufacturer/system sources.

Do not manually encode arbitrary partition thicknesses in AI prompts.

---

# 5. Porotherm validates the need for system-specific masonry/module grammar

A deeper Porotherm Russia pass is especially relevant to the user's earlier complaint about openings, piers and masonry modules.

Current technical documentation provides:
- block/product dimensions;
- typical nodes;
- BIM/reference materials;
- structural guidance;
- wall/opening constraints.

The published technical materials include project-dependent rules such as:
- minimum pier widths;
- different allowances for low-rise buildings;
- bearing-wall thickness depending on structural and thermal calculations;
- limitations on using masonry units in column-like conditions.

The exact applicable values depend on system/building conditions and must come from the relevant current technical/normative source.

### Strategic conclusion

There should **not** be one global:
`WINDOW_MIN_PIER = ...`

Instead:

```
MasonrySystem
  product module
  bond/course grammar
  bearing/nonbearing role
  floor count
  load state
  opening/jamb rules
  lintel family
  min pier envelope
  detail families
```

A wall system therefore directly constrains:
- legal opening positions;
- module-safe wall movement;
- allowed façade rhythm;
- door/window dimensions;
- lintel selection;
- junction geometry.

This is the missing link between "wall moved 35 mm" and "architect moves it to a buildable module."

---

# 6. Structural-system selection should precede final room/grid geometry

Another major finding is **Branch Concept Lite**.

## Shipping now

The current Branch site explicitly marks **Concept Lite — Available Now — Free**.

Current public capabilities:
- browser-based;
- real-time structural analysis;
- material/system comparison;
- timber, steel, concrete, hybrid structures;
- multi-bay exploration;
- member sizing;
- fire protection/fire-rating considerations;
- live quantities;
- live embodied carbon.

The public full Branch Concept product is separate and is still in beta/waitlist development, with broader:
- code regions;
- complex geometries;
- detailed outputs;
- collaboration/export.

Do not confuse the shipping free Lite tool with the fuller upcoming product.

## Why it matters

It provides exactly the early feedback we need:
- approximate structural depth;
- grid/span implications;
- material/system families;
- carbon/quantity effects;

before detailed engineering is complete.

### Decision

**P0 FREE REFERENCE/TEST.**

It may not connect directly to AC29, but it is a ready concept-stage structural envelope engine and an excellent benchmark for our structural-system selector.

---

# 7. Tenzor Intelligence validates the architecture, but Design Studio is not production yet

Current Tenzor modules publicly available include:
- orchestrator/Brain;
- validated calculator modules;
- document package builder;
- model viewer;
- structural audit;
- import/report extraction.

MCP access is currently private beta.

Tenzor's **Design Studio** describes almost our desired structural-option workflow:

```
architectural drawings / IFC / Revit
   ↓
IFC-aligned BIM with provenance
   ↓
structural scheme families
   ↓
T0 cheap triage
   ↓
T1 surrogate ranking
   ↓
T2 OpenSeesPy / ETABS only for 3–5 finalists
   ↓
Pareto ranking:
 cost / carbon / structural depth / schedule / code reserve
```

But its own site labels Design Studio as a **research preview / being built**.

### Decision

Use Tenzor's architecture as a strong method reference.

Do **not** treat Design Studio as a current dependency.

This distinction is mandatory in our matrix.

---

# 8. IDEA StatiCa removes more custom structural-detail work

IDEA StatiCa now provides mature local REST APIs and official Python/C# clients.

The Connection API can:
- create/update connections;
- apply parametric connection templates;
- update parameters;
- apply load effects;
- run CBFEM calculations;
- retrieve pass/fail and detailed results;
- generate reports;
- calculate production cost;
- export IFC/IOM;
- browse a Connection Library;
- ask the library to propose suitable design items for a connection topology/code;
- publish company/private templates.

This is extremely close to a **structural-node candidate library + verifier**.

The API supports local automation and even provides LLM-oriented documentation.

### Consequence

For steel/connection detail classes, our node system should be:

```
connection topology
   ↓
candidate template/library item
   ↓
parameter mapping
   ↓
IDEA StatiCa calculation
   ↓
verified connection
   ↓
IFC/detail/report
   ↓
SBIM evidence + DDR
```

Do not write a steel-connection solver or connection-template search engine.

---

# 9. Detail verification should be tiered

A construction detail does not need the same expensive analysis every time.

Recommended verification ladder:

## T0 — metadata/rule envelope
- layer continuity;
- known approved system;
- correct system/detail family;
- manufacturer applicability;
- simple dimensional ranges.

Milliseconds/seconds.

## T1 — native BIM/building-physics check
- Archicad Energy Evaluation/EcoDesigner;
- CYPE system checks;
- direct product/system calculators.

Seconds/minutes.

## T2 — specialist numerical analysis
Only on high-risk/new/changed details:
- flixo;
- WUFI;
- FEA;
- fire/CFD;
- detailed acoustic solver.

Minutes/hours.

This matches the Fast Project Compiler principle:
**do not run the deepest model on every wall edit.**

---

# 10. Thermal bridges and moisture already have specialist engines

## flixo

Current flixo product line supports building-physics detail analysis including:
- EN ISO 10211-type thermal-bridge workflows;
- EN ISO 10077-2-related window/frame calculations;
- Psi values;
- surface temperatures;
- condensation/mould risk;
- DXF import;
- material/boundary-condition libraries;
- parametric detail variations.

## Schöck thermal-bridge calculator

Schöck currently exposes an online Psi calculator for junction classes such as:
- balconies;
- parapets.

It calculates:
- heat flow;
- surface temperature;
- Psi values;

for manufacturer-system-specific junctions.

## WUFI

WUFI provides validated dynamic coupled heat/moisture simulation.

Relevant product families cover:
- 1D hygrothermal assemblies;
- 2D;
- whole-building variants;
- moisture;
- driving rain;
- condensation;
- retrofit;
- more detailed thermal-bridge problems.

Limited/free versions exist for some workflows.

### Decision

Do not write:
- thermal-bridge FEM;
- hygrothermal solver;
- condensation/mould solver.

CSE/detail objects should store the **verification recipe/provider**, not the equation engine.

---

# 11. Acoustic selection also has specialist tools

INSUL and comparable building-acoustics tools already predict sound insulation for:
- walls;
- floors;
- ceilings;
- windows;
- material/construction variants.

Such tools are useful for rapid alternatives but do not replace certified laboratory/system data where a project requires it.

### Decision

For common certified partition systems:
prefer manufacturer tested/certified data.

Use acoustic simulation for:
- nonstandard assemblies;
- optimization;
- comparison.

---

# 12. Carbon/cost/circularity is already a mature external evaluation layer

One Click LCA / Carbon Designer 3D has grown far beyond a simple carbon calculator.

Current workflows include concept-stage:
- building type/area/floor count;
- reference buildings;
- primary structural systems;
- alternative assemblies;
- products/suppliers;
- embodied-carbon comparison;
- cost comparison;
- operational-carbon context.

Current 2026 product additions also include:
- Sustainable Planner workflows;
- lifecycle cost;
- circularity/resource-passport functions;
- service-life/replacement modelling;
- material/product passport concepts.

An Archicad 29 connector had already been identified in earlier research.

### Consequence

We should not build:
- EPD database;
- generic LCA calculation engine;
- generic service-life replacement engine;
- circularity scoring engine;
- generic lifecycle cost database.

CSE stores mappings to the external evaluator and caches verified results.

---

# 13. Maintainability and repairability need to be first-class decision criteria

Architectural selection cannot stop at:
- passes code;
- cheapest;
- lowest carbon.

CSE should include or link to:
- expected service life;
- maintenance interval;
- replacement accessibility;
- wet/dry installation;
- demountability;
- repair locality;
- disassembly sequence;
- replacement dependency;
- warranty/technical maintenance instructions;
- product availability/substitution class.

This can use data from:
- manufacturer technical documentation;
- LCA/product passports;
- circularity platforms;
- internal office experience.

### Design rule

A candidate that is slightly cheaper but requires destructive replacement of several adjacent systems should carry a higher lifecycle/disruption penalty.

---

# 14. DfMA research confirms that a system must contain connection/assembly grammar, not just layer thickness

Current BIM/DfMA research already models:
- component relations;
- connection relations;
- assembly operations;
- prefabricated subsystem decomposition;
- assembly/logistics cost;
- carbon;
- module dimensions.

This matters because a 300 mm "wall" is not equivalent to another 300 mm wall if:
- junction families differ;
- installation sequence differs;
- permissible opening rules differ;
- tolerances differ;
- transport/panel/module logic differs.

### CSE addition

```
assembly_grammar:
  components
  connection_types
  permissible_interfaces
  tolerance_rules
  installation_order
  replacement_order
  prefabrication_module
  logistics_limits
```

---

# 15. Decision algorithms are commodity too

Research and existing tools already use combinations of:

- hard constraint filtering;
- set-based design;
- AHP;
- PROMETHEE;
- NSGA-II / Pareto search;
- surrogate models;
- lifecycle cost;
- LCA;
- regulatory gating.

Therefore CSE selection should not be a mysterious LLM preference.

## Selection pipeline

```
candidate systems
        ↓
HARD FILTER
 code
 fire
 structural
 acoustic
 thermal
 moisture
 geometry/module
 availability
        ↓
FEASIBLE SET
        ↓
MULTI-CRITERIA RANKING
 design intent
 cost
 carbon
 buildability
 maintenance
 circularity
 schedule
 disruption
        ↓
top candidates
        ↓
deep specialist check only where needed
```

The LLM may:
- interpret user intent;
- explain trade-offs;
- propose weights;

but deterministic/known MCDM/Pareto methods should execute ranking.

---

# 16. Proposed core object: Construction System Envelope (CSE)

This should be treated as an extension/specialization of ACP.

Example normalized schema:

```yaml
system_id:
system_family:
provider:
source_documents:
version:
verified_at:

applicable_host_types:
  - wall
  - slab
  - roof
  - facade
structural_role:
fire_role:

geometry:
  preferred_thickness:
  min_thickness:
  max_thickness:
  module_x:
  module_y:
  course_height:
  allowed_span_range:
  allowed_height_range:

openings:
  allowed_families:
  min_pier_envelope:
  jamb_module:
  lintel_families:
  sill_families:
  reveal_families:

performance:
  fire:
  acoustic:
  thermal:
  moisture:
  airtightness:
  structural:

appearance:
  surface_family:
  joint_rhythm:
  opening_rhythm_compatibility:
  allowed_finishes:

assembly_grammar:
  components:
  connections:
  tolerances:
  installation_sequence:
  replacement_sequence:

economics:
  cost_source:
  cost_range:
  install_time:

sustainability:
  epd_refs:
  embodied_carbon:
  service_life:
  replacement_factor:
  circularity:
  disassembly_score:

archicad_recipe:
  building_materials:
  composite:
  complex_profile:
  favorite:
  gdl_objects:
  pla_library:
  property_classification_bindings:

detail_families:
  wall_to_slab:
  wall_to_roof:
  window_jamb:
  window_sill:
  parapet:
  foundation:
  penetration:

verification_recipe:
  t0_rules:
  t1_provider:
  t2_provider:
  required_evidence:

invalidation:
  triggers:
  dependent_guid_classes:
```

The exact schema should remain compact in HOT/WARM state; full documents stay COLD.

---

# 17. Geometry must be derived from the selected system envelope

This is the central architectural correction.

Old sequence:
```
draw room
draw wall line
later decide wall construction
later discover thickness/detail problem
repair project
```

New sequence:
```
room/program intent
   ↓
candidate system class
   ↓
real thickness/module/span envelope
   ↓
generate/move wall on legal construction increment
   ↓
update clear dimensions/areas
   ↓
opening/detail grammar
   ↓
architectural plan/facade
```

That directly addresses the user's example:
a wall should not drift by an arbitrary 35 mm if the selected masonry/system grammar requires another placement.

---

# 18. Structural System Envelope should be a sibling of CSE

At concept stage, do not need a final rebar/connection design.

We need a bounded structural family:

```yaml
structural_system:
  family:
  materials:
  grid_ranges:
  span_ranges:
  structural_depth_range:
  column_wall_ranges:
  lateral_system_options:
  fire_protection:
  preliminary_carbon:
  preliminary_cost:
  compatibility:
    facade:
    floor_system:
    core:
    construction_systems:
  verification:
    T0: conceptual sizing
    T1: Branch/Karamba/other
    T2: FEA/IDEA/Dlubal
```

This allows the architectural solver to know:
- "this 11.5 m clear span is plausible but expensive";
- "this wall move invalidates the current slab family";
- "this grid shift breaks the façade module";
- "this opening conflicts with the lateral system";

without a full FEA run every time.

---

# 19. Repair hierarchy becomes more precise

Preferred low-disruption repair order:

1. adjust movable equipment/furniture;
2. substitute equivalent equipment/product;
3. substitute system/product **inside the same CSE geometric envelope**;
4. change layer/product while preserving external geometry;
5. adjust opening within façade/module/pier envelope;
6. change low-impact nonbearing partition within module;
7. change local detail family;
8. change structural member within current Structural System Envelope;
9. move high-impact wall/grid;
10. change structural system family;
11. change massing/architectural concept.

The system should escalate upward only when lower-impact repairs are infeasible.

This is a much more architect-like intervention hierarchy than "minimize number of operations."

---

# 20. High-priority practical audit after template stabilization

## CSE-01 — TechnoNIKOL Archicad system pack

Test:
- current PLA/system library in AC29;
- building materials;
- composites/profiles if supplied;
- node/detail elements;
- property/classification data;
- update/version behaviour;
- actual Russian documentation/certificate links.

Goal:
normalize 2–3 real roof/façade/foundation systems into CSE records without re-authoring them manually.

## CSE-02 — Porotherm masonry grammar

Pick one wall system and encode:
- block module;
- course;
- wall thickness;
- opening/pier rules;
- lintel family;
- verified detail references.

Then move a wall/opening and verify that solver candidates snap to valid buildable increments.

## CSE-03 — Knauf performance selector

Input:
- target EI;
- target Rw;
- height;
- max thickness.

Return feasible Knauf system families.

Goal:
prove that "select a wall" can be deterministic performance filtering.

## STRUCT-01 — Branch Concept Lite

Use same simple building mass/grid alternatives.
Record:
- span/grid;
- structural depth;
- material system;
- carbon;
- quantity.

Goal:
construct a first Structural System Envelope.

## DETAIL-01B — thermal bridge ladder

One real window/parapet/slab-edge detail:
- T0 approved detail metadata;
- T1 Archicad EcoDesigner;
- T2 flixo or specialist calculator.

Goal:
measure which checks need to run on every edit vs only milestone/deep audit.

---

# 21. New roadmap removals

Custom implementation is now blocked pending reuse tests for:

- generic Building Material property database;
- generic U-value engine;
- generic thermal-bridge solver;
- generic hygrothermal solver;
- generic acoustic solver;
- generic LCA/EPD database;
- generic circularity engine;
- generic lifecycle-cost engine;
- generic construction-system catalogue;
- generic manufacturer detail archive;
- generic steel-connection solver;
- generic structural connection library;
- generic early structural sizing engine;
- generic multi-criteria optimizer.

Custom justified layer:
- provider adapters;
- Russian applicability/currentness;
- CSE normalization;
- module/opening/interface grammar;
- architectural design-intent compatibility;
- cross-system dependency/invalidation;
- repair hierarchy;
- AC29 instantiation/readback.

---

# 22. Current maturity classification

## Shipping/available now
- Archicad 29 Energy Evaluation;
- EcoDesigner STAR subject to eligible license;
- CYPE Construction Systems;
- TechnoNIKOL Navigator/catalogues;
- Knauf system data;
- Porotherm technical systems/details;
- Branch Concept Lite — free/current;
- IDEA StatiCa APIs/library;
- flixo;
- WUFI;
- INSUL;
- One Click LCA/Carbon workflows;
- BIMsmith Forge (Revit-centric).

## Shipping but weak direct AC29 fit
- FenestraPro — Revit/Forma oriented;
- BIMsmith Forge — Revit-oriented.

## Research/method references
- structural set-based optimization;
- wall-assembly MCDM/Pareto research;
- DfMA connection/assembly ontologies;
- multi-objective façade/window research.

## Explicitly not production dependency
- Tenzor Design Studio — research preview/current development.

---

# Strategic conclusion

The "detail-first" correction is now implementable without building a giant proprietary materials/construction engine.

The right model is:

**select a verified Construction System Envelope early, let it generate geometric constraints, and only then finalize architectural geometry.**

A wall in SBIM should therefore never be merely:
`line + thickness`.

It should be:
`project intent + selected construction system + structural role + module + opening grammar + detail family + verification evidence + Archicad implementation recipe`.

That is much closer to how an architect actually reasons about a constructible building.
