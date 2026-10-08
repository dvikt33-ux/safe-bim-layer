# Architectural AI checkpoint 28 — Vertical Core Envelope and Architectural Design Grammar

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Context carried forward

This checkpoint continues directly from checkpoints 20–27.

Already fixed:
- AC29 first;
- HOT/WARM/COLD state;
- LIGHT/MEDIUM/HEAVY execution;
- reuse-first search gate;
- Construction System Envelope (CSE);
- Design Intent / DDR;
- floor-plan solver reuse;
- section/detail Information Obligations;
- current SPDS documentation compiler;
- existing specialist engineering/compliance engines before custom coding.

This pass attacks two remaining sources of "architectural intelligence":

1. **the vertical/service core**, whose geometry can determine the whole plan, structural system, MEP stacking and egress;
2. **architectural identity/design language**, so optimization does not gradually destroy the original architectural concept.

---

# 1. The service core is not a late room cluster — it is an upstream system

A service core combines several highly coupled subsystems:

- stairs / protected stairs;
- lift groups;
- lift lobbies;
- shafts;
- MEP risers;
- electrical/communications risers;
- toilets/wet rooms;
- technical rooms;
- structural/lateral core walls;
- fire compartmentation;
- smoke/fire interfaces;
- vertical continuity;
- accessible routes;
- maintenance/replacement access.

Therefore core design can no longer be represented as:
`place a rectangle called core`.

It must be selected before final space planning because it changes:
- net/gross efficiency;
- corridor topology;
- egress;
- structural grid/lateral system;
- slab openings;
- façade availability;
- wet-zone stacking;
- MEP distribution;
- vertical-transport service quality;
- usable area by floor.

---

# 2. Automated Service Core Generator already formalized much of this problem

The 2016 eCAADe paper **Automated Service Core Generator in Autodesk Dynamo** is substantially closer to our desired logic than a superficial "core generator".

Its decomposition is especially reusable:

## Elevator Bank Unit — EBU
- passenger/service elevator banks;
- lobbies;
- floor ranges;
- vertical zoning;
- key floor levels;
- dropping/reconfiguring lift banks as building height changes.

## Technical Room Unit — TRU
- M&E rooms;
- duct risers;
- pipe risers;
- electrical/communication shafts;
- explicit concern for structural shear-wall/core compatibility.

## Stair Hall / Restroom Unit — SRU
- stairs/fire stairs;
- restroom/wet-service programs;
- vertical continuity;
- relationships to mechanical/refuge floors.

The generator explored:
- central cores;
- split cores;
- end cores;
- atrium-core arrangements;
- service-core count;
- internal arrangement;
- net/gross ratio;
- core-to-floor distances;
- elevator-bank zoning.

Most importantly, the paper states a direct **Building Shell ↔ Service Core dependency**:
changing shell geometry triggers core recomputation.

That is exactly our causal-graph principle.

### Decision

Do not invent service-core decomposition theory.

Use:
`EBU + TRU + SRU + structural/fire/wet-stack extensions`
as the conceptual starting point.

---

# 3. The elevator component should be solved by elevator specialists, not architectural intuition

## AdSimulo

Current AdSimulo v6.x is a web-based lift-traffic analysis and expert system.

Current public capabilities:
- passenger-by-passenger simulation;
- up/down/two-way/mixed traffic;
- office/hotel/residential/retail/hospital/etc.;
- conventional and destination control;
- high-rise zoning;
- sky lobbies;
- twin/double-deck-like specialist cases;
- average wait / time-to-destination / interval / handling capacity;
- expert system searches configurations;
- 3D;
- BIM/IFC handoff;
- Russian-language UI is currently listed.

Current version observed in September 2026 release notes: 6.6.0.

Its own current workflow explicitly says:
**traffic analysis must precede lift layout/BIM.**

That is the correct dependency.

## Peters Research Elevate

