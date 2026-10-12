# Connected component package v3.1

The accepted 18-element native core now shares actual absolute metre XYZ,
native GUIDs, named story bindings, materials, host links and body bounds with
opt-in Roof, Morph and one straight Ventilation routing element. Every model
Create and explicit Morph repair uses the retained SceneWriter/SQLite journal.
Its original six-command default remains unchanged; adapters must be enabled.

`archicad_connected_components.py` reuses the existing BIM Graph, authored
typed readback, Model Dump normalizer, owned ColumnSegments, and the donor Roof
and Morph cycle geometry helpers. Donor standalone transports/deletions are
never called. `archicad_connected_ifc.py` uses IfcOpenShell on local exports;
`archicad_connected_solver.py` uses actual OR-Tools CP-SAT to choose among
explicit straight-route candidates. No second writer or own solid/path engine.

## Entry point

Install `scripts/requirements-connected.txt` in an isolated dependency folder.
The source argument is the local accepted native core or connected receipt;
the intent contains `enabled`, `operations`, optional `dependencies`.
The original core, previous connected prefix, model inventory and every new
command's parameters are checked before writing. Only one MEP route is supported.

```text
python scripts/archicad_connected_components.py --source accepted.json --intent intent.json --mode offline --output offline-result
python scripts/archicad_connected_components.py --source accepted.json --intent intent.json --mode preflight --output live-preflight
python scripts/archicad_connected_components.py --source accepted.json --intent intent.json --mode execute --output live-result --state-dir existing-state --scene-id unique-id --confirm-plan-hash <fresh-native-preflight-hash>
```

Default mode is offline. Native mode binds the previously approved isolated test
target only. Modules are explicit `roof`, `morph`, `mep`; unknown or disabled
module operations fail. Existing connected prefix elements are re-read and
reused, never recreated. Intent hash binds source, GUID inventory, enabled
adapters, dependencies and the current whole-model geometry before execution.

## Actual bounded integration scenario

On AC29 build5101 RUS / installed Tapir1.5.10, a Basic single-plane Roof covers
the accepted upper-floor footprint at pivot Z6m, thickness0.2m, slope0.15rad.
The Details v2.12 archive is SHA-verified and actually joins selected ARMO IR
entities to two source facts. A project-length2m diagnostic Morph uses the
source25×150mm cross-section; its material and placement are explicit project
inputs. It intentionally intersects the Roof to calibrate native collision
reporting. It is not an approved ARMO assembly or a timber material claim.

One native Ventilation route runs between42,46,2.5 and48,46,2.5m, nominal
section0.2×0.15m. Native readback proves its system, polyline, one segment,
two nodes and one physical duct with two matching endpoint ports. Those ports
are unconnected. Generic GetDetails returns Unknown/native type150 and
GetMEPElements omits these current AC29 elements; dedicated MEP getters and
actual physical BREP supply the bounded proof. Branching/full networks remain
unsupported. Actual physical duct/flange bounds are0.262×0.212m, and the CP-SAT
screen uses these rather than nominal section dimensions. AmongY42,44,46,
Y44 is blocked by two native columns; preferredY46 is OPTIMAL and equals the
native route. An independent native collision query reports no collisions
with all18 retained core primaries. This is a small candidate selection test,
not global path optimality or engineering clearance approval.

## Defects discovered and resolved in this scope

- The installed CreateMorphs size shortcut produced an8-vertex **5-face open**
  surface. It was not accepted as a solid. Read-only reconciliation retained its
  GUID; one new explicit ModifyMorphs body added the missing bottom face.
  Actual BREP then had6faces and closed edges. The compiler now expands a size
  request into an explicit6-face body **before** graph validation/hash. A
  separate0.1m diagnostic cube through the reusable CLI proved CreateMorphs
  with that body, one create only, with all47 previous GUIDs/geometry retained.
- Morph memo `isClosed=false` still disagrees with resultant `BREP.closed=true`.
  This remains visible in context. Exact oriented contours, vertex placement,
  native BREP closure and independent edge-incidence checks establish the
  geometry; the memo flag is not promoted to correct.
- The first OpenProject response timed out at15s. No Open retry was made;
  subsequent identity-first readback reconciled all21 primaries/47 GUIDs and
  saved file hash. The final22-element save/reopen used40s transport and
  returned explicit success, with equal saved/reopened file SHA256.
- IFC exports the physical duct as IfcFlowSegment, not the routing container's
  IFC root. The connector retains both identities and explicitly maps the
  exported physical duct. No container GUID is silently relabelled.

## Verification and remaining gaps

Final saved/reopened model:22 primaries/48 total native GUIDs. Original40 GUIDs,
typed core/story/material/library/host semantics, and actual BREP were retained.
The CLI create separately preserved all47 previous geometry records. Positive
Roof/Morph collision reports hasBodyCollision=true. Two Morph diagnostic
elements are deliberately retained as test evidence.

Local IFC2X3 export is parsed with IfcOpenShell0.8.5; its file length unit is
millimetres (scale0.001), normalized geometry is metre absolute XYZ. All22
coordinated entries match actual native world bounds within1e-5m, including one
explicit physical-route representation. This is GUID/bounds verification,
not complete face, quantity or semantic equivalence. IFC/model raw files stay
local; GitHub receives only selected anonymized proof and checksums.

Details integration currently adapts the selected ordinary IR family. The
release contains1142ordinary detail/IR records and73special Porotherm context
records. Those73context records need a separate adapter. The ARMO candidate's
eight required entities lack dimension facts, and its source commit gate is
false; the native host link does not authorize an entire manufacturer assembly.
SAM/SAF solver connection, Shell creation, generic Opening typed readback,
SEO execution, normative engineering approval, document generation, visible
UI, general MEP connections, large-model speedup and installer remain gaps or
source-only capabilities. Earlier accepted materials/GDL/core functions are
preserved, not replaced by this package.

24 new focused tests pass locally. Full Windows discovery ran340 tests with28
historical SQLite temporary-directory cleanup errors; these are not reported
as a Windows full-suite PASS. The PR's full Linux CI is the required independent
regression confirmation. Code and evidence remain on separate branches;
main, earlier accepted branches, APX, source archives and original LCF are
unchanged. No paid service or delegated agent was used.
