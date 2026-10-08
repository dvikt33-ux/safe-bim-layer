# Architectural AI checkpoint 31 — Program/Room Requirement Envelopes, functional relationships and operational flow

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Context

This checkpoint continues after:
- AC29-first runtime;
- CSE / VCE / ADG;
- floor-plan/section/detail/documentation compiler work;
- whole-system reuse audit;
- FLOORA/specialist-model training strategy;
- Architect Skill OS / evidence hierarchy.

The specific gap attacked here is one of the user's original complaints:

**The AI can draw rooms, but it does not yet have a sufficiently explicit architectural-programming model explaining why a room exists, how large it may be, what equipment/activities it must support, which other rooms it must or must not touch, and which user/service flows may cross it.**

The answer is not another free-form prompt.

We need a structured program layer upstream of geometry.

---

# 1. dRofus is the strongest current program/room-requirements backbone found for AC29

Current dRofus product/help documentation confirms:

- structured Rooms and Function/Sub-Function hierarchy;
- Programmed Area;
- Designed Area synchronized from BIM;
- Room Data Sheets;
- Room Templates;
- Item/Equipment lists;
- Finishes;
- Groups/Classifications/Statuses;
- Function Data before detailed room geometry exists;
- Room Item Checks;
- bidirectional Archicad Add-On;
- direct Archicad Zone ↔ dRofus Room synchronization;
- Archicad Object ↔ dRofus Item synchronization;
- IFC integration;
- REST API with OpenAPI/Swagger;
- OAuth2/Bearer support;
- read-only project API-key option.

This is far closer to our missing "programming database" than a custom YAML room list.

## Critical data distinction already built into dRofus

dRofus separates:

- **Programmed Area** — what is required;
- **Designed Area** — what the BIM actually contains.

This maps perfectly to the user's requirement that "changing area" is not an abstract action.

In SBIM:

```
target/min/max area = requirement
actual area = measured consequence of wall/zone geometry
```

The system must never directly "set actual area" as if it were an independent variable.

It must:
1. change actual geometry;
2. read actual Zone/room area back;
3. compare against the requirement envelope.

---

# 2. dRofus Room Templates are almost exactly our reusable room-type standard layer

Current dRofus room templates can carry:
- programmed area;
- room data;
- item/equipment lists;
- finishes;
- classifications/statuses/groups;
- centrally propagated updates;
- derived-room exceptions.

This gives us an existing answer to:
"How do we avoid re-inventing the requirements for every WC, office, electrical room, exam room, etc.?"

Preferred model:

```
Room Type / Template
       ↓
project occurrences
       ↓
local deviations
       ↓
actual Archicad Zones
```

A room occurrence should therefore be linked to:
- a reusable template identity;
- a project-specific deviation set;
- an actual AC29 Zone/GUID.

Do not duplicate the full template payload into every AI context.

---

# 3. Room Data Sheets solve far more than room area

Current dRofus documentation explicitly defines Room Data as **functional and constructional engineering requirements for a room**.

A Room Requirement record may therefore include much more than:
- name;
- target area.

It can carry, depending on project schema:
- dimensions/heights;
- environmental requirements;
- acoustic requirements;
- finishes;
- power/data;
- sanitary/plumbing;
- equipment;
- furniture;
- security;
- room classifications;
- operating/maintenance needs;
- documents/images.

This is exactly the type of data that should constrain layout before walls become stable.

### Consequence

The future architecture agent should not reason:
"Office = 12 m² because that seems normal."

It should query the active Room Requirement Envelope.

---

# 4. Equipment-to-room dependency is already implemented as rule logic in dRofus

The current **Room Item Check** can define rules connecting room equipment/items to constructional requirements.

Official examples include:
- number of computers ↔ required power outlets;
- item type ↔ minimum/maximum room temperature;
- noisy item ↔ required sound insulation.

This is a major match to the user's earlier point:
equipment is normally lower-impact than a wall, but equipment may impose requirements on the room.

The causal direction can be:

```
equipment/item
    ↓ requires
clearance / utility / environment / load / access
    ↓
Room Requirement Envelope
    ↓
fit test
    ↓
only if infeasible:
repair hierarchy
```

The room is not sized only by nominal area.

