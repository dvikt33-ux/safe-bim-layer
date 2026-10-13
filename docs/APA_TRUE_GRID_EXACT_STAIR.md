# True Grid and exact native Stair continuation

This package extends the PR75 runtime source overlay and the existing SceneWriter.
The compiled candidate is not installed. BUILD_PASS and OFFLINE_PASS are distinct
from LIVE_PASS and SOURCE_DIMENSION_PASS. No accepted PLN or Stair is edited.

## Native Grid

Four SDK commands use API_ObjectID with APIVarId_GridElement (`GREL`):
GetNativeGridDefaultsV1, GetNativeGridElementsV1, CreateNativeGridElementsV1 and
ModifyNativeGridElementsV1. Generic variation is explicitly rejected. Creation
starts from real Grid defaults and pins the loaded library index, scalar parameter
names and types. The reader exposes the actual type/variation/GUID, native parameter
descriptions, placement, floor and A/B dimensions. Native position edits preserve
the root GUID, floor, loaded library and parameters; an expected-position baseline
prevents stale edits. No lines, labels, generic Object tool or Morph substitute.

`archicad_native_spatial_tools.prepare_axis` binds existing semantic axes to real
source-qualified length/label parameters and emits an existing BIM Graph operation.
Unverified role mappings, guessed parameter names and changed defaults are denied.
`archicad_project_accelerator.apply_native_axis_grid` delegates to the existing
SceneWriter/SQLite journal. Completed creates reuse their original GUID; unknown
outcomes never retry. Source coordinate edits return the updated semantic axis and
native binding. Explicit existing bindings support reuse after an edit. Native
parameter acceptance does not by itself prove the rendered line span; that check
remains part of the isolated live test. The library's actual role mapping must be
qualified after loading the new read contract, not invented during offline work.

## Why the accepted Stair reads 0.32m

The actual exported Favorite XML has active 2R+G limits0.60–0.65m, going0.25–0.35m,
and riser0.15–0.20m. For test rise3.3m and20risers, R=0.165m. Requested going0.35m
gives2R+G=0.68m and violates the active Favorite maximum. Going0.32m gives exactly
0.65m and matches the previously independently read native value. This is a source
Favorite constraint, not Russian regulatory approval. The requested baseline6.65m
and native walking-line6.4m are retained as separate facts; the source arithmetic
does not prove every detail of the native baseline-solving process.

Source-compatible new test cases include rise3.0m/20risers/going0.35m and
rise3.3m/22risers/going0.35m (R=0.15m and2R+G=0.65m).23risers at3.3m violates the
same Favorite's minimum riser. These are explicit test combinations. They are not
created native stairs, normative values or an engineering design.

GetNativeStairGeometryV1 reads exact native geometry, locks, step/tread counts,
baseline and walking-line coordinates, offsets and active native rules.
EvaluateNativeStairGeometryV1 runs ACAPI_HierarchicalEditing_SolveStair on detached
memo data; it performs no element/default writes and is not live creation evidence.
CreateExactStairsV1 reuses the installed provider's CreateStairs implementation and
Favorite snapshot/restore behavior. It requires locked going, preserves the native
rule profile, calls the SDK solver and refuses a changed requested dimension or
baseline before creation. ModifyNativeStairGeometryV1 uses native element masks and
memo editing on one explicitly owned root with expected-height/going/count guards.
An edit may change hierarchical children; protect all previously accepted roots and
children and test only a new independently owned sample.

Python creation pins the main Favorite XML/hash, checks actual active source ranges,
and checks exact going, riser, height, width, count, baseline and source-rule readback.
The XML's existing partial export remains partial; no complete GDL bundle is claimed.
The accepted0.32m Stair is read-only. There is no rule override or hidden resizing.

## Build and deployment boundary

The existing overlay builder now registers all previous documentation commands and
new native commands through the same provider. The SDK29 Line extended-pen compile
error is repaired using GetEffectiveColorIndex; Text's existing short pen remains
unchanged. No sheet/layout behavior is developed. A fresh build directory prevents
recursive replacement. An explicit read-only local-runtime source snapshot preserves
the provider's existing local library/catalog overlays; its hashes are recorded.
The original dirty Tapir checkout remains unchanged. A clean archived provider build
and a captured runtime-source build are deliberately distinguished.

The complete Windows Release APX compiles and links against SDK29/C++20 with /WX.
That proves a candidate build, not loading/licensing/runtime compatibility. The
installed APX is unchanged. Only after separate deployment permission may a fresh
installed schema qualify the new native contracts. Source schemas cannot authorize
runtime execution. Windows/Linux Python checks cover the same-writer journal,
idempotence, source-rule conflicts, native-type rejection and strict numeric gates.

## Prepared isolated test

Use a separately approved copy named APA_Grid_Stair_Exact_Test_01.pln with the loaded
library. Preserve the original143 and168 identities and files. Initial identity,
port, saved-file hash, source-plan hash and journal gates precede every mutation.
Read the new Grid defaults and source parameter roles; create/update/reuse native
axes from the existing semantic layout. Run detached Stair combinations first and
create only a source-compatible independently owned straight sample outside the
accepted geometry. Independently read dimensions/BREP, native type/variation/GUID,
materials/floors/contacts/collisions; Save/Open and compare retained signatures.
Timeout or mismatch means reconciliation, never blind Create/Modify retry.

No native live result is claimed until the new APX is separately loaded and this
test succeeds. A11.S03 remains PARTIAL; A07 dependencies/S10/historical DONE are
retained. Roof contour/slope development follows actual Grid/Stair acceptance.

Primary SDK reference: [Graphisoft native Stair solver](https://graphisoft.github.io/archicad-api-devkit/group___hierarchical_editing.html).
Local SDK29 headers, actual Favorite XML and the installed source schema are the
qualification inputs; online documentation may describe a later SDK.
