# Native BIM documentation adapter

The same Archicad model supplies saved floor-plan views, native section
databases and specifications. `scripts/archicad_bim_documentation.py` delegates
all native changes to the existing SceneWriter and SQLite journal. It reuses
the BIM Graph contract compiler, Native Model Dump, retained GUID/material/story
signatures and the existing connected IFC resultant-BREP quantity adapter.
There is no drawing renderer, normative calculator, second executor or daemon.

## Working interface

1. Bind the exact user-authorized saved test project, its port, saved-file hash,
   actual story and accepted native signatures using the retained SceneWriter.
2. Obtain `ProjectMap`/`PublicViewMap` with `GetNavigatorItemTree`. Resolve
   `StoryItem` by native story prefix and navigator GUID. Resolve each view's
   database through `GetDatabaseIdFromNavigatorItemId`.
3. `create_viewpoint(...)` creates one explicitly planned native Section or
   Interior Elevation. `create_view(...)` saves an associative view of that
   native database and independently verifies its source database identity.
4. `refresh_package(...)` rebuilds each supplied vertical database, reads actual
   section-element/owner GUID pairs, activates the saved floor view and extracts
   native cut-fill polygons and typed element details. It returns one immutable
   shared model snapshot and a package of plan facts and specifications.
5. `write_package(...)` writes `documentation.json` and a CSV per native type.
   `compare_versions(...)` distinguishes actual BREP/material/story changes
   from changes in the native floor-plan representation.

Example for an already bound writer and approved native view identifiers:

```python
from archicad_bim_documentation import refresh_package, write_package

result = refresh_package(
    writer=writer, run_id=unique_run_id,
    floor_view_guid=approved_floor_view_guid, plan_story=0,
    guids=actual_building_guids,
    views={
        "section": {"guid": approved_section_view_guid, "windowType": "Section"},
        "projection": {"guid": approved_projection_view_guid,
                       "windowType": "InteriorElevation"},
    },
    retained_signatures=accepted_native_signatures,
    authorization_ref=explicit_user_scope,
    saved_sha256=verified_saved_pln_sha256,
)
write_package(result["package"], new_output_directory)
```

The offline CLI consumes an actual dump and explicit GUID membership:

```text
python scripts/archicad_bim_documentation.py --native-dump model.json --guids selected-guids.json --story 0 --output new-documentation
```

This CLI prepares facts/CSV only. It does not create native views, connect to
Archicad or grant write permission. Missing or repeated GUIDs/stories fail
before native writes. Output directories must be new; exports never overwrite.

## Installed API window barrier

The installed `GetModelDumpV1` enumerates the active database before calling
`ShowAllIn3D`. It switches the active window to 3D. A first call from an
elevation can omit nonspatial floor-plan identities. `capture_full_model`
re-reads this read operation once if required identities are absent. Missing
identities still block the operation.

The geometry barrier runs **before** an independently journalled activation
of the exact target navigator item. Section/wall writes are refused unless the
native current window is FloorPlan. Vertical regeneration uses its matching
Section/Elevation/InteriorElevation window. Actual story/window readback is
mandatory for floor facts. No Create/Modify is replayed to recover a failed
read, timeout or wrong database. Save/Open opt in only through a scoped
documentation intent; Open cannot target a foreign project.

## Current native follow-on and placement correction

The follow-on keeps the exact PR71 head as its parent. It preserves all121
accepted main-model signatures, including the original109, and adds one real
native **Elevation** by copying an existing Elevation template through
`MoveElements(copy=true)`. Its four native subordinate Objects bring the main
inventory to126. The original source marker and physical building are retained.

The first finite marker segment crossed only half the building. The user's
floor-plan screenshot revealed this; visible-owner counts had not proved full
coverage. Only the newly created Elevation was moved by projectY=-5m, then its
native database and new linked Drawing were rebuilt. Native rendering now shows
the complete west face with both stories, both visible windows and roof.
The selected owner count changed9→12, but the acceptance comes from the actual
rendered silhouette and measured projection extent, not that count. The native
PDF roof width is8.029912m at1:100, versus8.029888m from the actual roof BREP
projectY extent (0.0001m export precision tolerance). This is horizontal-scope
proof, not engineering, per-primitive or material-semantic acceptance.