It must also contain a feasible arrangement of its required activities/items.

---

# 5. Direct AC29 integration already exists

Current dRofus Archicad Add-On supports bidirectional synchronization of program data and design data.

Current official workflows include:
- linking dRofus Rooms to Archicad Zones;
- synchronizing Zone/model properties back to dRofus;
- current examples include Designed Area, Ceiling Height and Perimeter coming from Archicad;
- linking dRofus Items to Archicad Objects;
- comparing Planned vs Modeled equipment occurrences in Zones.

Supported linked Archicad element types include, among others:
- Doors;
- Windows;
- Walls;
- Curtain Walls;
- Slabs;
- Electrical Equipment;
- Lighting Fixtures;
- Columns;
- Beams;
- Roofs;
- Morphs;
- Shells;
- Skylights;
- Railings;
- Stairs.

### Strategic result

For requirements/room/equipment SSOT we should test dRofus **before writing our own AC29 room database**.

---

# 6. dRofus REST API makes AI-side orchestration technically viable

Current dRofus REST API:
- exposes OpenAPI specification;
- exposes interactive Swagger UI;
- supports project/database-specific properties;
- supports OAuth2 Bearer authentication;
- provides multiple regional API endpoints;
- supports filtering/select/order/paging;
- supports project data automation;
- API-key mode exists for read-only use;
- API-key mode is explicitly not intended for machine-to-machine production writes.

### Consequence

Future SBIM provider can be:

```
dRofus REST API
       ↓
Program/Room Requirement adapter
       ↓
SBIM Context Capsule / solver
       ↓
AC29
```

Production write integration should use proper OAuth2/Bearer or an approved integration path, not a read-only user API-key hack.

A current ChatGPT plugin-directory search did **not** surface a dedicated dRofus or Hypar plugin, so direct ChatGPT integration should currently be assumed to require REST/API or our provider adapter rather than a ready ChatGPT connector.

---

# 7. Important limitation: dRofus should not be mistaken for the whole spatial planner

Current dRofus documentation says Function Data supports adjacency definition.

However:
- the historical **Graphical Function Planner** was removed from dRofus from version 2.14;
- the old graphical planner/relational requirement UX should therefore not be treated as a current dependency.

This is an important boundary.

Recommended role:

**dRofus = authoritative structured program/room/equipment requirement source.**

Not:
**dRofus = our geometric adjacency/layout solver.**

Adjacency/flow optimization should remain in:
- our Program Relationship Graph;
- OR-Tools;
- TopologicPy;
- FloorPlan6 methods;
- optional external planning UI/benchmark.

---

# 8. BriefBuilder is a serious alternative/reference for the requirements graph

Current BriefBuilder publicly positions the brief/program as a structured requirements model.

Current documented capabilities include:
- spaces, systems and elements as structured objects;
- requirements with value/unit/source references;
- must-have vs nice-to-have distinction;
- IFC design-vs-requirement verification;
- API access for feeding requirements into design tools;
- reusable templates;
- automated bubble diagrams;
- functional adjacency visualization;
- logistics/walking-distance relationships.

This is particularly relevant to our cross-room relationship model.

## Comparison

### dRofus strengths for SBIM
- direct Archicad integration;
- room/equipment depth;
- templates;
- designed/programmed delta;
- API;
- BIM object synchronization.

### BriefBuilder strengths
- explicit generic requirements-management model;
- hard/soft requirement framing;
- bubble/adjacency/logistics communication;
- IFC validation;
- API concept.

### Decision

dRofus remains the stronger **P0 AC29 requirements backbone candidate**.

BriefBuilder is a **P1 requirements/adjacency semantics benchmark**.

Do not build both into mandatory runtime.

---

# 9. Hypar is a strong early-space-planning UX benchmark, but not our AC29 backbone

Current Hypar documentation (verified against October 2026 builds) supports:
- importing program requirements from spreadsheet;
- direct dRofus program import;
- intelligent spaces;
- live net/gross/count metrics;
- doors/windows/equipment;
- room furnishing/layout suggestions;
- design options;
- collaboration;
- program-vs-placed tracking.

The dRofus integration is currently documented as:
- dRofus -> Hypar one-way requirements import;
- then Hypar -> Revit;
- no current direct Hypar -> Archicad workflow was verified in this pass.

