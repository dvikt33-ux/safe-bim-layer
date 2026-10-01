# Architectural Model Quality Research for Safe BIM

Status: research baseline for the next generation of Safe BIM.
Scope: Archicad 29 + Tapir 1.5.9 style workflows, with emphasis on architectural-grade geometry, clean connections, collision avoidance, gap prevention, repeatability, and visual quality.

## Executive conclusion

The current weak results are not primarily a problem of “insufficiently complicated geometry”. They come from the modeling architecture: elements are generated too independently, too many coordinates are authored directly, topology is not canonicalized before writes, intended intersections are not distinguished from errors, and there is not yet a complete refinement/finalization loop.

The target should not be “LLM emits hundreds of Tapir calls”. The target should be:

1. LLM produces a constrained architectural intent/specification.
2. A deterministic compiler builds a canonical building graph.
3. Geometry is derived from shared topology, not independently guessed coordinates.
4. Archicad-native elements are preferred over Morphs.
5. Connections are authored explicitly using Archicad semantics: priority-based junctions, trims, and solid element operations where appropriate.
6. Every stage has pre-write and post-write quality gates.
7. The model is refined in cycles: skeleton -> primary elements -> interfaces -> detail -> visual/material pass -> final validation.
8. The system stores durable element identity and can resume without duplicate writes.

The practical target is a model whose geometry can be trusted at roughly an LOD 300 / coordination-oriented LOD 350-like level for the elements the system claims to own: size, shape, location and orientation must be measurable from the model, and important interfaces with adjacent systems must be represented. This is a target model-quality philosophy, not a claim of formal BIMForum certification.

## Research method

The research was performed as multiple cycles, each testing a different hypothesis.

### Cycle 1 — Why our current generated models look weak

Observed failure modes in our tests:

- disconnected or visually weak junctions;
- walls that merely collide rather than join correctly;
- roof/wall gaps or overshoots;
- repeated/duplicate elements after partial failures;
- flat or generic composition with little architectural hierarchy;
- overly literal read-back comparison causing false failures (for example polygon vertex order);
- terrain, roads, roofs and secondary geometry created as unrelated parts rather than one coordinated system;
- Morph geometry created without a full topology-quality contract;
- no final model-check cycle before declaring success.

Root cause: geometry is treated as a list of element-placement commands rather than as a shared topological model.

### Cycle 2 — Native Archicad connection semantics

Graphisoft’s own documentation is explicit that correct model intersections are not equivalent to simple geometric overlap.

Key findings:

- Automatic priority-based junctions depend on Building Material intersection priorities.
- Wall-wall cleanup requires reference-line intersection; simple physical collision is not enough.
- Equal-priority walls may require Junction Order.
- Slab-slab collision does not automatically clean up.
- Mesh is not supported by normal automatic element cleanup.
- Roof/Shell trimming is associative and is intended for precise roof/wall and related connections.
- Solid Element Operations provide associative target/operator geometry modification.

Implication for Safe BIM: “clash-free” cannot mean “no elements intersect”. Many valid BIM connections intentionally intersect. We need a typed connection matrix that distinguishes intended junctions, hosted relationships, boolean relationships and true clashes.

### Cycle 3 — Archicad model checking

Archicad includes Collision Detection and Physical Model Quality checks. Graphisoft describes Collision Detection as checking physical intersection between element groups, while Physical Model Quality focuses on geometric/modeling anomalies and can use configurable tolerances.

Implication: Safe BIM should run an internal quality gate before writing, then make its output compatible with Archicad’s own model-check concepts after writing. A future automated integration should consume model-check results if Tapir/API coverage permits; until then, the generator should at least produce deterministic issue reports that mirror these checks.

### Cycle 4 — Morph and freeform geometry robustness

Graphisoft states that a Morph is non-solid if an edge is not joined by exactly two faces. Visually plausible geometry can therefore still be invalid as a solid.

