# Safe BIM Generation Pipeline v2

Purpose: convert architectural intent into high-quality Archicad models through staged deterministic generation rather than one-shot element placement.

This document is implementation-oriented. It turns the research in `ARCHITECTURAL_MODEL_QUALITY_RESEARCH.md` into a practical staged compiler/runtime design.

---

# 0. Pipeline overview

The next-generation workflow should be split into explicit model passes:

```text
PASS 0  Project + datum preflight
PASS 1  Architectural skeleton
PASS 2  Primary building elements
PASS 3  Interfaces and hosted elements
PASS 4  Connection/refinement pass
PASS 5  Architectural expression pass
PASS 6  Collision/gap/geometry QA
PASS 7  Visual/material finalization
PASS 8  Final read-back + deliverable validation
```

The central idea is simple:

> Each pass may depend on the verified outputs of earlier passes, but it may not independently reinterpret their geometry.

The model therefore evolves from one canonical architectural graph instead of from unrelated coordinate snippets.

---

# 1. Pass 0 — Project, coordinate and datum preflight

## Inputs

- selected Archicad project copy;
- pinned Tapir schema/provider version;
- project zero / sea-level datum if relevant;
- story table;
- unit system;
- local project coordinate system;
- StyleKit / Favorites availability;
- project quality profile.

## Checks

1. Confirm project identity.
2. Read Tapir version and compare with pinned schema.
3. Read stories and elevations.
4. Resolve Project Zero and site datum.
5. Confirm target story IDs and elevations.
6. Resolve required Favorites/Building Materials/Composites/Profiles where the schema supports them.
7. Check that no modal/busy state prevents writes.
8. Establish execution state file and unique run identity.

## Output

`ProjectContext`

```python
ProjectContext(
    project_id,
    tapir_version,
    stories,
    project_zero,
    coordinate_frame,
    style_kit,
    tolerance_profile,
    run_id,
)
```

No geometry is written in Pass 0.

---

# 2. Pass 1 — Architectural skeleton

This is the most important stage.

The skeleton is not “temporary walls”. It is the canonical topology from which later geometry is derived.

## 2.1 Site skeleton

- site boundary;
- terrain data extent;
- building origin and rotation;
- roads/paths centerlines;
- important external datum lines.

## 2.2 Story skeleton

For every story:

- exact elevation;
- floor-to-floor height;
- intended slab reference plane;
- ceiling/roof relationship;
- primary façade datum levels.

## 2.3 Grid skeleton

Represent structural and architectural grids explicitly.

```python
GridLine(
    id,
    axis,
    coordinate,
    role,
)
```

Columns, façade bays and repeated interior modules should derive from grids, not from repeated raw arithmetic in multiple scripts.

## 2.4 Space graph

```python
SpaceNode(
    id,
    function,
    story,
    target_area,
    polygon_id,
)

AdjacencyEdge(
    space_a,
    space_b,
    relation,
    preferred_connection,
)
```

Relations may include:

- shared wall;
- open connection;
- door connection;
- vertical connection;
- no adjacency;
- exterior boundary.

## 2.5 Canonical boundary graph

The boundary graph owns every wall-bearing edge.

```python
Vertex
Edge
Loop
Face/Space
```

Two adjacent rooms share one boundary edge. They do not create two walls.

## 2.6 Skeleton quality gate

Before continuing:

- all required room loops close;
- no self-intersections;
- no duplicate edges;
- no orphan vertices;
- adjacency graph is symmetric;
- shared boundaries agree;
- external perimeter is one or more valid closed loops;
- story assignment is complete;
- minimum geometric tolerances pass.

If the skeleton fails, do not create Archicad elements.

---

# 3. Pass 2 — Primary building elements

This pass creates only large, semantically primary geometry.

Recommended order:

1. terrain/site Mesh;
2. primary slabs;
3. exterior walls;
4. interior structural/major walls;
5. columns and beams;
6. primary roofs/shells;
7. stairs/major vertical circulation when supported;
8. curtain walls where structurally part of the envelope.

Do not create decorative Morphs or façade ornaments here.

## 3.1 Slabs

Slab polygons should derive from canonical floor plates.

Avoid drawing independent slab contours that almost match the walls.

Each slab record should retain:

- source loop IDs;
- reference plane;
- thickness;
- story;
- StyleKit/Favorite reference;
- intended wall relationship.

## 3.2 Walls

Walls compile from canonical edges.

A `WallPlan` should contain:

```python
WallPlan(
    edge_id,
    story,
    bottom,
    top_or_toplink,
    reference_line_rule,
    flip,
    favorite_or_structure,
    junction_intent_start,
    junction_intent_end,
)
```

## 3.3 Columns

Columns come from grid intersections or declared local supports.

Do not generate columns visually by counting façade spacing independently from the structural grid.

## 3.4 Roofs

Roof geometry comes from `RoofGraph`, never from unrelated roof-face commands.

## 3.5 Primary-element post-write gate

After every write:

- read back GUID;
- verify semantic element type;
- normalize and verify geometry;
- persist receipt;
- update spatial index.

After the pass:

- detect duplicate elements;
- validate primary intersections;
- validate all declared structural/architectural supports;
- stop before openings if the envelope is invalid.

---

# 4. Pass 3 — Interfaces and hosted elements

This is where the model becomes coordination-grade rather than massing-grade.

## 4.1 Doors and windows

Openings use wall-local positions derived from façade/space logic.

Never store a window only as global XY.

```python
OpeningPlan(
    host_edge_id,
    host_guid,
    normalized_position,
    sill,
    width,
    height,
    favorite,
    alignment_group,
)
```

## 4.2 Vertical openings

For stair voids, shafts and atria:

- derive cut polygons from the same vertical circulation graph;
- create actual Opening elements where supported, or use verified boolean operations;
- never leave “visual holes” formed by coincident slabs.

## 4.3 Roof/wall interfaces

Use `TrimElements` where the roof/shell relationship is intended.

Workflow:

1. create roof;
2. verify roof geometry;
3. identify supporting/trimmed wall set;
4. create trim relationship;
5. read back trim relationship if supported;
6. verify wall top envelope.

## 4.4 Solid Element Operations

Use `CreateSolidElementLinks` for intentional boolean relationships where native cleanup does not solve the condition.

Examples:

- terrain cut by retaining/foundation geometry;
- special void operator cutting a construction element;
- complex roof/volume subtraction where semantically appropriate.

Store target/operator/operation as part of the execution receipt.

Do not use SEO as a universal cleanup tool. If a wall reference line is wrong, fix the topology instead.

---

# 5. Pass 4 — Connection and refinement pass

This is a dedicated pass, not scattered repairs.

## 5.1 Wall junction resolver

For every graph node where walls meet:

1. collect incident wall edges;
2. confirm shared canonical vertex;
3. confirm reference-line geometry;
4. classify T/L/X/multi-way junction;
5. resolve material/junction-order requirements;
6. check visible body continuity after read-back.

## 5.2 Roof resolver

- verify ridge/valley coincidence;
- verify face elevation at shared edges;
- trim supporting walls;
- identify overhang gaps;
- reject sliver roof faces.

## 5.3 Slab/wall resolver

Since slab-slab intersections do not automatically clean up, continuous floor systems should ideally use coherent slab regions rather than overlapping fragments.

Check:

- perimeter consistency;
- intentional offsets;
- no duplicate coplanar slabs;
- no thin accidental strips between adjacent slab polygons.

## 5.4 Terrain/building resolver

Terrain does not participate in automatic cleanup like ordinary construction junctions.

The site interface must be explicit:

- finished grade;
- foundation cut/fill intent;
- retaining edges;
- road/terrain relationship;
- building platform.