Therefore:

**Hypar is an excellent planning UX / room-fit / suggestion benchmark.**

But for our AC29-native project:
- dRofus connects directly to Archicad;
- FloorPlan6/OR-Tools/TopologicPy can provide solver logic;
- introducing Hypar into the required write path would add an unnecessary Revit-oriented hop.

### Useful Hypar lesson

Hypar explicitly recommends checking furnished room suggestions during blocking to answer:
"does this room really fit its intended occupancy/equipment?"

That validates our rule:
**area alone is insufficient; fit must be tested before layout is accepted.**

---

# 10. SEPS2BIM proves that domain programming knowledge can be a reusable data asset

The public VA/DoD healthcare **SEPS2BIM** ecosystem is a very important precedent.

Published resources describe roughly:
- ~2,100 equipment objects;
- ~1,100 space templates;
- departments;
- project program generation;
- APIs/web services;
- BIM objects/templates.

SEPS creates baseline Programs for Design and room contents from mission/workload/staffing inputs.

This is not a Russian normative source.

But it proves the architecture:

```
domain knowledge
    ↓
room templates
    ↓
equipment templates
    ↓
department/program logic
    ↓
project room program
    ↓
BIM
```

### Consequence

For Russian typologies we should eventually build/import **small verified domain packs**, not one giant universal room dictionary.

Examples:
- school;
- kindergarten;
- shopping centre;
- apartment building;
- clinic;
- office;
- hotel.

Each pack can define:
- function hierarchy;
- room templates;
- equipment/activity sets;
- relationship patterns;
- norm links.

---

# 11. Proposed core object: Program Requirement Envelope (PRE)

PRE is project/function-level intent before geometry.

```yaml
pre_id:
project_type:
version:
source_refs:

function_hierarchy:
  - department
  - subdepartment
  - function_group

population:
  user_groups:
  quantities:
  schedules:

area_budget:
  target_net:
  target_gross:
  gross_net_envelope:
  max_total_area:

room_requirements:
  - rre_id
    count:

relationship_graph:
  adjacency:
  anti_adjacency:
  distance:
  sequence:
  separation:
  stacking:

flow_classes:
  - public
  - staff
  - service
  - goods
  - waste
  - emergency
  - maintenance

security_privacy:
  zones:
  transitions:

shared_resources:
technical_requirements:
normative_refs:
design_intent_refs:

priority:
  hard:
  strong:
  weak:
```

---

# 12. Proposed core object: Room Requirement Envelope (RRE)

RRE is **not the room geometry**.

It is the feasible requirement envelope for one room/type/occurrence.

```yaml
rre_id:
template_id:
function_id:
occurrence_id:

identity:
  name:
  classification:
  security_group:

quantity:
area:
  min:
  target:
  max:
  tolerance_policy:

geometry:
  min_width:
  min_depth:
  preferred_aspect:
  ceiling_height:
  facade_contact:
  daylight_need:
  external_window_required:

occupancy:
  user_groups:
  count:
  activities:

equipment:
  required_items:
  optional_items:
  maintenance_clearances:
  operating_clearances:

access:
  door_count:
  clear_width:
  access_level:
  accessibility:

environment:
  acoustic:
  temperature:
  humidity:
  air_quality:
  lighting:

services:
  power:
  data:
  water:
  drainage:
  ventilation:
  medical_or_special:

structure:
  floor_load:
  vibration:
  wall_hanging_loads:

finishes:
fire:
security:

relationships:
  adjacency:
  anti_adjacency:
  max_distance:
  required_sequence:
  vertical_stack:

source_evidence:
priority:
```

Every field may be:
- HARD;
- STRONG;
- WEAK;
- UNKNOWN/NEED_VERIFY.

---

# 13. Proposed Functional Relationship Graph (FRG)

The relationship graph must be separate from room geometry.

Nodes:
- functions;
- departments;
- room types;
- room occurrences;
- VCE/core components;
- entrances;
- service/loading points;
- external destinations.

Edges should be typed.

Examples:

```yaml
edge:
  from: PUBLIC_ENTRANCE
  to: FOOD_COURT
  type: route
  user_class: public
  weight: high

edge:
  from: LOADING_DOCK
  to: TENANT_STORAGE
  type: service_flow
  must_not_cross:
    - public_main_route

edge:
  from: CLEAN_STORAGE
  to: WASTE_ROOM
  type: anti_adjacency
  severity: hard
```

Useful edge classes:
- direct adjacency;
- near;
- far;
- forbidden adjacency;
- visible connection;
- acoustic separation;
- security transition;
- public flow;
- staff flow;
- goods flow;
- waste/dirty flow;
- emergency flow;
- maintenance flow;
- vertical-stack requirement.

This graph represents **desired operational logic**.

---

# 14. Desired graph and realized graph must be different objects

This is essential.

## Desired FRG
What the brief/program says should happen.

## Realized Spatial Graph
What the actual AC29 model does:
- Zone adjacency;
- doors;
- corridor routes;
- vertical links;
- distances;
- visibility;
- restricted transitions.

Compute realized graph from:
- native AC29 data where possible;
- TopologicPy;
- geometry only as fallback.

Then compare:

```
Desired relationship
          vs
Realized relationship
          ↓
PASS / MARGIN / FAIL
```

This makes "bad room placement" objectively diagnosable.

---

# 15. Operational flows should become first-class layout constraints

A room-adjacency matrix alone is insufficient for complex buildings.

The user already identified the problem in shopping-centre planning:
staff/service routes should not arbitrarily intersect public routes.

The program must therefore carry **flow classes**.

Examples:

### Shopping centre
- visitors;
- tenant staff;
- goods;
- waste;
- security;
- maintenance.

### School
- pupils;
- teachers;
- visitors;
- food/service;
- emergency.

### Healthcare
- patient;
- staff;
- clean supply;
- dirty/waste;
- equipment;
- public;
- emergency.

The solver should evaluate:
- path length;
- number/type of crossings;
- shared edges;
- bottlenecks;
- security transitions;
- vertical transfers.

This can reuse:
- TopologicPy;
- NetworkX;
- DepthmapX for HEAVY spatial-syntax analysis;
- PeopleFlow for selected heavy movement simulations.

Do not code graph theory from scratch.

---

# 16. Functional placement is a facility-layout optimization problem, not a language-generation problem

Once PRE/RRE/FRG are compiled, layout candidate ranking becomes conventional constrained optimization.

Hard constraints:
- required rooms/counts;
- area minima/maxima;
- fixed core/structure/site;
- mandatory/forbidden adjacency;
- façade/daylight requirement;
- security separation;
- stack/wet/service constraints;
- Russian code rules.

Soft objectives:
- weighted adjacency;
- travel cost;
- circulation efficiency;
- public/service separation;
- net:gross;
- daylight;
- architectural grammar;
- low disruption;
- construction module.

Execution:
- OR-Tools / CP-SAT;
- FloorPlan6 methods;
- TopologicPy metrics;
- optional learned candidate priors (FLOORA/Finch).

GPT should compile the problem and interpret trade-offs, not directly invent arbitrary coordinates.

---

# 17. Correct change semantics: a program change does not directly move a wall

Example:

"Increase café back-of-house from 40 to 52 m²."

Correct pipeline:

```
PRE/RRE change
  target area 40 -> 52
        ↓
mark affected room cluster DIRTY
        ↓
retrieve neighbors + FRG + equipment + CSE + structure
        ↓
generate module-valid boundary/wall candidates
        ↓
recompute actual areas
        ↓
recompute neighboring-room envelopes
        ↓
flow/adjacency/structure/facade checks
        ↓
select feasible repair
        ↓
AC29 write
        ↓
read actual Zone areas back
        ↓
update Program-vs-Design delta
```

This implements the user's principle that:
**area change is always the result of geometry change.**

---

# 18. Room-fit test must precede acceptance

A candidate room is not accepted merely because:
`actual_area >= min_area`.

It must pass:

```
polygon/proportion
+ required equipment
+ operating clearance
+ door swing/access
+ circulation inside room
+ accessibility
+ environment/services
+ façade/window conditions
+ structural/MEP conflicts
```

Only then is the Room Requirement Envelope satisfied.

This addresses a recurring AI failure:
"area is correct but the room is unusable."

