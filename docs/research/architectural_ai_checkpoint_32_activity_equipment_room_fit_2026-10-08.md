# Architectural AI checkpoint 32 — Activity/Equipment Envelopes and deterministic room-fit before wall changes

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Context

Checkpoint 31 established:
- dRofus as the strongest AC29-ready program/room/equipment requirements backbone;
- PRE — Program Requirement Envelope;
- RRE — Room Requirement Envelope;
- FRG — Functional Relationship Graph;
- actual room area is derived from wall/Zone geometry, never an independent editable scalar.

This pass attacks the next user-identified failure mode:

**A room may satisfy its nominal area and still be architecturally unusable because equipment, furniture, doors, maintenance access, operating clearances or circulation do not fit.**

The opposite is also important:

**If equipment does not fit, moving a high-impact wall should not be the first repair.**

---

# 1. Hypar already productizes "room fit" as geometry + clearance, not area alone

Current Hypar documentation (verified against v0.2.044, 2026-10-05) supports explicit **Clearance** objects on:

- furniture;
- equipment;
- doors;
- spaces.

Clearances:
- stay attached to their host;
- move/duplicate with their host;
- can be dimensioned exactly;
- can be circular or polygonal/rectangular;
- turn red when they overlap:
  - another clearance;
  - wall;
  - furniture;
  - column;
- can be intentionally accepted;
- become invalid again if the underlying overlap/geometry changes.

Door swings participate in the same live conflict model.

This is almost exactly the reactive-dependent pattern already adopted in SBIM.

### Important architectural lesson

Clearance is not just a validation number.

It is **derived geometry** attached to a source object.

---

# 2. Hypar's Suggestions validate the "fit before freeze" workflow

Current Hypar room-layout suggestions:
- propose furnished layouts based on room type/name and geometry;
- expose seat/desk/bed count;
- can "Fit to space";
- can "Expand space";
- adapt as the space changes;
- learn/reuse layouts from the current project and user/group libraries.

Hypar's own workflow guidance recommends using the suggestions during **blocking** to verify that a room is actually big enough before committing the plan.

This directly confirms the user's requirement:
equipment/furniture fit belongs before finalizing walls, not at the end.

---

# 3. Hypar libraries are a useful precedent for verified room kits

A saved Hypar space can contain:
- walls;
- furniture;
- doors;
- clearances.

Libraries can be:
- personal;
- group;
- reused across projects.

This suggests a reusable **Room Kit** layer:

```
Room Template
   dRofus requirements
        +
Room Kit
   approved geometric arrangement(s)
        +
Activity/Equipment Envelopes
        ↓
candidate room geometry
```

Do not ask an LLM to reinvent a typical exam room, office, accessible WC or plant-room arrangement every project.

Retrieve/adapt an approved kit first.

---

# 4. Finch independently confirms the "adapt a verified plan, preserve locked dimensions" pattern

Finch's current Adaptive Plan Library can:
- reuse a stored plan in new shapes;
- lock walls;
- mark walls extendable but not shrinkable;
- preserve minimum-width conditions;
- return an Adaptivity Score;
- scan/search the firm's own library.

This reinforces a generalized rule:

**Room/sub-layout adaptation should preserve invariant dimensions and only stretch declared degrees of freedom.**

The system should not uniformly scale a room kit.

---

# 5. qbiq confirms that furniture standards belong inside the planning engine

Current qbiq public documentation claims its planning engine can incorporate:
- project program;
- adjacency rules;
- spatial constraints;
- circulation;
- company planning guidelines;
- custom furniture;
- existing furniture inventory;
- finishes;
- multi-floor planning;
- efficiency/daylight/privacy metrics.

qbiq is commercial/closed and Revit/CAD oriented, so it is not a direct AC29 kernel dependency.

But it is strong evidence that:
**furniture/equipment standards + program + circulation are already treated as one planning problem in production products.**

---

# 6. dRofus remains the requirement source; geometry/fit is a separate layer

dRofus gives us:
- Items;
- Item Lists;
- Room templates;
- Item occurrences;
- Archicad Object links;
- Room Item Check.