CGAL’s mesh-repair documentation independently identifies the same family of geometric defects that procedural generation must guard against: inconsistent orientation, degeneracies, gaps, missing data, non-manifold features and self-intersections.

Implication: Morph generation requires a topology validator, not just a vertex/polygon serializer.

### Cycle 5 — Terrain representation

Graphisoft describes Mesh as a surface defined from characteristic point elevations with interpolation between them. Tapir examples show a single Mesh with polygonCoordinates plus many internal sublines, each carrying XYZ values.

Implication: survey/topography should be one coordinated Mesh whenever possible, rather than many separate Morph hills or stacked slabs. Morph should be reserved for rock outcrops, retaining geometry, sculptural terrain details or shapes that cannot be represented naturally as Mesh.

### Cycle 6 — BIM development level

The BIMForum LOD framework is useful not as a visual-detail checklist but as a reliability contract. LOD 300 emphasizes specific measurable quantity/size/shape/location/orientation. LOD 350 adds modeled interfaces needed for coordination.

Implication: a model that merely “looks like a building” is not architectural-grade. Safe BIM must explicitly declare what geometry is reliable and must represent important interfaces, not only silhouettes.

### Cycle 7 — Tapir capability mapping

Tapir currently exposes more useful coordination operations than our early Safe BIM layer used.

Verified in the Tapir repository:

- `CreateSolidElementLinks` with Subtraction, SubtractionUpwards, SubtractionDownwards, Intersection and Addition;
- `GetSolidElementLinks` for read-back of target/operator relationships;
- `TrimElements` for roof/shell trimming relationships;
- Roof creation with single-plane `pivotLine + angle`;
- Morph creation from explicit vertices/polygons;
- Mesh creation with XYZ polygon points and sublines;
- Wall creation supports architectural settings including structure type, Building Material, Composite and Favorites in current Tapir code paths.

Implication: refinement should use associative Archicad connections instead of geometrically faking every cut with separate primitives.

---

# 1. The core architectural rule: shared topology first

## 1.1 Canonical vertex registry

Every major building corner should exist once in a canonical registry.

Bad:

```text
Wall A end = (12.0000, 5.0000)
Wall B start = (12.0037, 5.0002)
Slab corner = (11.998, 5.001)
```

Visually these may look close, but they are three different topological points.

Target:

```text
V_104 = (12.000, 5.000)
Wall A = V_021 -> V_104
Wall B = V_104 -> V_209
Slab polygon includes V_104
```

Coordinates should be generated from topology and a project tolerance, not independently by each element generator.

## 1.2 Canonical edges

Shared room boundaries should map to shared edge objects. An edge owns:

- start/end vertex IDs;
- inside/outside side;
- wall semantic type;
- story range;
- thickness/reference-line rule;
- adjacent spaces;
- opening intervals;
- connection intent at both ends.

Walls are compiled from edges. Rooms do not each generate their own coincident walls.

This eliminates a major source of duplicate walls and micro-gaps.

## 1.3 Closed-loop invariants

Before any wall or slab write:

- each room/perimeter loop must be closed;
- no zero-length edge;
- no duplicate consecutive point;
- no self-intersection;
- winding must be normalized;
- holes must be strictly inside the containing polygon;
- shared edges must reference the same canonical vertices.

If a loop fails, the stage stops before Archicad is modified.

---

# 2. Use native BIM elements first

Element preference order:

1. Wall / Slab / Roof / Shell / Column / Beam / Opening / Door / Window / Stair / Railing / Curtain Wall when the geometry belongs to that semantic class and Tapir coverage is verified.
2. Object/library part when a reusable parametric object already represents the item.
3. Morph only for exceptional freeform geometry.

Why:

- Native elements participate in Archicad’s intersection and documentation logic.
- Hosted Doors/Windows preserve host semantics.
- Roof/Shell relationships can be associative.
- Building Materials and Favorites provide consistent appearance and construction semantics.
- Morphs require extra topology checking and are easier to make non-solid.

Morph is not a universal geometry escape hatch.

---

# 3. Reference lines are part of geometry correctness

