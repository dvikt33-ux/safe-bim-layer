# Safe BIM coordination and dimensional-design standard

Status: **normative supplement for generated Archicad geometry**  
Version: **1.0-draft**  
Scope: Safe BIM Layer planners, generators, collectors and QA.

This supplement formalizes coordination failures observed in generated building
models. It extends `SAFE_BIM_ARCHICAD_MODELING_STANDARD.md`; it does not replace
the native-element and minimum-element-count rules.

## 1. Core principle: calculate relationships before drawing geometry

A generated element is not accepted merely because it is approximately located.
Before a dependent pass can proceed, the generator must prove the relationships
that make the element part of one coordinated BIM system.

Speed is never an acceptance criterion. A fast model that must be deleted is a
failed result. A slower pass with verified geometry, dimensions and rule
provenance is preferred.

Required order:

```text
trusted design / normative inputs
-> dimensional and topological calculation
-> BIM element creation
-> read-back / trusted geometry collection
-> blocker QA
-> only then the next dependent pass
```

If the calculation inputs or required rule values are missing, the result is
`NOT_VERIFIED` with `reasonCode = DATA_MISSING`; it is never guessed and never
promoted to `PASS`.

## 2. Roof-to-wall coverage

A roof system must reach every exterior wall line that it is intended to cover,
including the required design overhang where one exists.

Forbidden results include:

- a roof plane ending short of an exterior wall;
- a gable/transverse roof failing to cover the wall below;
- an unexplained strip of wall exposed because the roof footprint was calculated
  independently from the wall system.

The collector must compare actual roof reach/overhang with a trusted project or
verified normative rule. The minimum value is not hard-coded in the checker.

**BIM-QA-012 — ROOF_TO_WALL_COVERAGE** blocks `PASS_5_ROOFS` when any required
wall line is under-covered.

## 3. Wall junction continuity

Walls that are intended to meet must actually meet. Internal partitions,
load-bearing cross-walls and exterior walls are not independent line segments.

For every intended `T`, `L`, `X`, end or collinear junction, the trusted plan
must record the two wall identities and the intended junction type. Read-back or
geometry evidence must prove that the walls intersect/connect within the
verified tolerance.

A visible or geometric gap between an internal wall and the exterior wall is
`FAIL`, not a cosmetic defect.

**BIM-QA-013 — WALL_CONNECTIVITY** blocks the wall pass when an intended
junction is open or exceeds its verified maximum gap.

## 4. Vertical load-bearing continuity

A load-bearing wall on an upper storey must have a verified load path to an
intended supporting element below.

Default expectation:

```text
upper load-bearing Wall
-> lower load-bearing Wall
```

A Beam, Column, foundation or designed transfer structure may support the upper
wall only when that support is explicitly part of the structural intent. A
transfer/fallback arrangement may not be invented merely to make the geometry
pass.

The checker verifies geometric support ratio and horizontal offset against
trusted rule parameters. It does **not** claim to perform a structural-capacity
calculation; capacity and reinforcement remain separate engineering checks.

**BIM-QA-014 — VERTICAL_LOADBEARING_CONTINUITY** treats a floating or
unacceptably offset load-bearing wall as `FAIL`.

## 5. Wall/opening conflict

A wall or partition must never arrive in the host wall through the occupied
window/door opening zone.

Examples of automatic failure:

- an internal wall terminates in the middle of a Window;
- a partition divides a Door opening;
- the wall does not intersect the opening but violates the verified minimum
  clearance required from the opening edge.

The potential junction/opening pairs must be produced by a trusted collector or
planning contract, not selected after generation to hide conflicts.

**BIM-QA-015 — WALL_OPENING_CONFLICT** is a blocker for the opening pass.

## 6. Opening edge, corner and pier clearances

Window and Door placement must be dimensioned, not visually distributed.

The project/rule registry may require checks including:

- window to exterior corner;
- door to exterior corner;
- door to a perpendicular/adjacent wall;
- opening to adjacent wall;
- distance between neighboring openings;
- pier width between openings;
- jamb/return width.

Each measurement references a `ruleId` and named parameter. The checker contains
no default regulatory distance.

**BIM-QA-016 — OPENING_EDGE_CLEARANCE** fails when any measured clearance is
below its verified rule value.

## 7. Masonry modular coordination

Brick/block walls must use an explicit masonry coordination rule instead of
arbitrary dimensions.

The verified project rule defines, as applicable:

- `moduleStep`;
- `allowedResidues`;
- `moduleTolerance`;
- the dimensions/offsets to which that module applies.

This supports different masonry systems without embedding one brick size or one
mortar-joint convention into Safe BIM. `allowedResidues` can express half-module
or other explicitly approved offsets.

Checks may include:

- pier width;
- jamb offset;
- opening offset;
- distance between openings;
- wall return length;
- wall run length.

**BIM-QA-017 — MASONRY_MODULE_FIT** fails when a controlled dimension does not
fit the verified modular rule.

## 8. Rule provenance contract

Every numeric acceptance threshold used by BIM-QA-012..017 must resolve to a
`VERIFIED` Rule Registry entry.

A normative entry must include:

```text
id
status = VERIFIED
sourceKind = NORMATIVE
document
edition
clause
verifiedAt
parameters
```

A project/reference rule must include:

```text
id
status = VERIFIED
sourceKind = PROJECT | REFERENCE
basis
approved = true
verifiedAt
parameters
```

No value may be inserted merely because it is common practice, remembered from
another project, or convenient for the generator.

Missing/unverified provenance yields `NOT_VERIFIED / DATA_MISSING`.

## 9. Offline checker and live boundary

`bim_coordination_qa.py` implements an offline fail-closed checker for
BIM-QA-012..017. Its evidence contract requires complete scoped inventories plus
trusted geometry measurements.

The checker can prove its calculation logic using synthetic/reference fixtures,
but that does not prove a real PLN. Until a live collector captures the required
relationships from Archicad, these rules remain `liveValidationState =
NOT_VERIFIED`.

The main generator must therefore not treat an offline unit-test PASS as a
production-model PASS.
