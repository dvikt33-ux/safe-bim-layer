# Next live test matrix

Date: 2026-09-28
Purpose: turn current static research into reproducible Archicad 29 evidence without repeating already-proven probes.

## Global gates

Every write test must:

1. verify Tapir exact version 1.5.9 (or record new exact version if intentionally updated);
2. verify exact disposable sandbox path;
3. save raw evidence before and after each write phase;
4. use no DeleteElements/SaveProject unless the test explicitly requires it;
5. read back the actual postcondition;
6. distinguish relation proof from evaluated geometry proof;
7. stop escalation on unexpected partial write/error.

Evidence grades:

- L1 request accepted;
- L2 returned identifier exists;
- L3 properties/relations read back;
- L4 evaluated geometry/quantity or durable dependency behavior confirmed;
- L5 cross-context/project persistence confirmed where applicable.

---

# Suite A — Native Openings

## OPEN-01 rectangular

Create native Opening in a disposable wall; verify owner, dimensions, GUID existence and evaluated 3D opening.

## OPEN-02 circular

If supported by wrapper/API path, verify native Circular semantics rather than approximating with polygon unless approximation is intentional.

## OPEN-03 polygonal extension

After wrapper exists, create arch/star/concave contour using native polygonal Opening.

Verify:

- native element type remains Opening;
- owner Wall remains Wall;
- contour readback/geometry;
- evaluated 3D hole;
- edit owner/Opening and prove associativity.

---

# Suite B — Associative SEO

## SEO-01 basic Wall-Morph subtraction

- create target Wall;
- create closed Morph operator;
- prove AABB overlap only as preflight;
- create Subtraction link;
- read link;
- verify target evaluated volume/geometry changes using Quantity/ModelAccess.

## SEO-02 hidden operator layer

Correct sequence:

```text
CreateMorph
-> CreateSolidElementLink
-> SetDetailsOfElements(layerIndex = hidden layer)
-> rebuild
-> relation readback
-> evaluated geometry readback
```

## SEO-03 operator edit

Modify operator using a safe geometry path or recreate operator while preserving test intent; prove association/evaluated target updates.

## SEO-04 directional operations

SubtractionUpwards / SubtractionDownwards.

## SEO-05 addition/intersection/remove

Create, verify evaluated effect, remove relation, verify relation absence and evaluated rollback/rebuild behavior.

---

# Suite C — Destructive Morph booleans

After wrapper implementation:

- subtract;
- intersect;
- add/union.

Capture input GUIDs and result GUIDs.

Verify:

- documented destructive lifecycle;
- result body closedness/topology;
- volume/surface before/after;
- result GUID durability;
- undo behavior if wrapper uses one undoable command scope.

---

# Suite D — Morph bug fixes

## MORPH-FIX-01 body replacement

After fix/custom path:

- identical closed cube replacement;
- resized closed cube replacement;
- dense sphere replacement.

Must preserve `isClosed=true` and topology.

## MORPH-FIX-02 rotation

Fix or remove `rotationDegreesZ`; 90° must rotate basis around Z with intended pivot semantics. Compare against explicit axes matrix.

## MORPH-FIX-03 edge smoothing

Use dedicated edge-type API wrapper; prove HardVisible / HardHidden / SoftHidden live readback and visible sphere behavior.

---

# Suite E — Profiles

Create and read back:

1. rectangle;
2. L;
3. T;
4. U;
5. arc-containing profile;
6. profile with hole;
7. multi-skin profile.

Then:

- assign to Wall/Beam/Column where allowed;
- modify Profile attribute;
- prove dependent elements rebuild.

No edge override is allowed without canonical readback and target validation.

---

# Suite F — Composites

Create:

- 3 skins;
- 5 skins;
- 7 skins.

Verify exact ordered Building Material GUIDs, skin roles, thicknesses and separators.

Then create supported BIM elements using each Composite and prove physical thickness derives from skin sum.

---

# Suite G — GOST/SPDS documentation

## GOST-01 font

Resolve font by name through custom wrapper; create Text and Label; read exact resolved font index and style fields.

## GOST-02 pens

Create Safe BIM Pen Table with selected role widths/colors; attach to Safe BIM view; read View settings.

## GOST-03 line types

Create/read Solid, Dashed, Center/Section role line types.

## GOST-04 plan dimensions

Create associative dimensions against walls/openings.

Verify:

- true Dimension element;
- post-create existence;
- association after owner move;
- first-chain paper-space minimum policy;
- inter-chain minimum policy;
- collision avoidance.

## GOST-05 section/elevation dimensions

Use semantic presets; verify returned GUID really exists in expected DB.

---

# Suite H — Database / view acceleration

## CTX-01 dual context

Keep Section/Elevation as Front Window; switch Current Database in background to model DB, modify owner, restore document DB, rebuild once.

Verify Front Window did not change.

## CTX-02 timing

Compare:

- UI `ChangeWindow` route;
- background Current Database route.

Run multiple iterations and report median/p95.

## CTX-03 2D writes

Create/read Text/Line/Label in Section and Elevation DB.

## CTX-04 scheduler benchmark

Compare 20 mixed operations in conversational order vs grouped by database/context.

---

# Suite I — Off-screen 3D verifier

Benchmark selected evaluated geometry for:

- 1 element;
- 10 elements;
- 100 elements;
- 1000 elements.

Collect:

- generation time;
- response size;
- body/polygon counts;
- memory/timeout behavior;
- comparison with full visible 3D switch.

Use Quantity first, ModelAccess second.

---

# Suite J — Shared library

## LIB-01 attach

Attach Safe BIM linked local library to project A; verify `GetLibraries`.

## LIB-02 second project

Open project B; auto-attach same shared library; verify no duplicate entry.

## LIB-03 part discovery

Place/register a known test GSM in shared folder; reload; verify `GetAvailableLibraryParts` in A and B.

## LIB-04 SaveSelectionAsSharedLibraryObject

After wrapper implementation, save one selected geometry object; verify manifest, file, reload and discovery in project B.

---

# Suite K — Arrays / replication

Test:

- linear;
- grid;
- radial;
- along 2D curve;
- along 3D curve;
- rising Z;
- lateral offset;
- tangent orientation.

Run on Morph plus representative native Wall/Column/Beam/Object where valid.

Verify new GUIDs, transforms, spacing/orientation and dependency semantics.

---

# Suite L — Native Revolved Shell

After wrapper implementation:

- cylinder-like profile;
- cone/frustum profile;
- dome;
- vase/baluster;
- partial 180°;
- partial 270°;
- full 360°.

Compare native Revolved Shell semantics against Morph-generated revolve only as a geometric fallback/reference.

---

# Stop condition

A capability is closed only when:

- no known contradictory evidence remains;
- evidence grade matches the claim;
- repeat run behavior is understood;
- failure behavior is documented;
- destructive lifecycle is explicit;
- Safe BIM policy chooses the correct native/freeform tool.