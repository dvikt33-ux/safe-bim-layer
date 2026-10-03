# Archicad Capability Registry

This registry records only capabilities that were actually exercised against Archicad/Tapir and received a positive read-back and/or visual verification. A capability is not promoted to `VERIFIED` from source-code inspection alone.

## Status vocabulary

- `VERIFIED` — live Archicad test passed and the result was read back and/or visually confirmed.
- `PARTIAL` — API path works, but geometry/quality is not yet acceptable as a canonical modeling solution.
- `REJECTED` — technically possible, but rejected as a modeling pattern for Safe BIM.
- `KNOWN_LIMITATION` — schema/API limitation confirmed from source and/or runtime.

## Verified capabilities

### Native Door library part creation and placement
Status: `VERIFIED`

- SafeBIM library-part creation path can produce a real Archicad Door library part.
- `SB_English_Panel_Door_v1` was created, found by Archicad, placed in a Wall host and read back as `Door`.
- Door smoke test completed successfully.

Canonical rule: use native `Door` for doors; do not substitute Morph geometry.

### Window glass material
Status: `VERIFIED`

- GSM window geometry can use the surface/material `Стекло - Прозрачное Быстрое` instead of `MATERIAL 0`.
- The resulting glass was visually confirmed transparent in Archicad.

### Solid Element Operations for slab target/cutters
Status: `VERIFIED`

- Slab target + slab operators can be created.
- `CreateSolidElementLinks` with `Subtraction` succeeds.
- `GetSolidElementLinks` reads the target/operator relationships back.
- Collision test before SEO reported body collisions; collision test after SEO returned none.
- Operators can live on a dedicated cutter layer.

Canonical use: use SEO as a controlled boolean operation with explicit operators and read-back. SEO link existence alone is not sufficient proof of final geometry.

### Complex Profile creation and Beam use
Status: `VERIFIED`

- Custom profile creation through `CreateProfiles` works.
- A custom 139 x 243 mm profile was successfully assigned to native Archicad Beams.
- Profile Beam read-back preserved `profileId`, `isFlipped = false`, and `profileAngle = 0` in the successful beam test.

### Horizontally curved profile Beam
Status: `VERIFIED`

- A profile Beam can be converted to `HorizontallyCurved`.
- Required working combination: `ModifyBeams` with both `beamShape = "HorizontallyCurved"` and a non-zero `arcAngle`.
- `beamShape` alone did not bend the beam and is not sufficient.
- Both positive and negative 90-degree curved examples were created successfully.

### 90-degree Beam corner cleanup / 45+45 joint
Status: `VERIFIED`

- Two straight profile Beams sharing one corner point can form a clean 90-degree corner with standard Beam connection behavior.
- The visual test confirmed the joint works without an added diagonal corner object.

Canonical rule: test native Beam cleanup before inventing extra cutter geometry at a joint.

## Partial capabilities

### Ornamental step-cutter profile
Status: `PARTIAL`

- The complex profile can reproduce the intended stepped/curved section closely enough to prove the method.
- Later variants showed faceting and orientation problems.
- The exact smooth canonical profile is not yet frozen.

Next requirement: replace polygonal approximation with true arcs where supported, or a sufficiently dense validated approximation; preserve correct orientation through straight and curved Beam paths.

### Porch generation by SEO
Status: `PARTIAL`

- SEO mechanics are proven.
- Final three-sided porch geometry and decorative nosing/cutter behavior are not yet canonical.

## Rejected modeling patterns

### Fragmenting walls to simulate openings
Status: `REJECTED`

Do not create many short Wall segments around window/door voids when a native hosted `Window` or `Door` can be used.

### Morph windows
Status: `REJECTED`

Morph frames/glazing are not an acceptable substitute for native/library `Window` elements in normal building modeling.

### Stepped stacks of walls to fake gables
Status: `REJECTED`

Do not approximate a gable by many horizontal Wall strips. Use a normal Wall and trim/crop it to a validated Roof/Shell/SEO result.

### Unvalidated overlapping roof planes
Status: `REJECTED`

Do not advance to rafters while roof intersections contain holes, overlaps or unresolved valleys/ridges.

### Rafters generated independently from unverified roof geometry
Status: `REJECTED`

Rafter geometry must be derived from the final accepted roof planes and their real ridge/eave/valley geometry.

## Known limitations

### CreateSlabs schema
Status: `KNOWN_LIMITATION`

`CreateSlabs` does not accept `buildingMaterialId` in the current Safe BIM/Tapir schema. The supported create fields are limited to the actual command schema (including level, thickness, reference plane, polygon, holes and floor). Material/structure changes require a supported later operation or a favorite-based workflow.

## Promotion rule

A new solution is added to this registry only after:

1. Minimal isolated smoke test.
2. Successful command execution.
3. Read-back of the created/modified element.
4. Geometry/visual check when the API cannot prove the result by data alone.
5. No hidden fallback to Morph or fragmented geometry if a native BIM tool exists.
6. Reusable script/test is saved in the project together with the evidence needed to reproduce the result.