Elevate remains an established specialist vertical-transport traffic-analysis tool.

Current support material includes templates based on:
- CIBSE Guide D;
- ISO 8100-32.

## DigiPara Elevatorarchitect / Liftdesigner

Current DigiPara workflow provides:
- early VT concept layouts;
- detailed lift planning;
- LOD 100–500 depending on product;
- PDF;
- DWG;
- IFC;
- Revit output.

This can translate a traffic solution into spatial/BIM requirements.

### Consequence

Our system should consume a **lift-system envelope**:
- number of cars;
- capacity;
- speed;
- serving floors/zones;
- shaft/car dimensions;
- lobby requirement;
- pit/headroom where known;
- service/firefighter requirements;
- maintenance envelope.

It should not calculate elevator dispatch physics itself.

---

# 4. Archicad 29 itself already contains a local stair constraint solver

This is a major direct AC29 reuse point.

Current Archicad 29 Stair Rules & Standards allows project-specific ranges for geometry variables.

Current documented behavior:
- the created Stair automatically adheres to the configured rules;
- flights can stretch/shrink within rules;
- minimum landing length can be enforced;
- tread/riser ranges are enforced;
- walking-line ranges are constrained;
- headroom rule can be configured;
- collision detection can find headroom conflicts;
- when input geometry conflicts with rules, Archicad's Stair Solver proposes alternative geometries.

Most importantly:
**Stair Rules & Standards are stored in the project template**, explicitly so company- or region-specific settings can be reused.

### Consequence for TDK_AC29.tpl

Do not build a general stair geometry solver.

Compile verified Russian/project stair constraints into Archicad's native:
`Rules & Standards`
where expressible.

Our role:
- select which current Russian rule applies;
- populate allowed ranges;
- decide stair location/type;
- evaluate core/egress impacts;
- let native Archicad solve local stair geometry;
- read back and validate.

This is exactly the desired split between global architectural reasoning and local native geometry solving.

---

# 5. PeopleFlow adds a deeper evacuation-performance layer without custom pedestrian physics

A 2026 open research framework, **PeopleFlow**, provides:
- automated floor-plan ingestion;
- multi-agent pedestrian simulation;
- congestion-aware routing;
- clearance time;
- density;
- bottleneck;
- exit-utilization metrics;
- reproducible scenario batches.

The published evaluation reports 660 simulations across multiple layouts/scenarios.

This is not a Russian fire-code certification engine.

But it is useful as a **HEAVY design-performance evaluator**.

Layering:

```
LIGHT:
  normative path width / travel / exits

WARM:
  TopologicPy / graph egress

HEAVY:
  PeopleFlow-style multi-agent evacuation simulation
```

Again: do not run this on every wall drag.

---

# 6. Proposed object: Vertical Core Envelope (VCE)

The core should be represented similarly to CSE: as a verified family/envelope of feasible solutions, not one frozen rectangle.

Example:

```yaml
vce_id:
version:
source_decisions:

building_scope:
  building_type:
  floors:
  heights:
  populations_by_floor:
  zones:

placement:
  strategy:
    - central
    - split
    - end
    - atrium
  allowed_regions:
  max_core_to_served_area_distance:
  facade_contact_policy:

vertical_transport:
  traffic_provider:
  traffic_result_id:
  lift_banks:
    - served_floors:
      car_count:
      capacity:
      speed:
      control_type:
      shaft_envelope:
      lobby_envelope:
  service_lifts:
  firefighter_lifts:

egress:
  stair_count:
  stair_types:
  separation_requirements:
  stair_envelopes:
  discharge_strategy:
  refuge_or_special_floors:

wet_and_service:
  toilets:
  wet_stack_zones:
  plumbing_risers:
  HVAC_risers:
  electrical_risers:
  telecom_risers:
  refuse_other_shaft_families:

structure:
  lateral_role:
  core_wall_system:
  coupling_beams:
  opening_limits:
  structural_envelope:

fire_smoke:
  compartments:
  shaft_ratings:
  lobby_protection:
  smoke_control_interfaces:

continuity:
  vertically_locked_components:
  allowed_drop_or_shift_components:
  transfer_floors:
  shaft_termination_rules:

geometry:
  preferred_area:
  max_area:
  width_depth_ranges:
  grid_module:
  floor_specific_profiles:

performance:
  net_to_gross:
  max_travel:
  lift_level_of_service:
  structural_efficiency:
  MEP_distribution_penalty:
  facade_penalty:

archicad_recipe:
  zones:
  walls:
  stairs:
  openings:
  shafts:
  objects:
  favorites:

verification_recipe:
  LIGHT:
  WARM:
  HEAVY:

invalidation:
  triggers:
```