One new native associative Section dimension measures the actual0.20000006m
Slab thickness. Five native witness coordinates and SectionElement→Slab owner
links survive Save/Open. These are native drawing2D coordinates; memo loc3D does
not establish project-world XYZ.

Three new saved views use actual ProjectMap sources. New SetViewSettings
scopes control only their scale and saved frame. One A2 native Layout/master
holds three native Drawings: plan, section and real Elevation. A preliminary
oversized new Drawing is parked outside the sheet; its GUID is preserved.
Element, database, ViewMap and LayoutBook/Publisher navigator GUID domains are
separate. GetDetailsOfElements reports an opaque drawing link GUID rather than
the requested view GUID, so that metadata identity remains NOT_VERIFIED.
A controlled change of the new plan view scale100→125→100 changed its Drawing
scale0.01→0.008→0.01; the clip frame stayed fixed. This establishes that source
behavior without pretending the GUID fields are equal.

`PublishPublisherSet` for the selected new Layout generated one native A2 PDF
page. File bytes, pages, titles, drawing scale and rendered facade were checked,
including after Save/Open. The views publisher produced65pages despite selecting
only two items; that path is not accepted as a selected subset. Outputs require
new empty local directories and independent file readback: the SDK's empty{}
success reply alone proves no PDF. No global Publisher settings were edited.

`archicad_native_documentation` reads native owner coverage, associative anchors,
Drawing fill contours, schedule definitions and actual exported files. Native
Drawing contours include32plan and34section polygons. Inverting the Drawing
transform supplies candidate drawingUV, which requires native anchor checks;
it never supplies project XYZ. The facade's surface projection exposes no such
fill contours through this installed API. Its scope is independently checked in
the native vector PDF. Line/text primitives and per-contour BIM ownership remain
unavailable; full vertical graphics export is not claimed.

Thirteen native Schedule definitions exist. Native row-reading and scheme
configuration are unsupported by the installed contract. Existing six-type CSV
specifications continue through the shared snapshot; no duplicate schedule
engine is created. Previously verified height-change synchronization is retained
as historical evidence, not rerun or represented as a new BIM-change test here.
The current primary physical modelVersion is unchanged while the facade,
new view frames and new linked drawings are corrected and updated explicitly.
No background watcher is introduced.

## Window and publication boundaries

From a Layout, GetModelDumpV1 returns the precise ShowAllIn3D error
-2130313109. The existing SceneWriter journals a view-only change to the actual
floor0 ProjectMap item after exact project identity/saved-byte gates, then
rechecks the complete BREP/material/story signatures. Other native errors fail
closed. This recovery does not replay a Create, Modify or Publish operation.
CreateLayout requires an explicit master even though the installed schema
marks it optional. UpdateDrawings returns `success:true`, rather than an
executionResults array. Post-open cached Drawing fills are initially absent;
a known-success update of only the new Drawings restores the native contours.

Original ambiguous journal events are retained. Independent reconciliation
established either no dispatch/no effect or the actual created native identity;
no blind Create/Modify replay was used. Save/Open and all126current main-model
signatures passed independently. New dimension, layout, saved view databases
and drawing identities were separately read in their actual native databases.

A11.S03 stays PARTIAL; A07.S01 remains dependency-gated and A11.S10 BLOCKED.
Normative and engineering acceptance are not performed. Normative-system and
Knowledge Graph/search implementations, installed APX and main/master are
unchanged. The main APA orchestrator used the existing read-only Knowledge
Graph with current GitHub source gates before claiming this task. MORPH LAST
RESORT applies; no Morph or new physical BIM construction was created here.

Next: qualify native schedule rows/configuration or register the missing contract;
extend vertical line/text and owner-bound coordinates through a supported API.
Before future facade acceptance, require independent axis/scope plus actual
native drawn span and rendered output; a populated database is insufficient.
