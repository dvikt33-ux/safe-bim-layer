# APA-P70.A03.S02 — owner read-only isolated PLN baseline (port 19724, 20 elements)

**Status:** USER_SUPPLIED_LIVE_READ_ONLY_PREFLIGHT_PASS for exact project identity, story/material inventory; **SPATIAL_CLEARANCE_NOT_VERIFIED**; **NATIVE_WRITES_NOT_AUTHORIZED**. 2026-10-11. Controller task remains PARTIAL.

## Evidence: two Archicad processes and exact project binding

Owner ran GetProjectInfo read-only against ports 19723/19724 after 19726 refused earlier connections, with results:
- `19723`, PID `75280` — `C:\\LocalAI\\SafeBIM_Global_Library_Test_Projects\\APA_SyncGuids_2213_REOPEN_CHECK.pln`, **not target**. This project must not receive any APA test writes.
- `19724`, PID `96948` — `C:\\LocalAI\\APA_Isolated_Writer_Test_01.pln`, exact target; `projectUnchanged=true` after GET operations; current native `actStory=0`.
- `GetStories`: index `0` floorId `1` name `Первый Этаж` level `0`m height `3`m; index `1` floorId `2` name `""` level `3`m height `3`m; index `2` floorId `3` name `""` level `6`m height `3`m.
- `GetAttributesByType(BuildingMaterial)`: single `Железобетон - Конструкционный`, index `10`, GUID `63DB2CE9-903D-45C0-B93C-B3C604C77394`.
- **`GetAllElements`: `elementCount=20`.** Important: "newly saved" is **NOT equivalent** to an empty Archicad element inventory. Types, actual spatial bodies, bounding boxes and whether these 20 objects intersect the new authored scene envelope are not yet known.
- `nativeWriteCalls=0`; no current-model mutation, no Save, no new SceneWriter journal reservation.

## Interpretation and required next gate

Connectivity is established. Previous `WinError 10061` on 19726 was a stale socket; don't repeat port discovery unless runtime changes. We MUST NOT treat the existing 20 elements as empty, nor assume that they are safe template annotations. Existing `scripts/archicad_scene_run.py::scan_for_existing_geometry` already supports batches of 3D bounding boxes, nonspatial typed classification, explicit XY/Z envelope intersection and fail-closed behavior. Use that same read-only scanner or first list types/boxes on the exact port `19724`, anchored to actual authored scene envelope, with GetProjectInfo checked before and after. If bodies intersect, find a separate approved placement or fresh empty project; **do not delete anything automatically**. If all 20 turn out to be nonspatial/clear, record their exact verified classification and use unchanged SceneWriter.

The existing writer is currently hard-coded to a DIFFERENT historic scratch PLN `C:\\LocalAI\\APA_Test_House_01.pln`. Never swap that constant or patch global guards merely to bypass checks; future specific-target support requires explicit and auditable exact-path allowance, one-shot unique scene ID, pinned plan hash, durable SQLite before EACH native call, owner approval for the particular run and typed GUID/material/Z readback. The previous 45-GUID saved evidence `C:\\институт проект\\Улучшенная копия APA_Test_House_01.pln` and SyncGuids project at 19723 remain protected.

**Acceptance:** ONLY read-only identity/story/material/inventory PASS. No new code CI is asserted in this report, and full `APA-P70.A03.S02` remains PARTIAL. No Work session.
