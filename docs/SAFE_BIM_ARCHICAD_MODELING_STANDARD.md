# Safe BIM Archicad Modeling Standard

Status: **normative for generated Archicad geometry**  
Version: **1.0-draft**  
Scope: Safe BIM Layer, local planners, code generators, reviewers, and automated QA.

## 1. Purpose

This standard defines what Safe BIM is allowed to call a valid BIM result in Archicad.
It exists to prevent geometrically plausible but semantically wrong models: fragmented walls,
Morph substitutes for native openings, stepped gables, overlapping roofs, disconnected rafters,
and other constructions that may look approximately correct while violating normal Archicad
modeling practice.

A result MUST NOT receive `PASS` merely because the visible shape is recognizable. `PASS` requires
correct BIM element types, correct host relationships, coherent construction logic, and successful
read-back / QA for the completed pass.

## 2. Core law: use the native BIM element until there is a proven reason not to

One construction element SHOULD remain one normal BIM element while its construction logic is
continuous.

Default mapping:

| Construction meaning | Required Archicad element |
| --- | --- |
| straight continuous wall side | `Wall` |
| window | `Window`, hosted by a wall |
| door | `Door`, hosted by a wall |
| floor / structural plate | `Slab` |
| roof plane | `Roof` |
| rafter / timber member | `Beam` |
| post / vertical structural member | `Column` |

Fragmentation is allowed only when there is a real construction, geometry, renovation, material,
story, ownership, or API limitation that requires separate elements. The generator MUST record the
reason when intentional fragmentation is introduced.

### 2.1 Forbidden substitutions

The following are automatic blocker failures unless an explicit exception is recorded and reviewed:

- splitting one continuous facade into many short Walls merely to draw openings or a gable shape;
- creating a window or door opening by surrounding a void with several Walls when native Window /
  Door hosting is available;
- using Morph as a Window or Door substitute;
- using Morph as a substitute for a standard Wall, Slab, Roof, Beam, Column, Window, or Door when the
  corresponding native tool can represent the intended element;
- manually approximating a roof-shaped wall top with stacked or stepped Wall fragments.

## 3. Morph policy

`Morph` is a last-resort element type.

Morph MAY be used only after the generator or reviewer has established that all of the following are
inapplicable or insufficient:

1. the corresponding native Archicad tool;
2. Complex Profile;
3. a GDL / GSM library part;
4. normal roof / shell trimming or an appropriate solid-element relationship;
5. another semantically correct BIM construction.

Every generated Morph MUST carry an explicit machine-readable reason. `Morph` used as a Window or
Door is always `FAIL`.

## 4. Wall and opening rules

### 4.1 Walls

- A straight uninterrupted exterior side SHOULD be one Wall.
- Wall fragmentation count MUST be audited before the wall pass can pass.
- A gable wall MUST begin as a normal wall element; the roof-controlled top shape is produced only
  after the roof geometry exists and is validated.
- The generator MUST NOT construct the gable outline by horizontal wall strips or by a staircase of
  small wall pieces.

### 4.2 Windows and doors

- A window MUST be a native/library `Window` hosted by its intended Wall.
- A door MUST be a native/library `Door` hosted by its intended Wall.
- Openings MUST NOT be simulated by splitting masonry around them if the host opening tool is
  available.
- Host GUID / relationship MUST be verified by read-back where the available transport exposes it.
- `Morph windows == 0` and `Morph doors == 0` are blocker acceptance criteria.

## 5. Roof modeling rules

Roof geometry is a system, not a collection of approximately positioned planes.

For a multi-volume pitched roof, the required order is:

```text
main building volume
-> main roof

projection / risalit 1
-> transverse pitched roof

projection / risalit 2
-> transverse pitched roof

then
-> intersections
-> valleys
-> ridges
-> gap/intersection audit
-> only then structural rafters
```

Before the roof pass can receive `PASS`:

- roof planes MUST form the intended continuous weather envelope;
- unintended volumetric overlaps MUST be absent;
- unintended gaps between adjacent roof planes MUST be absent;
- valleys and ridges MUST be geometrically coherent;
- roof parts MUST NOT simply pass through each other as unresolved independent solids.

If a roof gap or unresolved penetration remains, the rafter pass is blocked.

## 6. Wall-to-roof relationship

Walls MUST NOT be manually reshaped to imitate the roof profile before the roof is validated.

Required logical sequence:

```text
full wall
-> validated roof system
-> normal Archicad roof/shell trim or another semantically correct native relationship
-> read-back / visual QA of the resulting wall top
```

The exact API mechanism may vary by transport capability. The invariant is the BIM result: one
normal wall controlled by a proper roof relationship, not dozens of wall fragments.

The pass fails when:

- a gable wall protrudes through the roof;
- the wall top is produced by stepped fragments;
- the intended roof-controlled wall top cannot be demonstrated by geometry/read-back evidence.

## 7. Rafter rules

Rafters are generated **from the already accepted roof geometry**. Roof geometry MUST NOT be derived
from independently calculated rafters in the normal building-generation workflow.

For every generated rafter the system SHOULD determine and retain:

- bearing / eaves point;
- ridge, valley, hip, or other upper target point;
- actual roof-plane slope;
- member length;
- cross-section orientation.

Rafter acceptance criteria:

- the rafter axis lies in the intended roof-plane system;
- the upper end reaches the correct ridge / valley / hip target;
- the lower end reaches the intended wall plate / bearing line;
- no rafter unintentionally penetrates through the roof envelope;
- rafter spacing/orientation is derived from the accepted roof, not from an unrelated approximation.

