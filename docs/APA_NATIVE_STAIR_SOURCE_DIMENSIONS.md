# Source-compatible native Stair dimensions

This package continues PR80 using the existing BIM Graph, SceneWriter and
SQLite journal. It does not install an APX or implement another executor.

`compatible_native_step_counts` evaluates the explicitly captured native
configured limits. `prepare_source_dimension_example` verifies the exported
Favourite hash, current Favourite availability, exact native story elevations,
the complete requested parameters and a straight walking line. It compiles
one ordinary `CreateStairs` graph. It never silently substitutes another
count, rise, going or width. Execute this graph only through the existing
scoped SceneWriter, after current identity, retained signatures, free-space
and journal checks.

The existing 3.3 m / 20-rise Stair has 165 mm rises. Requesting 350 mm going
gives 2R+G = 680 mm, above its captured native maximum of 650 mm. Its actual
320 mm going is preserved. An explicitly different test specimen uses
22 rises of 150 mm, 350 mm going, 1 m width and a 7.7 m walking line. These
are test parameters; native configured limits are not a normative verdict.

## Actual native result

One new native Stair was created in the existing authorized test project.
Independent built-in properties read going 350 mm, rise 150 mm, width 1 m
and walking-line length 7.7 m. Actual StairStructure BREP has 22 horizontal
levels: 20 regular successive front-edge pitches measure 350 mm and all
21 measured level differences are 150 mm. The final structural top transition
is recorded separately, without treating it as the default going.

SaveProject and OpenProject passed through the existing journal. A separate
read-only pass confirmed all 255 current inventory signatures, including the
previous 145 geometry/material/story signatures. Native collision query
against retained physical elements returned no pairs. The new specimen is
detached: it does not prove a new floor connection or engineering suitability.

## Inventory limitation and replay

The native operation created one Stair, 45 listed hierarchical members and
64 additional bodyless Objects. `audit_stair_inventory` distinguishes explicit
native object.owner references into the listed members from unresolved
references. Ten Objects reference native parents omitted from the generic
dump/hierarchy enumeration. Their parent types are readable, but ancestry to
this Stair is not proved; GetConnectedElements returned empty lists.

The inventory acceptance stays NOT_VERIFIED. Bodylessness does not prove
annotation status, harmlessness or ownership. No Objects were deleted and no
Create was repeated. The initial Create's journal entry remains
PARTIAL_OR_UNKNOWN_OUTCOME because its original strict inventory callback
stopped on the extra Objects. Later factual dimension/persistence evidence
does not rewrite that history or authorize retrying the Create.

The detached exact-SDK Stair solver/edit contract remains BLOCKED. A11.S03
stays PARTIAL; engineering acceptance stays NOT_VERIFIED. Next: resolve
specialized ancestry for the ten Objects before full inventory acceptance,
and continue native SinglePlane Roof contour/slope work independently.