---

# 6. Pass 5 — Architectural expression

Only after the geometry is structurally/topologically sound should the system add the architectural image.

## 6.1 Mass hierarchy

The design spec must identify:

- dominant volume;
- secondary volumes;
- entrance volume;
- vertical accent;
- roof hierarchy;
- service volumes.

## 6.2 Façade grammar

Create a dedicated `FacadeSystem`:

```python
FacadeSystem(
    facade_id,
    baseline_edges,
    bay_grid,
    story_datums,
    opening_family_rules,
    corner_rules,
    entrance_exceptions,
    material_zones,
)
```

Then derive openings from the system.

A façade should pass alignment checks:

- repeated bays align;
- sill/head lines align where intended;
- corner windows do not collide with corner junctions;
- openings do not cross wall joints unless explicitly designed;
- entrance hierarchy is visibly distinct.

## 6.3 Roof image

Roof slopes and ridge heights should come from a small coherent family. Avoid random per-face slopes unless the style explicitly calls for them.

## 6.4 Secondary details

Only now add:

- parapets;
- cornices;
- canopies;
- façade frames;
- buttresses;
- special Morph features;
- site walls;
- landscape objects.

Each detail must have a declared host/parent element.

---

# 7. Pass 6 — Geometry and coordination QA

This pass should run until stable or until it produces an issue list that requires human/design input.

## 7.1 Cycle A — duplicate detection

Fingerprint normalized geometry + semantic type + story.

Reject run-owned duplicates.

## 7.2 Cycle B — collision scan

Broad phase:

- AABB spatial index.

Narrow phase:

- type-specific tests.

Classify every intersection through the collision-intent matrix.

Unknown intersections are errors.

## 7.3 Cycle C — gap scan

Check:

- room loop closure;
- wall node continuity;
- slab perimeter continuity;
- roof adjacency;
- wall/roof interfaces;
- hosted-element containment.

## 7.4 Cycle D — topology scan

Morphs:

- edge-face incidence;
- manifoldness;
- orientation;
- self-intersections;
- degeneracies.

Polygons:

- self-intersection;
- holes;
- winding;
- minimum area.

## 7.5 Cycle E — architectural alignment scan

Check:

- façade bay alignment;
- story datum alignment;
- grid alignment;
- column/wall relationships;
- repeated family consistency;
- roof symmetry/asymmetry intent.

## 7.6 Cycle F — repair policy

Automatic repair is allowed only for deterministic, local, unambiguous cases.

Examples allowed:

- normalize polygon closure;
- reverse winding;
- snap two references already declared to be the same canonical vertex;
- remove duplicate closing vertex;
- sort/canonicalize equivalent read-back geometry.

Examples requiring regeneration or human/design decision:

- two unrelated rooms overlap;
- a roof cannot cover its host walls without changing the design;
- a door conflicts with structural support;
- two independent systems occupy the same volume;
- survey terrain is incomplete.

Never silently move major architectural elements simply to make a clash disappear.

---

# 8. Pass 7 — Visual/material finalization

## 8.1 Apply StyleKit consistently

Use project Favorites and verified material/composite/profile attributes.

Finalization checks:

- exterior materials coherent;
- roofs use intended roof material;
- internal/external wall families correct;
- doors/windows use the selected family set;
- columns/beams use intended construction material;
- terrain/site materials are distinct from building materials.

## 8.2 Detail density check

Avoid two opposite failures:

- under-modeling: visually empty generic boxes;
- over-modeling: thousands of decorative objects with no architectural purpose.

The detail budget should be tied to the requested output scale/use.

## 8.3 Visual QA views

Recommended fixed view set:

1. overall axonometric;
2. north/south/east/west exterior views;
3. one entrance perspective;
4. roof/top view;
5. each floor plan;
6. at least two strategic sections.