For walls, the generator must choose a project-wide convention such as:

- exterior walls: reference line on core/exterior datum;
- internal partitions: centerline or core reference depending on project standard;
- façade alignment always derived from one consistent datum.

Graphisoft notes that wall cleanup requires reference-line intersection, so end-point placement must solve reference-line topology, not merely visible face intersections.

Recommendation:

```text
WallSpec
  canonical_edge
  reference_line_rule
  flip_direction
  structure/favorite
  height/toplink
  connection_start
  connection_end
```

The wall body then derives from the edge plus the reference-line rule.

---

# 4. Building Materials and Favorites are part of model quality

A beautiful architectural model should not be generated with random tool defaults.

Introduce a `StyleKit` / `ConstructionKit` contract:

```yaml
wall_external: favorite "SB_EXT_WALL_300"
wall_internal: favorite "SB_PARTITION_120"
slab_typical: favorite "SB_SLAB_TYPICAL"
roof_primary: favorite "SB_ROOF_PRIMARY"
window_family: favorite "SB_WINDOW_A"
door_family: favorite "SB_DOOR_A"
column_primary: favorite "SB_COLUMN_RC"
terrain: favorite "SB_SITE_MESH"
```

Where the pinned Tapir schema confirms it, use `favoriteName`, Building Material, Composite or Profile identifiers.

The model compiler should override only the small set of parameters intentionally controlled by the design (length, position, story, height, opening size, etc.).

This gives:

- consistent construction layers;
- consistent intersection priorities;
- coherent surfaces/materials;
- predictable documentation appearance;
- easier global style changes.

---

# 5. Typed collision model

A raw statement “elements overlap” is not enough.

Create a collision-intent matrix.

Example:

| Pair | Default interpretation | Required validation |
| --- | --- | --- |
| Wall-Wall | intended junction | reference lines meet; junction topology valid |
| Wall-Slab | often intended interface | floor/story and core relationship valid |
| Column-Slab | often intended penetration/support | position is declared by structural grid |
| Door/Window-Wall | required hosted overlap | opening remains within host bounds |
| Wall-Roof | intended trim relation | TrimElements relationship or verified geometric termination |
| Roof-Roof | intended join or forbidden clash | ridge/valley topology matches roof graph |
| Slab-Slab | suspicious by default | no duplicate/coplanar overlap unless explicitly declared |
| Morph-Morph | suspicious | allowed only for declared assembly or boolean design |
| Mesh-Building | site interface | grade/foundation intent required |
| Same semantic element duplicated | error | identity/fingerprint duplicate gate |

## Broad-phase

Before exact checks, use axis-aligned bounding boxes and a spatial index (R-tree or sweep-and-prune) to avoid O(n^2) testing on large models.

## Narrow-phase

Exact checks should be type-specific. Examples:

- segment/segment intersection for reference lines;
- polygon overlap for slabs;
- vertical interval overlap for walls/columns;
- host-local interval checks for openings;
- roof-plane vs wall-top checks;
- triangle/face self-intersection for Morph bodies.

## Touching vs collision

Graphisoft’s collision documentation distinguishes physical collision from simple touching. Safe BIM should preserve the same distinction:

- `SEPARATED`
- `TOUCHING`
- `INTENDED_OVERLAP`
- `BOOLEAN_RELATION`
- `INVALID_COLLISION`

---

# 6. Gap detection

Collision detection does not find holes. Gap detection needs separate rules.

## Room boundary gaps

For every room/zone loop:

- degree at each boundary vertex should normally be 2;
- loop must close within project tolerance;
- no dangling edge;
- no double-owned interior boundary;
- adjacency must be symmetrical.

## Wall corner gaps

Compare canonical reference-line nodes. If two walls are declared connected, both must share the same vertex ID. Do not merely compare their floating-point coordinates after creation.

## Slab/perimeter gaps

The slab footprint should be generated from the same footprint graph as the walls, with an intentional offset policy. Do not redraw the slab polygon independently.

