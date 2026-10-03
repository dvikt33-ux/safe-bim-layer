# Safe BIM Archicad Modeling Standard

Status: **normative for generated Archicad geometry**  
Version: **1.1-draft**  
Scope: Safe BIM Layer, local planners, code generators, reviewers, and automated QA.

## 1. Purpose

This standard defines what Safe BIM is allowed to call a valid BIM result in Archicad.
It exists to prevent geometrically plausible but semantically wrong models: fragmented walls,
Morph substitutes for native openings, stepped gables, overlapping roofs, disconnected rafters,
and other constructions that may look approximately correct while violating normal Archicad
modeling practice.

A result MUST NOT receive `PASS` merely because the visible shape is recognizable. `PASS` requires
correct BIM element types, correct host relationships, coherent construction logic, minimal
semantically correct element count, and successful read-back / QA for the completed pass.

## 2. Core law: preserve BIM semantics and minimize element count

One construction element MUST remain one normal BIM element while its construction logic is
continuous and a native Archicad element plus native operations can represent the intended result.

The generator MUST NOT replace one coherent construction with many smaller elements merely because
that decomposition is easier to script.

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
story, ownership, or reviewed API limitation that requires separate elements. The generator MUST
record the reason when intentional fragmentation is introduced.

### 2.1 Mandatory decision order: operations before fragmentation

For every semantic construction role, the generator MUST evaluate the following order and stop at
the first semantically correct solution:

1. **one native BIM element**;
2. **one native BIM element plus normal Archicad operations**, including hosted openings,
   Trim Elements to Roof/Shell, Solid Element Operations / boolean subtraction or intersection,
   polygon editing/subtraction, trim/extend, or another native relationship;
3. **Complex Profile or GDL/GSM**, when that is the semantically correct representation;
4. **the smallest necessary multi-element native construction**;
5. `Morph` only under the separate last-resort Morph policy.

A transport/API limitation does **not** automatically authorize a worse BIM model. If the correct
operation cannot be executed through the current transport, the normal result is
`BLOCKED_BY_TRANSPORT` / `NOT_VERIFIED`. A fragmented fallback requires an explicit reviewed
exception; silent degradation is forbidden.

Examples:

- **Gable wall:** one full Wall -> validated Roof -> Trim to Roof/Shell (or semantically equivalent
  native relationship). A staircase of short Walls is `FAIL`.
- **Window / door:** one host Wall + native hosted Window/Door. Building masonry from short Walls
  around an empty rectangle is `FAIL`.
- **Porch / platform outline:** start from the minimum semantically correct Slab/other native
  element set and obtain recesses/cut-outs through native polygon edits or SEO where that expresses
  the intended construction. Do not approximate one coherent platform with a pile of small slabs
  or blocks just because separate primitives are easier to generate.
- **Roof-controlled geometry:** create the coherent roof system first, then perform native trim /
  intersection operations. Do not encode the roof shape into unrelated wall fragments.
- **Repeated retries:** reconciliation updates/reuses the intended element; it does not add another
  element beside it.

The trusted planning/reference contract SHOULD record, for every generated semantic role,
`maxElementCount` and the selected strategy (`NATIVE_ELEMENT`, `HOSTED_NATIVE`,
`NATIVE_OPERATION`, `COMPLEX_PROFILE`, `GDL`, or `MINIMAL_MULTI_ELEMENT`).

### 2.2 Forbidden substitutions

The following are automatic blocker failures unless an explicit allowed exception is recorded and
reviewed:

- splitting one continuous facade into many short Walls merely to draw openings or a gable shape;
- creating a window or door opening by surrounding a void with several Walls when native Window /
  Door hosting is available;
- using Morph as a Window or Door substitute;
- using Morph as a substitute for a standard Wall, Slab, Roof, Beam, Column, Window, or Door when the
  corresponding native tool can represent the intended element;
- manually approximating a roof-shaped wall top with stacked or stepped Wall fragments;
- representing one coherent slab/platform/porch role as many fragments when native edit/SEO
  operations can produce the same semantically correct result;
- choosing element fragmentation solely for visual convenience, script simplicity, or transport
  convenience.

## 3. Morph policy

`Morph` is a last-resort element type.

Morph MAY be used only after the generator or reviewer has established that all of the following are
inapplicable or insufficient:

1. the corresponding native Archicad tool;
2. native edit / trim / SEO operations;
3. Complex Profile;
4. a GDL / GSM library part;
5. another semantically correct BIM construction.

