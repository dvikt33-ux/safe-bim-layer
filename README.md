# Working Archicad MVP

This branch contains the working Archicad Model Dump v1 reader and six small,
geometry-derived create/read-back/delete cycles. The Python tools use only the
standard library. They talk to the Tapir JSON API on `127.0.0.1:19723`.

## Start Archicad and open the project

1. Start Archicad 29.
2. Manually open the one intended test PLN in Archicad. The MVP never opens,
   switches, or saves a project for you.
3. Ensure the Tapir add-on with Model Dump v1 is loaded. It exposes the local
   JSON bridge at port `19723` while Archicad is running.

## Build and load the Model Dump add-on

The native command is an overlay on the stock Tapir add-on. It copies a Git
snapshot into the build directory, adds `GetModelDumpV1` registration there,
and leaves the supplied Tapir checkout unchanged. The verified source ref is
Tapir commit `d2dfeec`.

```powershell
git clone https://github.com/ENZYME-APD/tapir-archicad-automation.git C:\src\tapir
$tapir = 'C:\src\tapir'
$devkit = 'C:\Graphisoft\Archicad 29 DevKit\Support'
python .\archicad-addon\Examples\build_model_dump.py `
  --tapir-repo $tapir --ref d2dfeec --devkit $devkit `
  --build "$env:TEMP\safe-bim-mvp-build"
```

In Archicad Add-On Manager, load
`%TEMP%\safe-bim-mvp-build\build\TapirAddOn_AC29_Win.apx`. Restart Archicad
if replacing an already loaded Tapir add-on. Do not load two Tapir builds in
the same Archicad instance.

## Read the current model

With the intended PLN open and the add-on loaded, run:

```powershell
python .\archicad-addon\Examples\model_dump_v1.py `
  --port 19723 --out "$env:TEMP\safe-bim-mvp\model-dump.json"