---

# 7. Vertical-core changes belong near the top of the impact hierarchy

A core move is potentially more disruptive than moving an ordinary wall.

Typical propagation:

```
MOVE CORE
  ↓
stairs/lifts/shafts
  ↓
all served floors
  ↓
corridors
  ↓
room/program areas
  ↓
wet-zone stacks
  ↓
slab openings
  ↓
structural lateral system
  ↓
MEP distribution
  ↓
fire compartments / egress
  ↓
façade / rentable area / cost
```

Therefore VCE should be classed approximately with:
- structural grid;
- major bearing walls;
- massing;
- primary façade system;

not with ordinary room equipment.

In normal repair:
**core movement should be one of the last local fixes attempted.**

---

# 8. Architectural identity can be formalized as grammar rather than an image similarity score

The user has repeatedly emphasized:
a technically correct repair must not destroy the intended architectural image.

This is the unresolved risk of pure optimization.

Existing shape-grammar research and tools provide a much stronger representation than "compare two renders".

## Shape Machine

Georgia Tech's current Shape Machine 1.2.0 provides:
- explicit shape rules;
- rule sequences;
- conditional rules;
- programs/DrawScript;
- Python interaction;
- design-history tracking;
- transformation/matching operations.

DrawScript is documented as a Turing-complete rule language.

This is not Archicad-specific.
But it proves a mature generic grammar engine already exists.

## ArcGIS CityEngine CGA

CityEngine's CGA is a production procedural architectural grammar language.

It supports:
- massing from initial shapes;
- subdivision into façades/floors/tiles;
- repeated bays;
- windows;
- materials;
- façade patterns;
- roof rules;
- reusable/importable rule sets.

This is especially relevant to:
- façade rhythm;
- bay logic;
- floor bands;
- repeated windows;
- special ground/top floors;
- massing grammar.

## Research confirmation

Research combining **Space Syntax + Shape Grammar** explicitly captures:
- spatial configuration;
- formal/3D style;

then generates variations of the same design language.

A 2026 performance-driven 3D shape-grammar paper adds:
- a controllable 3D constraint system;
- design-intent-driven form generation;
- performance optimization on grammar-generated forms.

### Decision

We should not invent the theory of architectural style rules.

We need a project-specific specialization.

---

# 9. Proposed object: Architectural Design Grammar (ADG)

ADG is a machine-checkable representation of architectural identity.

It is not a style prompt.

Example:

```yaml
grammar_id:
design_intent_ref:
precedent_refs:

massing:
  primary_volumes:
  silhouette_rules:
  datum_levels:
  allowed_setbacks:
  forbidden_transformations:
  symmetry_policy:
  hierarchy:

plan:
  primary_axes:
  circulation_hierarchy:
  public_private_service_rules:
  spatial_sequence_patterns:
  protected_views_or_vistas:
  core_relationship:
  repeated_bay_logic:

facade:
  vertical_axes:
  horizontal_datums:
  bay_module:
  opening_families:
  allowed_width_height_families:
  sill_head_alignment:
  solid_void_ranges:
  corner_rules:
  base_middle_top_logic:
  entrance_hierarchy:
  exceptional_bays:

materials:
  palette:
  joint_module:
  transition_rules:
  finish_hierarchy:

details:
  characteristic_edges:
  depth_reveal_rules:
  cornice_parapet_logic:
  preferred_detail_families:

transformations:
  allowed:
  conditionally_allowed:
  forbidden:

tolerances:
  numeric:
  topological:
  visual:

priority:
  invariants:
  strong_preferences:
  weak_preferences:
```