If these conditions cannot be checked, the rafter pass is `NOT_VERIFIED`, never `PASS`.

## 8. Story and system coherence

Stories, walls, slabs, openings, roofs, and structure are one BIM system.

The generator MUST NOT treat them as unrelated independent geometry batches. Each pass MUST use
read-back from previous accepted passes where the next element depends on earlier geometry.

At minimum the final audit checks:

- elements belong to intended stories;
- hosted elements still have their intended hosts;
- roof-controlled geometry remains consistent after restart/read-back;
- no duplicate elements were introduced by retry or reconciliation;
- element types match their construction meaning.

## 9. Mandatory staged generation protocol

A whole building MUST NOT be created by one unchecked monolithic script.

Default sequence:

```text
PASS 1  stories
PASS 2  walls
AUDIT 2

PASS 3  windows / doors
AUDIT 3

PASS 4  slabs
AUDIT 4

PASS 5  roofs
AUDIT 5

PASS 6  wall-to-roof relationships / trimming
AUDIT 6

PASS 7  rafters / roof structure
AUDIT 7

PASS 8  porch and secondary assemblies
AUDIT 8

FINAL BIM AUDIT
```

Rules:

1. A later pass MUST NOT start while the preceding required audit is failing.
2. An audit result may be `PASS`, `FAIL`, `NOT_VERIFIED`, or `BLOCKED_BY_TRANSPORT`.
3. `NOT_VERIFIED` and `BLOCKED_BY_TRANSPORT` do not authorize progression where the unverified
   condition is a dependency of the next pass.
4. Each pass SHOULD be restartable and idempotent; retries MUST NOT create duplicates.
5. Read-back evidence is preferred over planner assumptions.

## 10. Automatic blocker QA

The following checks are mandatory before final `PASS`.

### BIM-QA-001 — WALL_FRAGMENTATION

Exterior wall systems MUST NOT consist of excessive short fragments without recorded construction
reason. A fragmentation detector SHOULD compare segment count, segment lengths, continuity, and the
presence of openings that could have been native hosted elements.

### BIM-QA-002 — WINDOW_NATIVE_TYPE

All intended windows MUST be Archicad Window elements. `Morph` used as window: **0**.

### BIM-QA-003 — DOOR_NATIVE_TYPE

All intended doors MUST be Archicad Door elements. `Morph` used as door: **0**.

### BIM-QA-004 — ROOF_COLLISIONS

Unintended roof-solid penetrations / unresolved overlapping roof planes: **0**.

### BIM-QA-005 — ROOF_GAPS

Unintended open gaps in the intended roof envelope: **0**.

### BIM-QA-006 — WALL_TOPS

Exterior gable / roof-adjacent walls MUST NOT protrude above the accepted roof envelope and MUST NOT
be represented by stepped wall fragments.

### BIM-QA-007 — RAFTER_ALIGNMENT

Generated rafters MUST agree with accepted roof planes and intended bearing/ridge/valley geometry.

### BIM-QA-008 — STORY_ASSIGNMENT

Elements MUST belong to the intended story / elevation system.

### BIM-QA-009 — DUPLICATES

Duplicate generated BIM elements caused by retries, reconciliation, or repeated execution: **0**.

### BIM-QA-010 — PASS_DEPENDENCY

A pass MUST NOT be reported as `PASS` if any blocker rule required by that pass is failing,
`NOT_VERIFIED`, or unresolved.

## 11. Reference-model training protocol

Safe BIM SHOULD learn Archicad construction patterns from a small manually built reference fragment,
not only from API documentation or planner assumptions.

Minimum reference fragment:

- two connected walls and a corner;
- one native Window;
- one native Door where relevant;
- second story relationship;
- one gable wall;
- two correctly related roof planes;
- correct wall-to-roof result;
- three or four correctly placed rafters.

Required process:

```text
MANUAL CORRECT MODEL
-> API / Tapir read-back
-> sanitized canonical fixture
-> Safe BIM canonical pattern
-> generator output
-> automatic comparison against canonical fixture
```

Useful read-back evidence includes, where the available transport supports it:

- element type and GUID;
- host relationships;
- `GetDetailsOfElements`;
- connected elements;
- 3D bounding boxes;
- roof details;
- wall details;
- Beam details;
- Window / Door details;
- story / elevation data;
- property traces used by the Safe BIM identity layer.

The reference model is evidence, not a license to blindly copy machine-specific GUIDs or project
identifiers into production fixtures.

## 12. Current-house recovery protocol

For the currently failed house iteration, do **not** continue repairing the roof on top of the bad
construction stack.

Required recovery sequence:

1. preserve the existing good V2 walls;
2. remove only the generated bad additions: roof geometry, Morph windows, rafters, and any slab /
   porch pieces proven wrong;
3. choose one V2 gable / small building fragment;
4. rebuild only that fragment with:
   - one normal continuous wall;
   - one real library/native Window;
   - one correct small pitched roof system;
   - proper wall-to-roof result;
   - two or more real Beam rafters derived from that roof;
5. run the blocker QA rules on this fragment;
6. only after the fragment passes, generalize the construction recipe to the rest of the house.

No propagation from the pilot fragment is allowed while its roof, opening type, wall top, or rafter
alignment is unresolved.

## 13. Review rule

When a generated model looks acceptable but violates this standard, the model is wrong.

A reviewer or agent MUST prefer:

- correct native BIM semantics over visual approximation;
- fewer coherent elements over accidental fragmentation;
- read-back evidence over assumptions;
- staged verified construction over one-shot scripts;
- explicit `FAIL` / `NOT_VERIFIED` over a false `PASS`.