A future computer-vision QA loop can compare these views against design criteria. This requires a verified view/screenshot/export workflow and should not be assumed from Tapir until implemented.

---

# 9. Pass 8 — Final verification and model-ready gate

A build can end in one of these states:

```text
MODEL_READY
MODEL_READY_WITH_WARNINGS
DESIGN_INPUT_REQUIRED
RECONCILIATION_REQUIRED
RUNTIME_FAILURE
```

`MODEL_READY` requires:

- no unresolved write outcomes;
- no undeclared collisions;
- no boundary gaps;
- all owned elements read-back verified;
- all mandatory interfaces present;
- style/material resolution complete;
- topology checks pass;
- output issue list empty for mandatory severity.

---

# 10. Multi-file implementation architecture

Recommended source layout:

```text
safe_bim/
  spec/
    project_spec.py
    style_kit.py
    quality_profile.py

  topology/
    canonical_geometry.py
    polygon_ops.py
    space_graph.py
    boundary_graph.py
    roof_graph.py

  planning/
    skeleton_planner.py
    element_planner.py
    opening_planner.py
    site_planner.py
    facade_planner.py

  quality/
    spatial_index.py
    collision_rules.py
    gap_rules.py
    morph_validator.py
    duplicate_detector.py
    normalized_compare.py
    issue_report.py

  archicad/
    tapir_client.py
    mutation_gateway.py
    element_compiler.py
    connection_compiler.py
    readback.py

  runtime/
    execution_plan.py
    receipts.py
    reconcile.py
    stage_runner.py
```

The existing `safe_bim_layer.py` can gradually become a compatibility façade over this structure rather than continuing to absorb every responsibility.

---

# 11. Suggested public high-level API

The planner/LLM should call semantic operations, not Tapir primitives.

Example:

```python
project = SafeProject(spec)

project.compile_skeleton()
project.validate_skeleton()

project.build_primary_elements()
project.resolve_interfaces()
project.build_architectural_expression()

report = project.run_quality_cycles()

if report.can_finalize:
    project.finalize_style()
    result = project.verify_model_ready()
```

For a building definition:

```python
BuildingIntent(
    footprint=...,
    stories=...,
    grids=...,
    spaces=...,
    facade_systems=...,
    roof_intent=...,
    style_kit="modern_brick_01",
    target_reliability="LOD300_COORDINATION",
)
```

The LLM should never have to produce low-level JSON for each wall face or Morph polygon unless it is explicitly authoring a freeform design object.

---

# 12. Iterative design cycle

The generator should run a structured loop:

```text
DESIGN INTENT
    ↓
SKELETON COMPILE
    ↓
SKELETON QA
    ├─ fail -> repair design graph
    ↓ pass
PRIMARY ELEMENT BUILD
    ↓
GEOMETRY QA
    ├─ fail -> regenerate affected dependency subtree
    ↓ pass
INTERFACE BUILD
    ↓
CLASH/GAP QA
    ├─ fail -> resolve declared connection
    ↓ pass
ARCHITECTURAL EXPRESSION
    ↓
ALIGNMENT + VISUAL QA
    ├─ fail -> adjust façade/style rules
    ↓ pass
FINALIZATION
    ↓
MODEL_READY
```

Important: regeneration scope should be the smallest dependency subtree possible, not the whole project.

---

# 13. Dependency graph for partial regeneration

Every element plan stores dependencies.

Example:

```text
Story 1 datum
  -> exterior footprint
      -> wall W-12
          -> windows W-12-01..05
          -> roof trim relation
      -> slab S-01
  -> grid A/1
      -> column C-A1
```

If exterior footprint changes, invalidate the derived walls/slab/openings. If only a window family changes, do not recreate the wall.

This is required for scalable iterative architecture.

---

# 14. Quality profile configuration

Project-specific tolerances should be data, not hardcoded constants.

Example:

```yaml
quality_profile:
  position_snap_m: 0.001
  polygon_epsilon_m: 0.001
  angle_epsilon_rad: 0.0001
  duplicate_position_m: 0.002
  min_face_area_m2: 0.0001
  min_edge_length_m: 0.002
  collision_mode: strict_typed
  require_morph_manifold: true
  require_closed_room_loops: true
  require_verified_roof_wall_trim: true
```

These are starting configuration values, not universal architectural standards. They should be tuned by project scale and source-data accuracy.

---

# 15. Implementation sequence

## Milestone A — Canonical skeleton

Deliver:

- vertex registry;
- shared boundary graph;
- polygon normalization;
- room/perimeter closure validation;
- geometry fingerprints.

This alone should dramatically reduce gaps/duplicates.

## Milestone B — Normalized read-back

Deliver:

- polygon cyclic/reversal equivalence;
- float tolerance profiles;
- semantic comparison;
- execution receipts and reconciliation.

## Milestone C — Typed collisions

Deliver:

- AABB index;
- collision-intent matrix;
- duplicates;
- host containment;
- wall/slab/column checks.

## Milestone D — Connections

Deliver:

- `TrimElements` wrapper + verification;
- `CreateSolidElementLinks` wrapper + verification;
- roof-wall resolver;
- terrain/foundation interface model.

## Milestone E — RoofGraph + Morph validator

Deliver:

- ridge/valley/eave topology;
- manifold Morph checks;
- self-intersection checks;
- volume/orientation validation.

## Milestone F — StyleKit + façade grammar

Deliver:

- Favorites/material resolution;
- façade bays/alignment groups;
- controlled opening families;
- material/family consistency checks.

## Milestone G — Full staged build

Deliver:

- skeleton script;
- primary elements script;
- refinement script;
- finalization script;
- stage state/resume;
- final model-ready report.

---

# 16. The four code pieces requested for practical use

For each future generated project, output should be split into four runnable artifacts.

## `01_skeleton.py`

Creates or records:

- project datum;
- story/grid context;
- canonical site/building coordinates;
- optional terrain skeleton;
- no decorative geometry.

Must finish with `SKELETON_PASS`.

## `02_primary_elements.py`

Creates:

- slabs;
- walls;
- columns/beams;
- primary roofs;
- major site geometry.

Must finish with `PRIMARY_PASS`.

## `03_refinement.py`

Creates:

- doors/windows/openings;
- roof trims;
- solid-element links;
- secondary geometry;
- stairs/railings/façade systems where supported.

Runs clash/gap checks. Must finish with `REFINEMENT_PASS`.

## `04_finalization.py`

Creates/applies:

- final Favorites/materials where still required;
- architectural details;
- landscape details;
- visual coherence checks;
- final model report.

Must finish with `MODEL_READY` or a precise issue list.

Each file must be idempotent through shared execution state.

---

# 17. Non-negotiable rules

1. No raw LLM-to-Tapir mutation path.
2. No independent coordinates for geometry that should share topology.
3. No “fix by adding another element on top”.
4. No automatic retry after uncertain dispatch without reconciliation.
5. No Morph solid without topology validation.
6. No roof model declared complete before wall/roof interfaces are resolved.
7. No façade declared final before alignment-family checks.
8. No `DONE` state based only on successful API responses.
9. No hidden invented survey/site data.
10. No broad silent geometry movement just to eliminate clashes.

---

# 18. Expected effect

Moving to this staged architecture should improve three things simultaneously:

- **technical quality**: fewer duplicates, gaps, collisions and invalid freeform solids;
- **architectural quality**: stronger hierarchy, façade rhythm, coherent roofs/materials and repeatable families;
- **operational reliability**: partial regeneration, deterministic verification and safe resume after errors.

The main conceptual change is to stop treating the Archicad model as the source of geometry truth during generation. The source of truth is the verified canonical building graph; Archicad is the semantic BIM target that receives and then confirms the compiled result.
