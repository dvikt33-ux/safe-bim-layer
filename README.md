# Safe BIM Layer v0.1

Qwen emits only the high-level `create_room` contract. `safe_bim_layer.py` owns Tapir payload construction, pinned-schema preflight, one-write-at-a-time execution, ordered read-back, requested-vs-actual diffs, host relationship checks, and fail-closed orchestration.

High-level operations:

- `create_wall_loop(contour, floor_index, height, thickness)`
- `create_basic_slab(contour, level, floor_index, thickness)`
- `insert_window(host_wall_guid, params)`
- `insert_door(host_wall_guid, params)`
- `create_room(contour, wall_height, wall_thickness, slab, door, windows)`

`CreateSlabs` schema v1.5.8 does not expose `structureType` or `buildingMaterialId`; it exposes `favoriteName`, `level`, `thickness`, `referencePlaneLocation`, polygon, and floor. The Safe BIM Layer therefore does not invent low-level values: it creates with the supported schema and fails unless read-back reports `structureType: Basic` and the requested numeric thickness.

Known limitations recorded for v0.1:

- `Tapir_ModifyWalls` may change `showOnHome false -> true`.
- The earlier slab `0.20 -> 0.30` mismatch was caused by a Composite slab, not proven thickness ignoring.
- `floorPlanPolygons` may be multi-polygon; that alone is not a wall-join failure without geometric/visual evidence.
- A failed operation stops the room transaction; v0.1 does not auto-delete partial writes.

## Collaboration workflow

The production control path is local: Qwen emits high-level intent, Safe BIM
Layer validates and verifies each Tapir operation, and Archicad is reached only
through the local bridge. GitHub is the private review boundary. Arena is used
for scoped architecture reviews and pull requests in its own branch; it never
operates a local or real Archicad project. See
[the operating model](docs/OPERATING_MODEL.md) and the
[first Arena audit brief](ARENA_TASK_ARCHITECTURE_AUDIT.md).

## Story targeting and modal safety

All Safe BIM writes that carry `floorIndex` call `GetStories`, and if needed
resolve the matching Project Map `StoryItem` with `GetNavigatorItemTree` and
activate it through the schema-supported `ChangeWindow.navigatorItemId` form.
The layer then reads `GetStories.actStory` back and refuses the write on a
mismatch. The `storyIndex`-only form is intentionally not used because it has
returned success without changing the active story in a live Archicad session.

A Tapir `TimeoutError` is classified as `UNKNOWN_OUTCOME`. The layer performs
read-only `GetElementsByType`/`GetDetailsOfElements` reconciliation and never
retries that write automatically, preventing duplicate elements.

Archicad modal confirmation is fail-closed. This project does not currently
auto-click warning dialogs: a generic title/button match is unsafe, and a
reliable text/process/button identity for the localized Archicad dialog has
not been proven in the runtime harness. Correct story activation is therefore
the primary prevention mechanism; an unexpected modal must be handled by the
operator or a separately validated Windows UI harness before a write is
allowed to proceed.

## Resumable Executor and Safe BIM Palette

`safe_bim_runtime.py` persists jobs, steps, pre-write checkpoints and state
transitions in SQLite. Supported states are `PENDING`, `RUNNING`, `DONE`,
`FAILED`, `WAITING_USER`, `UNKNOWN_OUTCOME`, `PAUSED`, and `CANCELLED`.
`DONE` requires verified read-back. A timeout becomes `UNKNOWN_OUTCOME` and is
never retried until operation-specific reconciliation proves `NOT_APPLIED`.
Every resume verifies the currently open PLN against the job's stored path.

`safe_bim_ipc.py` exposes localhost-only state and Continue/Pause/Stop actions
for the Archicad palette. The palette under `palette/` is a thin Browser Palette:
it displays Russian primary labels plus English/enum labels and never contains
BIM mutation logic. Unexpected Archicad modal dialogs remain manual: close the
dialog, then press Continue so the Python runtime reconciles before proceeding.

The palette is built against the Archicad 29 API Development Kit. This machine
currently has only the MSVC 14.51 toolset, while the Archicad 29 SDK explicitly
requires the Visual C++ 2022 v143 toolset; therefore the source/resources were
prepared and resource compilation was verified, but an `.apx` cannot be
produced or loaded until v143 is installed.

Start the Python side with a strict JSON plan:

```text
python safe_bim_service.py --plan path-to-plan.json
```

The service binds only to `127.0.0.1:19731`. A new plan remains `PENDING` until
Continue is pressed in the palette; the palette uses the most recently updated
job as `active`.

## Standalone Windows controller

The optional `controller/` panel is a separate Python/Tkinter process. It uses
the same localhost IPC and does not run inside Archicad, so it remains usable
while Archicad displays a modal dialog. Start it with:

```text
run_safe_bim_controller.bat
```

It polls state without writes, sends Continue/Pause/Stop only on button clicks,
shows `DISCONNECTED` when the runtime is unavailable, and writes a small
rotating log to `controller/logs/controller.log`. For `WAITING_USER` or
`UNKNOWN_OUTCOME`, close the Archicad dialog manually and then press Continue.
The existing `palette/` and `.apx` remain available as an alternative path.
