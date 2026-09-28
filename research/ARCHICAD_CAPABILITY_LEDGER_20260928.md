# Archicad 29 + Tapir 1.5.9 capability ledger

Date: 2026-09-28
Branch purpose: consolidated research/audit evidence for Safe BIM.

## Evidence discipline

Every statement below is classified as one of:

- **LIVE CONFIRMED** — observed in Archicad 29 against the disposable project `C:\Users\Admin\Downloads\Test_House_WriteSandbox.pln` unless noted otherwise.
- **STATIC CONFIRMED** — verified from exact Tapir 1.5.9 source (`ENZYME-APD/tapir-archicad-automation`, commit/tag baseline `b1dc828b3a47309e52d003578cbefb13371bd46a`) and/or official Graphisoft Archicad 29 API documentation.
- **UNRESOLVED / LIVE REQUIRED** — architecture is understood but runtime proof is still required.

The project must not promote `success=true`, a returned GUID, a link relationship, or an AABB overlap to stronger evidence than it actually provides.

---

# 1. Environment identity

## R0 — LIVE CONFIRMED

- Archicad 29.
- Tapir exact version: `1.5.9`.
- JSON API port: `19723`.
- Golden/read project: `C:\Users\Admin\Downloads\Test_House.pln`.
- Disposable write sandbox: `C:\Users\Admin\Downloads\Test_House_WriteSandbox.pln`.
- Trusted Building Material GUID used in controlled writes: `922C639B-9875-48DF-A3FC-E0A8AC5F2839`.
- Stories confirmed during live probes:
  - floor 0: level 0.0, height 4.5
  - floor 1: level 4.5, height 3.7
  - floor 2: level 8.2, height 3.0
  - floor 3: level 11.2

Safety policy used in all later runs:

1. identity/read-only first;
2. exact sandbox guard before writes;
3. raw evidence saved;
4. no DeleteElements unless explicitly planned;
5. no SaveProject in geometry probes;
6. immediate readback after writes;
7. unsupported/ambiguous behavior fails closed.

---

# 2. Basic BIM elements

## Walls — LIVE CONFIRMED

Basic walls using the same Building Material can have different thicknesses. Live specimens included 0.25 m and 0.30 m walls using the same trusted Building Material. Thickness is therefore an element property for Basic walls and is not fixed by the Building Material.

Composite walls read their physical thickness from the Composite skins, not from a caller-supplied free thickness field.

## Beams — LIVE CONFIRMED

A Basic rectangular Beam without explicit material inherited defaults that did not match the intended dimensions/material semantics. A Basic rectangular Beam with trusted Building Material and explicit width/height produced exact readback.

Safe rule:

- Basic rectangular Beam must explicitly provide a trusted Building Material.
- If width and height are asymmetric, `isWidthAndHeightLinked=false` must be set where applicable.

## Story placement — LIVE CONFIRMED

Walls/windows demonstrated that:

- `floorIndex` is the owner/home story metadata;
- vertical world Z and `bottomOffset` are distinct;
- a Window's floor index follows its vertical position, not necessarily the owner's home story;
- a tall wall on story 0 can own windows whose returned floor indices correspond to higher stories.

Linked top-story semantics remain only partially proven: changing `relativeTopStory` was accepted, but the Tapir detail readback did not prove evaluated wall height recomputation.

---

# 3. Composites and Building Materials

## R2 / W3 — LIVE CONFIRMED

Composite GUID tested: `35A9ED6F-2F29-4400-B7DE-9C0DEA93A499`.

Known skin sum: 0.287 m.

Requests attempting to use the same Composite with nominal thicknesses 0.287 / 0.500 / 0.100 all read back as 0.287 m.

Safe rule:

- Composite physical thickness comes from skins.
- Any caller-provided element thickness for a Composite must be treated as validation-only; mismatch must fail closed.

Dependency resolution policy:

- `EXACT_MATCH`
- `USER_CONFIRMED_ALIAS`
- `SAFE_BIM_OWNED_TEMPLATE`
- otherwise `MISSING -> STOP`

No fuzzy or fabricated Building Material dependency is permitted.

## CreateComposites — STATIC CONFIRMED

Tapir 1.5.9 supports creation/overwrite of Composite attributes with:

- `useWith`
- skins containing type / Building Material / frame pen / thickness
- separators with line type and pen.