---

# 19. Proposed influence hierarchy inside the program layer

Program entities also have different disruption levels.

Approximate order:

## Very high
- building function mix;
- major department allocation;
- public/service zoning;
- VCE/core;
- primary entrances/loading;
- major vertical stacks.

## High
- room cluster topology;
- major corridors;
- wet/service room stacks;
- fire/security boundaries.

## Medium
- individual room boundary;
- room door location;
- shared support room allocation.

## Lower
- furniture/equipment location;
- equivalent equipment product;
- movable internal arrangement.

This hierarchy should feed the existing repair/disruption model.

---

# 20. Proposed source-of-truth split

Do not make one product own everything.

```
CLIENT / PROGRAM REQUIREMENTS
          ↓
      dRofus
  rooms/templates/items
          ↓
  SBIM PRE/RRE/FRG adapter
          ↓
OR-Tools / TopologicPy / layout engines
          ↓
        AC29
  actual geometry/zones
          ↓
    readback / designed area
          ↓
       dRofus
```

Other providers:
- BriefBuilder — requirement/adjacency benchmark or alternate program source;
- Hypar — optional early planning/fit UX benchmark;
- SEPS2BIM — domain-data architecture reference.

---

# 21. What NOT to code now

BLOCKED pending actual provider tests:

- generic room/requirements database;
- generic room-template system;
- generic equipment requirement database;
- generic room data sheet system;
- generic Programmed-vs-Designed area tracker;
- generic AC29 Zone-to-room synchronizer;
- generic requirement reporting system;
- generic requirement REST backend;
- generic bubble-diagram tool.

Likely custom remains:

- PRE/RRE normalization;
- FRG operational-flow schema;
- Russian typology/domain packs;
- norm/provenance links;
- hard/strong/weak semantics;
- conversion from dRofus/BriefBuilder to solver constraints;
- realized-vs-desired graph comparison;
- impact/invalidation integration.

---

# 22. Immediate tests

## PROGRAM-01 — dRofus program backbone

Build a tiny program:
- 2 departments/functions;
- 8–12 rooms;
- programmed min/target areas;
- room templates;
- groups/security class.

Verify:
- REST read;
- stable IDs;
- version/log data;
- project-specific properties.

## RDS-AC29-01

Connect the dRofus Archicad Add-On to an AC29 sandbox.

Test:
- Room ↔ Zone link;
- Programmed Area -> AC property/zone context;
- Designed Area <- Archicad;
- Ceiling Height <- Archicad;
- Perimeter <- Archicad;
- rename/move/delete;
- save/reopen;
- ID stability.

## ITEM-ROOM-01

One room template with:
- equipment list;
- power requirement;
- acoustic/environment requirement.

Test:
- planned Item list;
- Archicad Object occurrences;
- missing item;
- extra item;
- constructional Room Item Check result.

## ADJACENCY-PROGRAM-01

Define desired relationships for 10 rooms:
- hard adjacency;
- preferred adjacency;
- anti-adjacency;
- public/service flow separation.

Generate 3 layouts.

Compare:
- desired FRG;
- realized Topologic graph;
- weighted score;
- architect judgement.

## PROGRAM-CHANGE-01

Change one programmed room target area.

Verify:
- only affected cluster becomes dirty;
- actual area changes only through wall/boundary change;
- adjacent rooms recalculate;
- no arbitrary wall offset outside module;
- dRofus Designed Area receives actual readback.

---

# Strategic conclusion

This closes one of the most important remaining conceptual holes.

The AI should not start design from "a list of room names".

It should start from:

```
PROGRAM REQUIREMENTS
    PRE
      ↓
ROOM REQUIREMENT ENVELOPES
    RRE
      ↓
FUNCTIONAL / OPERATIONAL RELATIONSHIPS
    FRG
      ↓
candidate spatial layouts
      ↓
actual walls/zones in AC29
      ↓
realized graph + actual areas
      ↓
continuous comparison against program
```

For AC29, dRofus is currently the strongest ready-made backbone for the program/room/equipment side.

Our missing custom intelligence is much narrower:
**translate those requirements into architectural constraint graphs and keep them causally synchronized with actual Archicad geometry.**
