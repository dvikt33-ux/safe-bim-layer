# Authored native APA core

`apa-authored-project/1` joins the existing Semantic Brief, Project Library Pack,
authored native geometry, BIM Graph and SceneWriter. The canonical graph remains
the single execution plan. The isolated binding is the user-authorized
`C:\LocalAI\APA_Isolated_Writer_Test_01.pln`; identity is read before compilation
and at operation boundaries.

The examples contain explicit approved layout, named/native story bindings and
provisional library selections. `isolated-authored-project.json` is the initial
ten-element shell. `isolated-authored-building.json` includes eight walls, two
slabs, two columns, one door and four hosted windows. Optional
`wallBasicMaterialName` resolves an exact native BuildingMaterial name;
`nativeComponents` permits only columns and hosted doors/windows. Unsupported
commands, invalid graphs, missing stories or out-of-footprint columns block.

For a fresh authorized empty region, preflight is read-only:

```powershell
python scripts/archicad_project_accelerator.py --intent examples/accelerator/isolated-authored-building.json --isolated-port 19724 --preflight --output <new-evidence-directory> --data-dir <stable-journal-directory>
```

Execute adds `--execute --run-id <unique-id> --confirm-plan-hash <preflight-hash>`
instead of `--preflight`. Never replace the durable journal to retry. The example
building already exists in the acceptance PLN from 2026-10-11: do not replay it.
Native execution leaves saving explicit and returns COMPLETE_UNSAVED.

`archicad_authored_extension.prepare/execute` accepts a complete verified prior
plan and owned GUID mapping. It permits only an explicit wall material change
plus new columns/openings, verifies source geometry and unowned spatial
clearance, persists an intent before ModifyWalls, and delegates remaining creates
to the same SceneWriter using the verified prefix. It never recreates that prefix.

`prepare_opening_width/execute_opening_width` edits one existing door/window.
Preparation validates the proposed graph and reads the entire source model.
Execution checks the matching token, reserves the operation durably, repeats
identity and baseline checks, modifies the existing GUID once, and verifies all
geometry, materials, host/story bindings, inventory and column ownership.
Restoration is a separate explicit operation against the verified changed plan.
Any ambiguous result stops; automatic replay is forbidden.

GetAllElements includes ColumnSegment GUIDs. Acceptance counts them only when
GetSubelementsOfHierarchicalElements proves their direct column ownership; an
unrelated extra GUID still fails. CreateSlabs uses absolute project Z whereas
slab detail `level` is story-relative and `zCoordinate` is absolute. Wall write Z
is story-relative, with absolute native readback.

Native evidence proves an explicit small building and bounded incremental edit.
It does not establish automatic planning, arbitrary libraries, structural or
normative acceptance, junction quality, roof/stair/MEP completeness, visible UI
quality or Archicad30 support. Save/reopen acceptance harnesses and immutable raw
records are published separately on the canonical APA results branch.