This is sufficient for a high-level `CompositeBuilder`, but Safe BIM must preflight every referenced Building Material, pen and line type before creation.

---

# 4. Roofs, Shells, native semantics

## Roof W4 — LIVE CONFIRMED

- MultiPlane Roof creation succeeded.
- Basic roof thickness and angle read back.
- SinglePlane Roof with 0° angle was accepted; previous assumption that 0° is rejected was false.

## Multi-plane gable semantics — STATIC CONFIRMED / STOCK TAPIR GAP

Archicad's native multi-plane roof model supports per-edge semantics such as gable/sloped behavior. Stock Tapir 1.5.9 creation/readback does not expose the full per-edge data required to author and verify a true one-GUID gable roof.

Safe conclusion:

- native one-GUID multi-plane gable remains the target architecture;
- splitting into unrelated roof elements is only a fallback;
- a custom wrapper exposing pivot polygon edge data is preferable to Morph emulation.

## Shells — STATIC CONFIRMED / LIVE REQUIRED

Archicad 29 supports native Shell families including Revolved Shell with profile, axis, revolution angle and segmentation. Stock Tapir 1.5.9 does not expose a complete `CreateShells` workflow equivalent to the underlying API.

Recommended future wrapper:

- `CreateExtrudedShells`
- `CreateRevolvedShells`
- `CreateRuledShells`

---

# 5. Morph geometry

## W7 arbitrary polyhedra — LIVE CONFIRMED

Created and read back:

- pyramid;
- wedge;
- octahedron;
- later a wedge body was replaced through `ModifyMorphs`.

Arbitrary non-box polyhedral Morph creation is therefore proven.

## W7D topology / closedness — LIVE CONFIRMED

Created:

- closed tetrahedron: Solid, `isClosed=true`;
- closed cube: Solid, `isClosed=true`;
- open box missing top: Surface, `isClosed=false`.

All topology checks passed. Archicad may renumber Morph vertex IDs after body finalization; verification must therefore canonicalize topology by coordinates/relationships rather than assume original vertex numbering survives.

## Morph full geometry battery — LIVE CONFIRMED in aggregate

The research battery covered:

- cube/open box;
- pyramid;
- wedge;
- dense sphere / ellipsoid;
- hemisphere / dome-like shell;
- cylinder;
- cone;
- frustum;
- torus;
- wave/saddle surface;
- wire geometry;
- mixed surface/wire scenarios.

The correct semantic discriminator is geometry intent:

- `Solid` -> expected closed solid where appropriate;
- `Surface` -> open valid surface;
- `Wire` -> zero filled polygons valid.

## W7N materials / holes — LIVE CONFIRMED

14/14 checks passed:

- Morph face with a true hole round-tripped correctly;
- whole-Morph Building Material round-tripped;
- default Surface round-tripped;
- distinct per-face Surface overrides round-tripped.

## W7K stress — LIVE CONFIRMED

Progressive triangulated sphere stress passed all requested levels through approximately:

- 4514 vertices;
- 9024 faces;
- Euler characteristic 2;
- `isClosed=true`;
- zero boundary edges;
- zero non-manifold edges.

Observed create time at the largest tested level was roughly 0.38 s and readback roughly 0.07 s in the live environment. This is a proven working level, not the maximum limit.

---

# 6. Morph bugs / unsafe paths

## `ModifyMorphs(body=...)` closedness defect — LIVE CONFIRMED

Minimal controlled test:

- CONTROL cube created and read `isClosed=true`.
- NOOP cube: same exact closed body written back through `ModifyMorphs(body=...)` -> `isClosed=false`.
- RESIZE cube: different but still mathematically closed body -> `isClosed=false`.
- topology remained closed: 8 vertices / 6 faces / 12 edges, zero boundary/non-manifold.

This proves a Tapir/SDK body-replacement closedness defect independent of body topology.

Safe rule:

- `ModifyMorphs(body=...)` is disabled for trusted Solid editing until fixed or independently rebuilt/verified.
- transform-only Morph edits can be handled separately.

## `rotationDegreesZ` defect — LIVE + STATIC CONFIRMED

Live result for 90°:

- origin `(9950,600,0)` became `(0,600,-9950)`;
- axes matched a Y-axis rotation rather than Z-axis rotation;
- the origin itself was rotated around world zero.

Explicit `xAxis/yAxis/zAxis` replacement behaved correctly and preserved origin/closedness.

