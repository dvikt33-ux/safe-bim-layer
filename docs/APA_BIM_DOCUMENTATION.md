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

## Verified scope and limits

The live package preserves all 109 accepted native signatures. It adds one
native Section, one native Interior Elevation used from outside the building,
four explicitly saved views and one separate native test Wall. The test Wall
was changed from 1.0 to 1.2 m. Resultant volumes changed from 0.085 to 0.102 m3;
the existing quantity adapter measures the actual joined body, not a gross box.
Native cut-fill availability changed from 15 to 16 selected elements. One
column's plan representation also changed while its accepted 3D body stayed
unchanged. Native collision detection found no new volume intersections.
Save/Open retained the accepted model, new elements and saved view database
links. The public refresh adapter was exercised end to end on this model.

The scoped package contains 19 primary elements: 9 Walls (including the test
Wall), 2 Slabs, 2 Columns, 4 Windows, 1 Door and 1 Roof. Wall/Slab quantities are
verified planar resultant BREP quantities. Missing Column-parent bodies and an
unqualified Door quantity remain explicit; no segment/parent double counting.

The reused native exterior Elevation database is empty for the selected
building. Its saved view exists, but it is not an accepted facade drawing.
The new exterior projection is generated by the **InteriorElevation** native
tool; it is not presented as a newly created native Elevation element.
The installed interface has no `CreateElevations` or supported exterior-marker
geometry edit contract. Section/interior-elevation cut-line memo readback and
complete vertical 2D primitive export are unavailable. Native owner links and
successful regeneration do not prove every drawn vertical coordinate.

CSV specifications are actual BIM facts, separately identified from native
interactive schedules. Existing schedule items can be discovered, but their
row read/configuration contracts are not installed. A configured native PDF
release was not executed. `PrintView` is a printer operation without an output
filename contract. Available publisher-set names are read through the existing
transport's read-only `API.GetPublisherSetNames` path, documented in the
[Graphisoft Python API](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.html#archicad.commands.Commands.GetPublisherSetNames).

This package is an A11.S03 functional preparation for A07.S01. A11.S03 stays
PARTIAL; A07.S01 is not closed and its dependencies remain in the canonical
plan. Engineering and normative acceptance are NOT_VERIFIED/NOT_PERFORMED.
Normative-system and GitHub-search development, APX and main/master are
unchanged. MORPH LAST RESORT applies; no Morph was created in this package.
