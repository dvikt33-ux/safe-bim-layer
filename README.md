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