Source review explains the observed transform: the implementation mixes X/Z matrix components.

Safe rule:

- `rotationDegreesZ` disabled;
- Morph rotations use explicit basis axes / explicit matrix math.

## Edge smoothing — LIVE + STATIC CONFIRMED

W7P created four otherwise identical spheres requesting default edge modes:

- control;
- HardVisible;
- HardHidden;
- SoftHidden.

All remained closed, but requested hidden/soft edge defaults read back as HardVisible. Stock Tapir schema already warns that normal create/modify edge assignment is affected by an Archicad SDK issue.

Recommended wrapper:

- `ChangeMorphEdgeTypes` using the dedicated Archicad Morph edge-type API.

---

# 7. Morph conversion policy

Morph itself is not dangerous and is a first-class geometry tool.

What needs policy control is converting an existing semantic BIM element into Morph.

Safe policy:

```text
if lifecycle == temporary:
    BIM -> Morph conversion is ALLOWED
elif lifecycle == final:
    conversion is LAST_RESORT
    require_reason = true
    require_user_confirmation = true
```

Temporary/service elements that are guaranteed to be deleted later may be converted freely.

For permanent originals, prefer Morph copy + preserve the original until explicit replacement/deletion is approved.

---

# 8. Solid Element Operations / boolean modeling

## Associative SEO — LIVE + STATIC CONFIRMED

Tapir supports real Archicad solid links using operations including:

- Subtraction;
- SubtractionUpwards;
- SubtractionDownwards;
- Intersection;
- Addition.

The wrapper calls the native Archicad solid-link API.

### W8 association persistence — LIVE CONFIRMED

Wall target + Morph operator with `Subtraction`:

- link created;
- link read back;
- operator Morph geometry was later changed;
- Subtraction relation remained.

This proves associative relation persistence.

### Critical evidence distinction

`GetSolidElementLinks` proves a relationship exists.

It does **not** by itself prove the evaluated cut volume or resulting triangulated body.

Required future evidence levels:

1. `LINK_CONFIRMED`
2. `EVALUATED_GEOMETRY_CONFIRMED`

The second should use Quantity and/or ModelAccess, not screenshots alone.

## W8C figured wall-cut investigation — UNRESOLVED / LIVE REQUIRED

Several exploratory scripts attempted circle/arch/star/sloped-top Wall-Morph cuts.

Important corrections:

- one script proved four links but visible operators could visually fill their own cuts;
- a later hiding test stopped before modifying the project because one ARCH link no longer read back;
- another clean test attempted `layerIndex` directly in `CreateMorphs`, but exact Tapir 1.5.9 schema does not accept that field, so it stopped before creating the operators.

Therefore **figured Wall-Morph cuts are NOT currently marked PASS**.

Correct future test order:

```text
CreateMorph
-> CreateSolidElementLink
-> SetDetailsOfElements(layerIndex = hidden operator layer)
-> rebuild
-> verify relation
-> verify evaluated geometry via ModelAccess/Quantity
```

## Destructive Morph boolean — STATIC CONFIRMED / WRAPPER REQUIRED

Archicad exposes destructive solid operations for Morph geometry (subtract/intersect/add), returning new result Morph(s) and consuming/replacing input semantics according to the native operation behavior.

Stock Tapir 1.5.9 does not expose a complete high-level wrapper for this operation.

Recommended wrapper:

- `CreateMorphSolidOperations`
- explicit destructive flag in Safe BIM policy;
- pre-operation GUID capture;
- result GUID verification;
- quantity/topology verification.

---

# 9. Native Openings

## STATIC CONFIRMED correction

Archicad 29 supports native rectangular, circular and polygonal Opening geometry.

Current Tapir 1.5.9 `CreateOpenings` does **not** expose arbitrary polygon coordinates to callers. It requires width/height and, in its AC29 path, constructs a four-corner polygon and calls polygonal placement internally.

Therefore:

- arbitrary polygon Opening is an Archicad capability;
- it is not yet a stock Tapir caller capability;
- previous statement that stock Tapir already exposes arbitrary polygon openings was too strong.

Recommended wrapper extension:

```text
shape = Rectangular | Circular | Polygonal
polygonCoordinates = [...]
```

Native Opening should be preferred over Morph SEO whenever the architectural intent really is an opening and the native shape can express it.

---

# 10. Transforms, copying and arrays

## STATIC CONFIRMED

