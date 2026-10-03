# Safe BIM Archicad Modeling Standard

This document defines the minimum modeling quality required before a generated result may be called PASS.

## Native BIM first

Use the native Archicad element that represents the building object whenever it exists:

- Wall -> `Wall`
- Window -> `Window`
- Door -> `Door`
- Slab -> `Slab`
- Roof -> `Roof`
- Beam / rafter / ridge / plate -> `Beam`
- Column / post -> `Column`

Morph, fragmented Walls and ad-hoc surrogate geometry are fallback methods, not defaults.

## Wall continuity

A straight wall run remains one Wall unless there is a real BIM reason to split it.

Window and door openings must not be modeled by breaking a facade into sill/head/jamb Wall fragments when hosted native openings are available.

## Gables and wall-to-roof geometry

Do not build gables as stacks of short Walls.

Canonical sequence:

1. Create the normal full Wall.
2. Create and validate the Roof/Shell geometry.
3. Trim/crop the Wall to the accepted roof geometry using a supported Archicad relation or a verified SEO fallback.
4. Read back and visually inspect the result.

## Roof quality gate

A roof system must pass before rafters are generated.

Required checks:

- no unintended gaps between roof parts;
- no accidental overlapping volumes;
- ridges terminate correctly;
- valleys/intersections are geometrically resolved;
- eaves follow the intended footprint;
- roof planes reach the intended walls/gables;
- wall tops do not protrude through the accepted roof.

## Rafters

Rafters are generated from the accepted roof geometry, not from an independent guessed pitch model.

For each rafter family, the generator must derive or verify:

- eave/wall-plate point;
- ridge/hip/valley point;
- real roof slope;
- member orientation;
- member length;
- relationship to roof plane.

## Windows and doors

Normal building windows and doors must be native or library-part hosted openings.

Morph windows are a FAIL for normal building modeling.

Smoke test requirements for a reusable Window/Door solution:

- element type read-back is correct;
- host is a Wall;
- size is correct;
- placement/offset is correct;
- library-part identity is correct when a custom part is used;
- visual material/glass check when relevant.

## One capability at a time

Do not validate a whole house with one giant script.

Canonical progression:

1. Walls.
2. Native Window/Door insertion.
3. Slabs.
4. One simple roof.
5. Wall-to-roof trim.
6. One rafter family.
7. Complex roof intersection.
8. Porch/secondary systems.
9. Integrated house.

A failed phase blocks later phases.

## PASS criteria

PASS requires all of the following:

- command executed successfully;
- created/modified element can be read back;
- requested-vs-actual critical values match;
- host/connectivity is correct;
- duplicate count is zero;
- visual geometry is acceptable when read-back alone cannot prove the shape;
- the solution does not violate a rejected modeling pattern in `ARCHICAD_CAPABILITY_REGISTRY.md`.

## Repository rule

Every verified reusable capability must be committed with:

- minimal reproducible smoke test;
- expected result;
- read-back assertions;
- cleanup or disposable-project assumptions;
- registry entry marking it VERIFIED only after live confirmation.

Failed experiments may be kept as diagnostics, but they must not be represented as canonical implementations.