Every generated Morph MUST carry an explicit machine-readable reason. `Morph` used as a Window or
Door is always `FAIL`.

## 4. Wall and opening rules

### 4.1 Walls

- A straight uninterrupted exterior side MUST be one Wall unless a real reviewed construction reason
  requires a split.
- Wall fragmentation count MUST be audited before the wall pass can pass.
- A gable wall MUST begin as a normal wall element; the roof-controlled top shape is produced only
  after the roof geometry exists and is validated.
- The generator MUST NOT construct the gable outline by horizontal wall strips or by a staircase of
  small wall pieces.
- If a roof trim can produce the intended top, adding extra Wall elements instead is a blocker
  violation of `BIM-QA-011`.

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
- the intended roof-controlled wall top cannot be demonstrated by geometry/read-back evidence;
- a correct one-Wall-plus-trim solution was known but the generator created multiple Walls instead.

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
- element types match their construction meaning;
- each controlled semantic role uses no more elements than the trusted minimal representation
  unless a reviewed exception exists.

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
6. Each pass MUST carry a complete minimum-element-count / operation-strategy contract for the
   controlled elements in that scope.

## 10. Automatic blocker QA

The following checks are mandatory before final `PASS`.

### BIM-QA-001 — WALL_FRAGMENTATION

Exterior wall systems MUST NOT consist of excessive short fragments without recorded construction
reason. A fragmentation detector checks segment count, segment lengths, continuity, and the presence
of openings that should have been native hosted elements.

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

Every controlled element MUST match its independently declared story/floor assignment. When the
intent declares an absolute base-elevation check, that elevation MUST also match read-back evidence.

### BIM-QA-009 — DUPLICATES

Duplicate generated BIM elements caused by retries, reconciliation, or repeated execution: **0**.

### BIM-QA-010 — PASS_DEPENDENCY

A pass MUST NOT be reported as `PASS` if any blocker rule required by that pass is failing,
`NOT_VERIFIED`, or unresolved.

### BIM-QA-011 — MINIMUM_ELEMENT_COUNT

For every controlled semantic role, the actual number of generated elements MUST NOT exceed the
trusted `maxElementCount` for the selected semantically correct strategy unless an explicit reviewed
fragmentation exception exists.

This rule is intentionally independent from `BIM-QA-009`: two elements can have different IDs and
still be a modeling error if one native element plus an operation should have been used.

Examples of automatic failure:

- a gable represented by several Walls when one Wall + roof trim is the approved strategy;
- a window represented by wall fragments instead of a hosted Window;
- one porch/platform role represented by many small Slabs when one/minimal Slab set + native
  subtraction/edit operations is the approved strategy;
- fragmentation selected only because it is easier for the script.

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
- three or four correctly placed rafters;
- at least one operation-derived form (for example wall trimmed to roof or slab polygon/SEO cut)
  whose read-back is retained as the canonical minimal-element representation.

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
- property traces used by the Safe BIM identity layer;
- semantic role -> `maxElementCount` -> strategy/operation evidence.

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
   - proper wall-to-roof result produced by native trim/relationship, not wall fragmentation;
   - two or more real Beam rafters derived from that roof;
5. record element-economy intent for the fragment (`maxElementCount`, strategy and operation);
6. run the blocker QA rules on this fragment;
7. only after the fragment passes, generalize the construction recipe to the rest of the house.

No propagation from the pilot fragment is allowed while its roof, opening type, wall top, rafter
alignment, story assignment, or minimum-element-count audit is unresolved.

## 13. Exception policy

A fragmentation exception is valid only when all of the following are present:

- category is one of `construction`, `geometry`, `renovation`, `material`, `story`, `ownership`,
  `api_limitation`;
- a concrete reason is recorded;
- a reviewer is recorded;
- `approved: true`;
- for `api_limitation`, `fallbackReviewed: true` is additionally required.

`opening`, `gable`, `visual`, `script_simplification`, `convenience`, or similar reasons are not
valid exceptions.

## 14. Review rule

When a generated model looks acceptable but violates this standard, the model is wrong.

A reviewer or agent MUST prefer:

- correct native BIM semantics over visual approximation;
- one/minimal coherent element set plus proper operations over accidental fragmentation;
- read-back evidence over assumptions;
- staged verified construction over one-shot scripts;
- explicit `FAIL` / `NOT_VERIFIED` over a false `PASS`.