Tapir supports copying during transform operations (`MoveElements` and `RotateElements` paths include copy semantics).

This is enough to build high-level arrays without requiring a native `MultiplyElements` command:

- linear array;
- rectangular/grid array;
- radial array;
- path array;
- rising path / Z progression;
- lateral offset;
- orientation to tangent;
- optional progressive scale if supported by element-specific transforms.

Safe BIM should perform math at the planner level and batch copies/transforms by database/context.

---

# 11. Sections, elevations, databases and 3D

## Dual-context model — STATIC CONFIRMED

Archicad distinguishes:

- Front Window (what the user sees);
- Current Database (where database-dependent API calls operate).

They need not always be the same.

This enables a future background workflow where the user remains visually in a Section/Elevation while Safe BIM temporarily switches Current Database to the model database, edits the owner element, returns to the document database and rebuilds.

## Tapir current limitation

`ChangeWindow` is UI-oriented. In several paths it couples database switching with window/view navigation, and `GoToView` applies saved view state.

Recommended primitives:

- `GetExecutionContext`
- `RunInDatabase`
- `RebuildDatabase`
- restore prior database without changing Front Window.

## Section generated elements — STATIC CONFIRMED

Tapir `GetSectionElements` can expose raw section-element GUIDs and their owner model GUIDs.

This supports:

```text
section representation -> owner GUID -> model edit -> section rebuild
```

Generated section elements should not be treated as the authoritative model object.

## Section dimension presets — STATIC CONFIRMED

Available preset concepts include:

- WallCompositeFaces;
- WallSkinBorders;
- SlabCompositeFaces;
- SlabSkinBorders;
- BeamOrColumnRefLineEndPoints;
- BeamOrColumnBoundingBoxCorners;
- DoorWindowWallHoleCorners;
- DoorWindowModelHotspots.

This can significantly accelerate automated section/elevation documentation because Archicad already knows the semantic witness geometry.

## Ghost-GUID risk — STATIC / ISSUE EVIDENCE

Some section/elevation dimension creation flows have historically returned GUIDs even when the element was not truly created in the target database.

Safe rule for every created document element:

```text
create -> returned GUID -> GetDetails/read target DB -> only then PASS
```

## Off-screen 3D — STATIC CONFIRMED architecture

Archicad ModelAccess can evaluate 3D representation without requiring the user-facing 3D window to become the primary verification mechanism.

Recommended verification hierarchy:

1. cheap element/context filters;
2. Quantity-based fast verification;
3. ModelAccess deep geometry verification;
4. visible 3D only when human review is useful.

Future wrapper set:

- `EvaluateElements3D`
- `GetElementQuantities`
- `GetConnectionTable`
- optional temporary Sight/session abstraction.

AABB intersection remains only a preflight test and must never be promoted to solid-intersection proof.

---

# 12. GOST / SPDS documentation architecture

## Research status — STATIC CONFIRMED architecture, LIVE TESTS PENDING

Safe BIM should not hard-code a single arbitrary pen/font combination as "GOST". It should use a standards profile that resolves document roles into Archicad attributes.

Recommended semantic roles:

- cut contour;
- visible contour;
- thin/secondary;
- dimensions;
- axes;
- hidden;
- hatch;
- text.

Tapir already supports:

- Pen Tables;
- Line Type attributes;
- text/label pen and font indices;
- dimension-style name stored in View settings;
- associative dimensions.

Missing/desired custom primitives:

- resolve Font by family/name rather than hard-coded index;
- GOST Dimension Style provision or template guarantee;
- dimension placement/collision engine using paper-space offsets converted through view scale;
- compliance audit.

Minimum dimension-layout rule should be expressed as policy in paper units first and converted through scale. It must remain collision-aware rather than assuming one fixed model-space offset.

---

# 13. Profiles

## STATIC CONFIRMED

Tapir 1.5.9 `CreateProfiles` supports significantly more than simple copy-from-existing behavior.

Geometry sources include:

- `sourceAttributeId` (copy existing geometry);
- `newSkins` (caller-authored geometry on AC27+);
- both combined.

Repository examples/source cover:

- polygon geometry;
- arcs;
- multiple contours;
- holes;
- multiple skins;
- material and edge properties;
- `replaceSkins` behavior.

Profiles can carry applicability flags such as wall/beam/column usage.

Caution:

- do not write arbitrary edge slots blindly;
- some internal/anchor bridge edges are deliberately skipped because source investigation found crash-prone behavior.

Recommended high-level API:

- `ProfileBuilder.create`
- `ProfileBuilder.clone_and_modify`
- canonical edge map from readback before edge edits.

---

# 14. Shared library architecture

## STATIC CONFIRMED

Exact Tapir 1.5.9 includes library commands:

- `AddFilesToEmbeddedLibrary`
- `GetLibraries`
- `SetLibraries`
- `AddLibraries`
- `ReloadLibraries`
- `GetAvailableLibraryParts`

Important distinction:

- Embedded Library is project-local.
- A linked Local Library folder can be shared by multiple projects.

Recommended Safe BIM architecture:

```text
SAFE_BIM_LIBRARY/
  Furniture/
  Windows/
  Doors/
  Equipment/
  Details/
  User/
```

On Project Open/New:

```text
GetLibraries
-> if shared folder absent: AddLibraries(path)
-> optionally ReloadLibraries
```

This satisfies the goal that an object added to the common library can be available in subsequently opened projects, provided the add-on auto-attaches the shared folder or the project is created from a template that already links it.

Do not treat library-part index as durable identity; resolve by stable library-part identity/UniID/name+subtype policy each session.

Future wrapper required for the user-facing workflow:

- `SaveSelectionAsSharedLibraryObject`

Stock Tapir can attach/register files, but it does not yet provide a full "save selected model geometry as reusable GSM object in shared library" command.

---

# 15. Current high-priority problems

## P0

1. `ModifyMorphs(body=...)` corrupts closedness state on valid solids.
2. `rotationDegreesZ` is implemented incorrectly.
3. SEO relationship proof is weaker than evaluated-geometry proof.
4. batch write paths can leave partial results when an item later fails.
5. project evidence files are lagging behind the latest live findings.

## P1

6. Morph edge smoothing needs dedicated API wrapper.
7. arbitrary polygon native Opening needs Tapir wrapper extension.
8. destructive Morph boolean needs wrapper.
9. native Shell creation needs wrapper.
10. multi-plane Roof per-edge semantics need wrapper.
11. section/elevation dimension commands require post-create existence verification.
12. database/window operations need a background database execution abstraction.
13. off-screen 3D/Quantity verifier needs wrapper.
14. Font resolution by name needs wrapper.
15. GOST dimension placement/compliance engine does not yet exist.
16. SaveSelectionAsSharedLibraryObject does not yet exist.

## P2

17. runtime capability negotiation is missing.
18. project/story/attribute caches should be event-invalidated rather than reread before every micro-operation.
19. operations should be scheduled/grouped by Current Database.
20. high-level transactions should reduce JSON/API round-trips and rebuilds.

---

# 16. Safe BIM architectural target

```text
TASK
 -> planner
 -> choose native BIM / Morph / documentation primitive
 -> preflight dependencies
 -> schedule by database/context
 -> one controlled transaction scope where possible
 -> write
 -> relationship readback
 -> quantity / evaluated geometry verification when needed
 -> evidence ledger
 -> human-visible view only when useful
```

Tool-choice preference:

```text
architectural opening -> native Opening
roof -> native Roof
revolved architectural shell -> native Shell
wall/beam/column/slab -> native BIM element
freeform/helper geometry -> Morph
associative 3D cut -> SEO
destructive Morph boolean -> native Morph solid operation
```

Morph remains fully valid and useful; only destructive conversion of permanent semantic BIM elements requires last-resort policy.

---

# 17. Next live proof suite

When access to the notebook returns, the highest-value tests are:

1. native Opening rectangular/circular/polygon wrapper behavior;
2. evaluated Wall-Morph SEO via Quantity/ModelAccess;
3. destructive Morph boolean + result GUID/topology/volume;
4. background Current Database edit while Section/Elevation remains front window;
5. generic Text/Line/Label creation inside Section/Elevation DB with existence readback;
6. Quantity/ModelAccess cost for 1/10/100/1000 elements;
7. Profile creation matrix (rect/L/T/U/arc/hole/multi-skin);
8. CompositeBuilder 3/5/7 skins + separator validation;
9. GOST Pen/Line/Font/Dimension test set;
10. shared library attach/reload across two PLN files;
11. save reusable object to shared library once the wrapper exists.

No item should be promoted to PASS without the evidence level its semantics require.