But dRofus should not be expected to be the 2D/3D packing solver.

Recommended split:

```
dRofus
  what must exist
  quantity
  type
  room requirement
  utility/environment dependency
        ↓
SBIM Activity/Equipment Envelope
  geometric operating requirements
        ↓
Room Fit Solver
        ↓
actual AC29 objects/zones
```

---

# 7. Proposed object: Activity/Equipment Envelope (AEE)

One object may have several geometrically distinct envelopes.

Example:

```yaml
aee_id:
item_type_id:
provider:
source_ref:

physical:
  footprint:
  height:
  orientation_options:

clearances:
  installation:
  operating:
  maintenance:
  accessibility:
  door_or_drawer_swing:
  service_connection:
  emergency:

anchors:
  wall_required:
  floor_required:
  ceiling_required:
  corner_allowed:
  window_proximity:

relations:
  near:
  aligned_with:
  facing:
  anti_overlap:
  grouped_with:

utilities:
  power:
  data:
  water:
  drainage:
  ventilation:
  special:

loads:
  floor:
  wall:
  vibration:

replacement_class:
  equivalent_item_group:

priority:
  hard:
  strong:
  weak:
```

### Key rule

Physical object geometry and clearance geometry are different.

A bed may fit physically but fail because:
- transfer clearance;
- staff work zone;
- door swing;
- equipment approach;
- maintenance zone;
cannot fit.

---

# 8. Proposed Room Fit State

For each actual Zone:

```yaml
room_fit:
  zone_guid:
  rre_id:
  required_items:
  placed_items:
  missing_items:
  extra_items:
  capacity:
  clearance_conflicts:
  door_conflicts:
  internal_route_status:
  service_status:
  substitutions_used:
  fit_score:
  status:
    PASS
    FAIL
    NEED_REPAIR
    NEED_VERIFY
```

Room Fit is independent from nominal area compliance.

A room can therefore be:

- AREA_PASS + FIT_PASS;
- AREA_PASS + FIT_FAIL;
- AREA_FAIL + FIT_PASS;
- AREA_FAIL + FIT_FAIL.

Only the first is acceptable.

---

# 9. Internal room layout should use a deterministic candidate solver

For bounded room-layout problems, do not rely on GPT for coordinates.

Use:
- OR-Tools CP-SAT / no-overlap constraints;
- Shapely geometry;
- known equipment/clearance polygons;
- allowed orientation sets;
- anchors;
- access/path constraints.

The LLM may:
- choose candidate strategy;
- retrieve a donor Room Kit;
- interpret unusual requirement;
- explain why a repair was chosen.

But placement feasibility is deterministic.

### Candidate objective

After hard feasibility:

minimize:
- dead residual space;
- circulation interference;
- distance between functionally related items;
- number of special substitutions;
- departure from approved Room Kit;

maximize:
- clear usable route;
- flexibility;
- ergonomic/operational quality;
- reuse of standard arrangement.

---

# 10. Repair order becomes explicit and machine-enforceable

If Room Fit fails:

## Level 1 — zero architectural impact
1. move equipment;
2. rotate equipment;
3. switch between approved room-kit variants.

## Level 2 — low architectural impact
4. substitute equivalent equipment;
5. alter movable furniture configuration;
6. change local equipment grouping.

## Level 3 — medium impact
7. move/flip door within its valid wall envelope;
8. change door swing if legal and functionally acceptable;
9. adjust a noncritical internal partition within its module/envelope.

## Level 4 — high impact
10. move major wall;
11. alter room cluster;
12. modify structural/CSE/VCE state.

Every escalation requires proof that lower levels are infeasible.

This directly implements the user's influence hierarchy.

---

# 11. Equipment substitution should be a solver action, not an afterthought

Each required item should have an **equivalence class** where appropriate.

Example:

```
required functional item:
  refrigerator undercounter

candidates:
  model A: 600x600
  model B: 550x600
  model C: 600x550
```

If A does not fit but B satisfies:
- function;
- utilities;
- capacity;
- maintenance;
- procurement/project requirements;

then changing the product is cheaper than moving a wall.

This is exactly the type of repair an architect performs routinely.