---

# 10. ADG should distinguish invariants from preferences

This is essential.

Example:

## Invariant
`main facade vertical axes must remain continuous over floors 2–6`.

Breaking it is not acceptable in a normal local repair.

## Strong preference
`window widths should remain in family {1200, 1500, 1800}`.

Can be relaxed after impact review.

## Weak preference
`secondary-service windows should align where practical`.

Can be traded against equipment/MEP.

This mirrors how architects actually protect concept:
not every aesthetic relation has equal importance.

---

# 11. Grammar should constrain candidate generation before optimization

Bad pipeline:

```
generate arbitrary geometry
  ↓
optimize area/daylight
  ↓
compare final facade image
  ↓
discover architecture destroyed
```

Correct pipeline:

```
ADG
  ↓
allowed transformation space
  ↓
candidate generation
  ↓
hard rule / engineering filters
  ↓
performance optimization
  ↓
ADG conformance
  ↓
rank
```

The grammar shrinks the search space.

This is faster and preserves design identity by construction.

---

# 12. Spatial grammar and formal grammar should be separate but linked

The combined Space Syntax + Shape Grammar literature suggests a useful split.

## Spatial grammar
- room adjacency;
- sequence;
- privacy;
- circulation hierarchy;
- visibility;
- public/service separation;
- topology.

Execution can use:
- TopologicPy;
- Space Syntax;
- graph constraints;
- OR-Tools.

## Formal grammar
- massing;
- façade;
- bays;
- window rhythm;
- materials;
- proportions;
- details.

Execution/reference engines:
- Shape Machine;
- CityEngine CGA;
- Grasshopper.

The project links both through Design Intent.

This prevents a beautiful façade grammar from producing a bad plan, or a good topology from becoming formal noise.

---

# 13. Diffusion/generative models are useful only inside bounded envelopes

Current 2025–2026 floor-plan research has moved toward **conditioned generation** rather than unconstrained "make a plan".

A 2026 multi-stage diffusion approach accepts:
- outer boundary;
- structural wall plan;
- room masks;
- spatial anchors;
- room type list;

then generates layouts/openings and exports to IFC.

This is the correct role for learned generation:
**fill a bounded design envelope**, not establish the authoritative constraints.

Likewise RL/other generators should not directly own:
- current Russian compliance;
- core performance;
- structural feasibility;
- construction modules.

Those remain deterministic/external gates.

---

# 14. Current LLM spatial reasoning remains insufficient as the geometry authority

FloorplanQA (ICML 2026) evaluates structured spatial reasoning over:
- distance;
- visibility;
- paths;
- constrained object placement.

Its results show frontier models still fail inconsistently on physical/spatial constraints.

Therefore:
**GPT must not be the numerical geometry kernel.**

It should:
- interpret architectural intent;
- choose/reason about tools;
- propose candidate transformations;
- explain tradeoffs;

while:
- OR-Tools;
- TopologicPy;
- native AC solvers;
- geometry libraries;
- engineering tools;

determine geometric validity.

This reinforces the entire layered architecture.

---

# 15. Revised early-design dependency order

The current best dependency order is now:

```
SITE / PZZ / GPZU / HERITAGE
            ↓
PROGRAM / POPULATION
            ↓
STRUCTURAL SYSTEM ENVELOPE
       ↘
        VERTICAL CORE ENVELOPE
       ↗
FIRE / EGRESS / LIFT TRAFFIC / MEP
            ↓
ARCHITECTURAL DESIGN GRAMMAR
            ↓
FLOOR / SPACE LAYOUT
            ↓
CSE / REAL WALL-SLAB-ROOF ENVELOPES
            ↓
OPENINGS / FACADE
            ↓
DETAIL INTERFACES
            ↓
DOCUMENTATION
```

These are not strictly one-way.
They form controlled feedback loops.

But the graph makes explicit that:
- core;
- structure;
- construction systems;
- design grammar;

must exist before final room-wall geometry is treated as stable.

---

# 16. Practical experiment CORE-01

Use one multi-storey building shell.

Input:
- floor areas;
- floor populations;
- use type;
- heights;
- approximate structural system.

Generate at least:
- central core candidate;
- split-core candidate;
- end-core candidate.

For each candidate calculate:
- stair/egress feasibility;
- lift requirement via specialist result or documented envelope;
- shaft/riser area;
- structural impact;
- corridor/travel effect;
- net:gross;
- façade loss;
- wet-stack continuity.

Output:
a VCE record per candidate.

Do not model final architectural details yet.

---

# 17. Practical experiment STAIR-AC29-01

In `TDK_AC29.tpl` sandbox:

1. Create a Russian-rule stair preset from verified active norms.
2. Store it in Project Template Rules & Standards.
3. Attempt geometry below/above allowed tread/riser/landing ranges.
4. Record Archicad Solver alternatives.
5. Change storey height.
6. verify story-linked stair update.
7. test headroom/collision.
8. Model Dump/readback final geometry.

Success:
native AC29 solver replaces a custom local stair solver.

---

# 18. Practical experiment ADG-01

Use one existing architectural concept.

Describe only 10–20 high-value invariants/preferences, e.g.:
- primary façade bay;
- horizontal datum;
- opening family;
- major axis;
- entrance hierarchy;
- protected public sequence;
- core position zone;
- one material transition;
- one corner rule.

Then make four changes:
- enlarge an internal room;
- move one partition;
- resize one window;
- move one structural line.

For each:
1. generate several feasible candidates;
2. discard grammar-breaking candidates;
3. rank remaining candidates;
4. compare with architect judgement.

Success:
architecture remains recognizable without image-similarity hacks.

---

# 19. Practical experiment GRAMMAR-ENGINE-01

Do not commit to one grammar engine.

Represent one façade rule set in:
- simple SBIM declarative form;
- Shape Machine/DrawScript or a small adapter;
- optionally CityEngine CGA if available.

Measure:
- expressiveness;
- runtime;
- ease of mapping to AC29;
- ability to explain a violation;
- dependency on proprietary software.

Likely production architecture:
ADG remains vendor-neutral;
external grammar engines are optional executors.

---

# 20. New roadmap removals

Custom implementation is BLOCKED pending demonstrated gap for:

- elevator traffic simulator;
- elevator dispatch optimizer;
- generic lift concept drawing engine;
- generic stair local geometry solver;
- pedestrian evacuation physics engine;
- generic shape grammar engine;
- generic procedural façade grammar engine;
- unconstrained custom floor-plan diffusion model.

Custom justified:
- Russian VCE applicability;
- VCE integration between lift/fire/MEP/structure/Archicad;
- ADG project schema;
- translation of design intent into grammar rules;
- AC29 materialization/readback;
- cross-system invalidation;
- architectural ranking.

---

# Strategic conclusion

Two large parts of "architect intuition" can now be made explicit without pretending a single LLM understands everything.

**Service-core intelligence** becomes a Vertical Core Envelope assembled from proven specialist calculations.

**Architectural identity** becomes an Architectural Design Grammar that constrains the search space before optimization.

The resulting AI does not merely find a code-compliant arrangement.

It searches only inside a space of:
- buildable;
- serviceable;
- structurally plausible;
- vertically coherent;
- architecturally recognizable

solutions.