## Roof gaps

Build a roof graph first:

- eaves;
- ridges;
- valleys;
- hips;
- roof faces;
- supporting wall relationships.

Then compile roof faces. Adjacent faces share exact canonical ridge/valley edges.

Walls under roofs should be connected by a verified `TrimElements` relationship where available, not stopped at a guessed average height.

---

# 7. Roof generation must be topology-driven

A roof is not “two polygons with an angle”.

Create a `RoofGraph`:

```text
RoofGraph
  footprint
  eave_edges
  ridge_edges
  valley_edges
  face polygons
  slope per face
  face adjacency
  drainage direction
  host wall set
```

Validation before write:

- each roof face polygon is simple;
- shared roof edges coincide exactly;
- no unowned internal edge;
- ridge heights agree from both faces;
- faces do not self-intersect;
- overhang is derived consistently from wall footprint;
- all intended supporting walls are covered;
- roof does not leave sliver faces below minimum project tolerance.

After write:

- read back roof geometry;
- execute `TrimElements` for supporting walls/shell relations where appropriate;
- read back trim relationships if supported.

---

# 8. Morph quality contract

A Morph declared `Solid` must pass all of these before writing:

1. Every referenced vertex exists.
2. Each polygon has at least three distinct vertices.
3. Polygon area is above epsilon.
4. No consecutive duplicate vertex IDs.
5. No duplicate faces.
6. No zero-length edges.
7. For a closed solid, every undirected edge is used by exactly two faces.
8. Face orientation is globally consistent.
9. Normals point consistently outward after orientation normalization.
10. No non-adjacent face self-intersections.
11. No isolated vertex or edge.
12. Volume is finite and above epsilon.

These rules directly follow the class of defects highlighted by Graphisoft Morph solidity checks and standard polygon-mesh repair practice.

For complex Morphs, triangulate internally for validation even if Archicad receives polygon faces.

---

# 9. Terrain quality contract

Preferred representation: one Mesh for one continuous terrain surface.

Input model:

```text
TerrainSpec
  boundary
  contour polylines with absolute elevation
  spot heights
  breaklines
  exclusion holes
  project datum
```

Pipeline:

1. validate survey coordinate system and datum;
2. remove duplicated/near-duplicated survey points;
3. snap contour endpoints where they are logically continuous;
4. reject self-intersecting contour polylines;
5. preserve breaklines;
6. interpolate only inside data-supported regions;
7. generate one Mesh with internal XYZ lines/points;
8. compare read-back bounds/elevation range against source data.

Do not invent heights when source data is missing. Missing terrain data should produce an uncertainty region, not an authoritative surface.

---

# 10. Openings quality contract

Doors and windows should never be placed by global XYZ guesses after walls exist.

Store each opening as host-local coordinates:

```text
OpeningSpec
  host_edge_id
  t_along_host
  sill
  width
  height
  family/favorite
  reveal anchor
```

Validation:

- host exists and is Wall;
- opening horizontal interval lies within usable wall span;
- minimum edge clearance is configurable;
- openings on the same host do not overlap unless explicitly intended;
- vertical interval fits wall/trimmed envelope;
- stacked-story openings can align to a façade grid.

This makes openings stable if the building shifts globally.

---

# 11. Architectural visual quality is a constraint system

Do not add detail randomly. Build visual hierarchy.

## Massing hierarchy

Every design should declare:

- primary volume;
- secondary wings/volumes;
- vertical accents;
- entrance hierarchy;
- roof hierarchy;
- service/back-of-house masses.

## Façade grammar

Use a façade grid:

- bay widths;
- floor datums;
- base/middle/top zones;
- opening families;
- corner rules;
- entrance exceptions;
- alignment groups.

Windows should be generated from bays and alignment groups, not independent offsets.

## Repetition with controlled variation

A strong model usually uses a small vocabulary repeatedly:

- 2–4 window families;
- a small number of wall assemblies;
- consistent roof slopes;
- aligned sill/head levels;
- consistent structural grids;
- deliberate special elements at entrances/corners.