```

The client writes normalized JSON, the raw native response, the request, and
metrics beside the output file. A compact one-Morph excerpt is checked in at
[examples/model_dump_v1.sample.json](examples/model_dump_v1.sample.json); it is
a subset of a live dump, not a full project dump.

## Run a temporary write cycle

Write cycles create an element from the current model geometry, read it back,
and delete the returned GUID. Keep the intended test PLN open. Cycle evidence
goes to `%TEMP%\safe-bim-mvp-evidence` by default; set
`$env:SAFE_BIM_MVP_EVIDENCE` to choose another local directory.

```powershell
python .\scripts\archicad_write_cycles\wall_joint_cycle.py
python .\scripts\archicad_write_cycles\wall_material_cycle.py
python .\scripts\archicad_write_cycles\hosted_window_cycle.py
python .\scripts\archicad_write_cycles\hosted_slab_cycle.py
python .\scripts\archicad_write_cycles\hosted_roof_cycle.py
python .\scripts\archicad_write_cycles\hosted_morph_cycle.py
```

## Verified operations

| Operation | Result |
| --- | --- |
| Model Dump v1 | PASS |
| Geometry-aware Wall create and joint | PASS |
| Wall material inheritance and write | PASS |
| Hosted Window placement | PASS |
| Slab geometry and material | PASS |
| Roof geometry create/read-back/delete | PASS |
| Roof surface-material write | Known blocker: current native command surface does not write a single-plane Roof surface override |
| Morph geometry create/read-back/delete | PASS |

The Roof surface-material blocker is recorded separately and is not modified
by this MVP.

## Request-driven executor

`scripts/archicad_executor.py` runs one structured request per invocation. It
always reads a fresh Model Dump first. `dry-run` returns the calculated native
command and parameters without changing the model. `execute` creates the
element and leaves it in the open model. `delete` removes only the GUID named
in that request.

Supported actions are `create_wall`, `change_wall_material`, `create_window`,
`create_slab`, `create_roof`, `create_morph`, and `delete`. For chained Walls,
pass the prior created GUID as `sourceGuid`; the next invocation derives its
start point and direction from that Wall's fresh reference line.

Example request (`request.json`):

```json
{
  "action": "create_wall",
  "mode": "execute",
  "instruction": "Continue the selected wall",
  "sourceGuid": "GUID-FROM-A-PRIOR-RESPONSE",
  "length": 1.0
}
```

Run it from the repository root:

```powershell
python .\scripts\archicad_executor.py .\request.json
```

Use `"mode": "dry-run"` to calculate without creating. A create response
contains `createdGuid`, `sourceGuids`, derived geometry, and read-back
verification. Example response:

```json
{
  "status": "PASS",
  "action": "create_wall",
  "createdGuid": "NEW-GUID",
  "sourceGuids": ["SOURCE-GUID"],
  "geometry": {"start": {"x": 10.0, "y": 4.0}, "end": {"x": 11.0, "y": 4.0}},
  "verification": {"jointDistance": 0.0, "homeStoryMatches": true, "pass": true},
  "retained": true
}
```

To remove a retained element, submit a separate request:

```json
{"action":"delete","mode":"execute","guid":"GUID-FROM-RESPONSE"}
```

Each invocation writes its fresh dump and native API evidence under
`%TEMP%\safe-bim-mvp-evidence\executor` by default. No dump or evidence is
written into the repository.

## Plain language adapter

The thin `scripts/archicad_chat_executor.py` adapter reads a fresh dump,
translates a small set of Russian instructions into an `archicad_executor.py`
request, then returns its read-back result. It currently translates Wall
continuations and Slab creation. Window placement returns `NEEDS_SELECTION`
with Wall GUID candidates because this instruction alone does not identify a
host in a large model.

```powershell
python .\scripts\archicad_chat_executor.py "Продолжи последнюю созданную стену ещё на 1 метр."
python .\scripts\archicad_chat_executor.py '{"instruction":"Продолжи последнюю созданную стену ещё на 1 метр","mode":"dry-run"}'
```

For “last created Wall”, the adapter uses the unique short straight Wall whose
begin point joins one collinear predecessor and whose end remains open. It
returns `NEEDS_SELECTION` when the current geometry does not yield one unique
candidate. It does not use the element array order as creation time.


## Series 178-07sm.86 typical-floor MVP

The first pass for the photographed Series 178 typical floor is deliberately a
structural skeleton, not a claim of exact factory-panel reconstruction. The
checked-in spec preserves the verified grid `23.4 x 13.2 m`, the
`3.0/3.6 m` X modules and `5.4/2.4/5.4 m` Y modules. Panel marks, exact
openings, partitions, stair and balcony geometry remain provisional until the
next visual/read-back pass.

Dry-run first:

```powershell
python .\scripts\archicad_series178_typical_floor.py
```

Create the skeleton in the one currently open Archicad project:

```powershell
python .\scripts\archicad_series178_typical_floor.py --execute
```

Use `--story-index`, `--origin-x` and `--origin-y` if the test floor must be
placed on another story or away from existing geometry. The builder never
opens, switches, saves or closes a PLN. It refuses a matching pre-existing
skeleton, creates the slab first, verifies it, then creates the wall batch and
performs a fresh Model Dump read-back before returning `PASS`.


## Live change watcher over Tapir

`scripts/archicad_change_watch.py` provides a read-only polling watcher for the
currently open Archicad project. It does not open, switch, save, close, select,
create, modify or delete model elements. The watcher polls standard Tapir
commands and reports element additions, removals and changes detected from
type/details/floor/bounding-box fingerprints.

For the current Series 178 test project on port `19725`:

```powershell
python .\scripts\archicad_change_watch.py --port 19725 --interval 1.0 --expect-project-substring "SafeBIM_Global_Library_Test_Projects"
```

Stop it with `Ctrl+C`. A current snapshot and append-only change log are kept
under `%TEMP%\safe-bim-mvp-evidence\archicad-watch`.

This is polling, not an Archicad event subscription. It detects structural and
geometric changes visible through standard Tapir `GetDetailsOfElements` and
`Get3DBoundingBoxes`; changes outside that response surface may require the
native Model Dump bridge for deeper detection.


To turn the watch log into compact dispatcher/chat context, use:

```powershell
python .\scripts\archicad_watch_context.py --port 19725 --tail 20
```

The output contains the current project identity, active story, live element
count, story table, and the latest add/remove/change events. This is the bridge
between the continuously running local watcher and the next command-planning
step: a local dispatcher can call this helper before every requested Archicad
operation and include the returned JSON as current model context without
regenerating the 100 MB native Model Dump.


## Series 178 v0.2 — central stair visual pass

After the direct 29-element skeleton has been created and its manifest exists at
`%TEMP%\series178-direct-19725-created.json`, the next guarded pass creates
exactly one provisional Stair in the verified central `3.6 m` bay. It uses
standard Tapir commands only and refuses to run if the project, active story,
skeleton GUID set, or prior v0.2 stair state do not match.

Dry-run:

```powershell
python .\scripts\archicad_series178_v02_stair.py --port 19725
```

Execute after inspecting the plan:

```powershell
python .\scripts\archicad_series178_v02_stair.py --port 19725 --execute
```

The Stair dimensions in this pass are explicitly provisional visual
reconstruction values. The script records the returned GUID immediately under
`%TEMP%\safe-bim-mvp-evidence\series178-v02\stair.json`, reads the Stair
back through Tapir, and never saves the PLN. Keep
`archicad_change_watch.py` running in another terminal so the addition is
independently visible in the live event stream.

## Archicad native-element minimality rule

This rule applies to all Archicad generation tasks in this repository.

- Use the **minimum number of native BIM elements** needed to represent the intended building geometry.
- One continuous physical wall run is modeled as **one Archicad Wall** whenever the geometry and construction actually remain continuous.
- A door or window never justifies splitting a wall into multiple wall fragments. Create a native hosted **Door** or **Window** in the continuous Wall.
- Split a Wall only where the real construction changes: wall ends, corners, a true gap, a change of geometry, thickness, structure/material, story behavior, or another property that cannot be represented by one Wall.
- Prefer native Archicad tools for the object being modeled: Wall, Door, Window, Slab, Roof, Stair, Column, Beam, Opening, Railing, Zone, Dimension, etc.
- Do **not** imitate BIM geometry with Lines, Polylines, Arcs, Hatches, Morphs, or extra Wall fragments when a dedicated native tool can represent it.
- Do not create helper BIM elements solely to obtain dimension witness points. Dimensions should reference the real model elements whenever the bridge supports it.
- Reuse a host element for all of its hosted openings instead of creating duplicate or overlapping hosts.
- Before execution, simplify the planned element graph: merge collinear/continuous runs that have identical properties and confirm that every remaining split has a construction reason.
- Acceptance criterion: if two adjacent elements could be replaced by one native Archicad element without losing real geometry, semantics, hosted relationships, or required properties, the two-element solution is rejected as unnecessarily fragmented.

In short: **minimum BIM element count, maximum native Archicad semantics**. Openings belong inside hosts; they are not modeled as gaps assembled from host fragments.
