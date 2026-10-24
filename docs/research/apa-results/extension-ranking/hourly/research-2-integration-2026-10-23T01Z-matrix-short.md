# APA №2 — BUILD-01: матрица интеграции 01Z

Все SOURCE_ONLY; баллы — экспертный приоритет, не benchmark. OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0.

| ID | P | G | Готовый путь и критерий |
|---|---:|---|---|
| I01 | 99 | G0 | Windows Process Modules + SHA256 загруженного APX; DONE: PID/порт/PLN/SHA. |
| I02 | 100 | G0 | PR162 probe_runtime / IsAddOnCommandAvailable; DONE: команды и installed schema. |
| I03 | 97 | G1 | PR34/74 GetStories, nativeStoryBindings; DONE: два floorId/index/Z, DAG hash. |
| I04 | 100 | G2 | PR74 CreateSlabs→ModifySlabs; DONE: оба Basic Slab material/Z after reopen. |
| I05 | 96 | G2 | PR74/82/149 Walls/Beams/Columns/Roof; DONE: GUID/type/story/material/BREP. |
| I06 | 98 | G2 | PR74/131 Doors/Windows ownerWallId; DONE: host GUID and Wall BREP. |
| I07 | 98 | G3 | GetAllElements databases+errors; DONE: all stories and DB results complete. |
| I08 | 75 | G3 | PR126 batch, PR162 groups; DEFER; DONE: unique GUIDs, no replay. |
| I09 | 100 | G4/5 | Save/Close/Open + custom GetModelDumpV1; DONE: 2 distinct native models/readbacks. |

Source versions: Tapir pinned 1.5.10 export (installed NOT VERIFIED), MIT upstream; Archicad proprietary. Custom SDK license NOT_FOUND. Minimum new writer/router = 0. Gate path: SOURCE→OFFLINE→BUILD if required→INSTALLED→authorized LIVE→independent ACCEPTED.