Randomized variation should be bounded by an explicit grammar.

## Detail budget

Geometry detail should correspond to the target use. Decorative geometry that does not improve coordination, documentation or intended appearance should not be generated during the structural passes.

---

# 12. Model reliability target: LOD 300/350-like behavior

For an element to be accepted as `MODEL_READY` by Safe BIM:

- its size, shape, location and orientation are explicit and measurable;
- its semantic element type is correct where a native Archicad element exists;
- major interfaces are represented;
- it has passed type-specific collision/gap checks;
- its connections are intentional rather than accidental overlaps;
- its read-back matches the normalized contract;
- known uncertainty is recorded rather than hidden.

For an LOD 350-like coordination target, interface conditions also matter: jambs/openings, supports, roof/wall trims, adjacent slab/wall boundaries, and similar relationships must be modeled or explicitly declared out of scope.

---

# 13. Read-back normalization

A verifier must compare geometry semantically, not byte-for-byte.

Normalize before comparison:

## Polygons

Treat as equivalent when they differ only by:

- cyclic starting vertex;
- clockwise vs counterclockwise orientation when orientation is not semantically significant;
- repeated closing point;
- sub-tolerance coordinate noise.

## Sets of GUID relationships

Sort/canonicalize before comparison.

## Floating point

Use project-configurable tolerances by quantity class:

- position;
- angle;
- thickness;
- elevation.

Do not use a single universal epsilon for every property.

## Geometry fingerprints

Create normalized fingerprints from canonical geometry. These support duplicate detection and idempotent recovery after uncertain outcomes.

---

# 14. Idempotency and failure recovery

Never rerun a monolithic build blindly.

Every physical write step needs:

```text
step_id
operation
normalized input hash
preexisting element fingerprint set
returned GUID
post-write read-back
verified geometry fingerprint
status
```

Statuses:

- `PREPARED`
- `DISPATCHED_UNKNOWN`
- `VERIFIED_PASS`
- `FAILED_BEFORE_WRITE`
- `RECONCILIATION_REQUIRED`

On restart:

1. if verified receipt exists, skip;
2. if dispatch outcome was uncertain, reconcile using GUID/inventory/fingerprint;
3. never create a replacement until absence is proven;
4. never adopt a foreign coincident element merely because it matches geometry unless the execution identity proves ownership.

This directly addresses duplicate Mesh/slab issues seen in manual experiments.

---

# 15. Recommended internal data model

```text
ProjectSpec
  SiteSpec
  StoryTable
  GridSystem[]
  BuildingSpec[]
  StyleKit
  QualityProfile

BuildingSpec
  BuildingFrame
  SpaceGraph
  BoundaryGraph
  StructuralGraph
  RoofGraph
  FacadeSystems[]
  VerticalCirculation[]

CanonicalGeometry
  VertexRegistry
  EdgeRegistry
  PolygonRegistry
  SpatialIndex

ExecutionPlan
  Stage[]
    Step[]
      dependencies
      operation
      semantic_intent
      expected geometry
      connection intent
      verification contract
```

The LLM should operate mostly above `CanonicalGeometry`. Deterministic code owns canonical geometry and Tapir payloads.

---

# 16. Safe BIM should distinguish design errors from API errors

Suggested issue classes:

- `TOPOLOGY_ERROR`
- `SELF_INTERSECTION`
- `DUPLICATE_ELEMENT`
- `UNDECLARED_COLLISION`
- `BOUNDARY_GAP`
- `HOST_CONTAINMENT_ERROR`
- `ROOF_INTERFACE_ERROR`
- `DATUM_ERROR`
- `MORPH_NON_MANIFOLD`
- `READBACK_MISMATCH`
- `API_SCHEMA_MISMATCH`
- `ARCHICAD_RUNTIME_ERROR`
- `UNCERTAIN_WRITE_OUTCOME`

This allows the system to repair design-state issues before attempting another physical write.

---