The AI should rank it accordingly.

---

# 12. Clearance invalidation integrates naturally with the causal graph

If equipment moves:
- invalidate its AEE collisions;
- nearby internal-route graph;
- service connection;
- Room Fit;
- possibly door clearance.

Do **not** invalidate:
- entire building structure;
- unrelated floors;
- façade;
unless dependency edges say so.

If wall moves:
- invalidate every nearby AEE;
- room area;
- adjacent room fits;
- openings;
- routes;
- CSE;
- structure if applicable.

This produces the influence asymmetry the user described.

---

# 13. Room Kit should be a verified donor artifact

A Room Kit may include:

```yaml
room_kit_id:
room_type:
source:
  office_standard
  donor_project
  manufacturer
  generated_verified
geometry_envelope:
fixed_items:
flexible_items:
AEE_set:
door_envelope:
window_envelope:
stretch_axes:
locked_dimensions:
applicability:
verified_rules:
performance:
version:
```

Promotion requirements:
- fits its RRE;
- no hard clearance conflicts;
- regression fixture;
- source/provenance;
- validity envelope.

Room Kits then become procedural/architectural memory.

---

# 14. Public/service operational quality still requires room-external graph analysis

Room Fit handles **inside the room**.

FRG/Topologic handles:
- between rooms;
- public/service route separation;
- department relationships;
- building circulation.

Do not collapse these into one score.

Two-stage validation:

```
ROOM INTERNAL
 AEE / fit / access
        ↓
BUILDING EXTERNAL
 adjacency / path / flow / security
```

A perfectly arranged kitchen is still wrong if its goods route crosses the main visitor hall.

---

# 15. What can already be reused

## Hypar
Reuse as:
- UX benchmark;
- clearance semantics;
- room-kit/suggestion workflow reference;
- furnished-fit benchmark.

Direct runtime dependency for AC29:
**not required / not verified**.

## Finch
Reuse:
- adaptive-plan constraints;
- locked/extendable dimensions;
- donor-library matching.

## dRofus
Reuse:
- item/equipment SSOT;
- item occurrence;
- requirement linkage;
- AC29 object synchronization.

## qbiq
Reuse as:
- commercial quality benchmark;
- proof that custom standards/furniture/adjacency belong inside planning.

## OR-Tools / Shapely
Reuse:
- actual fit/placement solver mechanics.

---

# 16. What NOT to code

BLOCKED pending tests:

- generic AI furniture generator;
- custom geometric solver framework;
- generic clearance collision engine;
- generic equipment database;
- generic room-layout neural network;
- generic room-library search AI.

Custom justified:
- AEE normalization;
- AC29/dRofus item mapping;
- Room Kit schema;
- repair-level hierarchy;
- solver constraint compiler;
- Room Fit Coverage Signature.

---

# 17. Tests

## ROOM-FIT-01

One office / meeting room:
- target area already compliant;
- place required table/chairs/storage;
- door swing;
- circulation clearance.

Prove:
- AREA_PASS may still produce FIT_FAIL.

## ROOM-REPAIR-01

Create a room where one equipment item is too large.

Provide:
- one valid smaller equivalent product;
- one wall-move alternative.

Expected:
- substitution selected before wall move.

## CLEARANCE-INVALIDATION-01

Move one object.

Expected dirty scope:
- its AEE;
- room fit;
- nearby route/door checks.

No unrelated project-wide recalculation.

## ROOM-KIT-01

Take an approved donor room kit.

Adapt it to:
- +8% width;
- -5% depth.

Verify:
- locked dimensions preserved;
- extendable dimensions adapt;
- equipment/clearances remain valid;
- no uniform scaling.

---

# Strategic conclusion

The room should not be considered "designed" when its polygon and area are valid.

It becomes valid only when:

```
RRE area/geometry
        +
required activities/items
        +
AEE clearances
        +
door/access
        +
internal route
        +
utilities/environment
        ↓
ROOM FIT PASS
```

And when Room Fit fails, the system should first repair **inside the room** before escalating into high-impact architectural geometry.

This formalizes one of the most important differences between an architect and a naive floor-plan generator.