# 17. Acceptance criteria for an architectural-grade generated model

A generated building is not `DONE` until all mandatory gates pass.

## Geometry

- no self-intersecting room/slab/roof polygons;
- no zero-length geometry;
- no duplicate elements owned by the run;
- no undeclared collisions;
- all declared adjacency edges close;
- wall reference-line graph is connected as intended;
- hosted openings stay inside hosts;
- solid Morphs are manifold and consistently oriented.

## BIM semantics

- native Archicad tool used where appropriate;
- story/home-story assignment verified;
- materials/favorites resolved;
- roof/wall and other critical connections represented;
- generated element IDs/metadata trace back to design intent.

## Visual architecture

- openings align to façade grid unless intentionally exceptional;
- primary/secondary mass hierarchy is visible;
- roof hierarchy is coherent;
- materials are drawn from the StyleKit;
- repetitive elements use controlled families;
- no accidental micro-slivers or razor-thin geometry.

## Coordination

- collision matrix passes;
- required clearances pass where specified by project input;
- interfaces required by target model reliability level are represented.

## Execution integrity

- every owned element has a verified receipt;
- no unresolved uncertain writes;
- state can resume without duplication.

---

# 18. High-priority implementation recommendations

1. Build `canonical_geometry.py`: vertex/edge/polygon registry, snapping, winding, self-intersection and polygon normalization.
2. Build `building_graph.py`: spaces, shared boundaries, wall edges, adjacency.
3. Build `quality_geometry.py`: collision broad-phase, gap checks, duplicate fingerprints.
4. Build `morph_validator.py`: manifold/orientation/self-intersection checks.
5. Build `roof_graph.py`: deterministic eave/ridge/valley topology.
6. Replace one-shot `create_room` thinking with staged execution.
7. Add normalized read-back comparison.
8. Add style/favorite resolution from project attributes.
9. Add Tapir connection layer for `TrimElements` and `CreateSolidElementLinks` with read-back verification.
10. Add final issue report and explicit `MODEL_READY` gate.

---

# Sources

## Graphisoft Archicad 29

- Model Element Connections: https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-269.htm
- Intersecting Elements That Don’t Clean Up: https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-274.htm
- Best Practices for Intersections: https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-275.htm
- Fine-Tune Intersections: https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-276.htm
- Physical Model Quality Check: https://help.graphisoft.com/AC/29/INT/_AC29_Help/092_ModelCheck/092_ModelCheck-2.htm
- Model Check: https://help.graphisoft.com/AC/29/INT/_AC29_Help/092_ModelCheck/092_ModelCheck-1.htm
- Intersection Priority: https://help.graphisoft.com/AC/29/INT/_AC29_Help/025_Attributes/025_Attributes-23.htm
- Morph solidity: https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-257.htm
- Meshes: https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-130.htm
- Favorites Palette: https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-63.htm
- Stories: https://help.graphisoft.com/AC/29/INT/_AC29_Help/050_ViewsVB/050_ViewsVB-5.htm

## BIM / interoperability

- BIMForum LOD Specification resource: https://bimforum.org/resource/lod-level-of-development-lod-specification/
- buildingSMART IFC Validation Service: https://validate.buildingsmart.org/

## Computational geometry

- CGAL Polygon Mesh Repair: https://doc.cgal.org/latest/PMP_Mesh_repair/index.html
- CGAL Polygon Mesh Processing: https://doc.cgal.org/latest/Polygon_mesh_processing/

## Tapir Archicad Automation

- Solid element operations and trims: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/archicad-addon/Sources/SolidElementOperationCommands.cpp
- Mesh example: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/archicad-addon/Examples/create_mesh.py
- Roof read-back/create example: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/archicad-addon/Examples/roof_details.py
- Morph body example: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/archicad-addon/Examples/create_modify_delete_morph.py
- Wall creation fields/Favorites/material support: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/grasshopper-plugin/TapirGrasshopperPlugin/Components/ElementsComponents/CreateWallsComponent.cs
