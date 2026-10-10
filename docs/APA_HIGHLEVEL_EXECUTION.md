# APA high-level model integration — draft PR #34

**Status:** source integrated; offline + synthetic E2E CI 106/106 PASS;
**Archicad 29 live creation NOT VERIFIED.**
This is an executable Python orchestration entry point, not a compiled APX nor a finished architectural project.

## Reused (not duplicated)

- `scripts/archicad_project_accelerator.py` — one high-level project intent entrypoint
- `scripts/archicad_bim_graph.py` — pinned Tapir contract, GUID dependencies, validation and topological order
- `scripts/archicad_scene_run.py` — existing one-shot guarded SceneWriter; native typed readback, project identity, SQLite journal and never-retry semantics
- `scripts/archicad_scene_v1.py` — retained pavilion compatibility
- `schemas/tapir-live-1.5.10/` — pinned modified Tapir snapshot

## First execution without Archicad

```powershell
python scripts/archicad_project_accelerator.py --intent examples/accelerator/building-shell.intent.json --output "$env:TEMP\apa-building-shell-offline-001"
```

Expected: `ACCELERATOR_COMPILED_OFFLINE` in `result.json`, `plan.json` with 25 native operations; **zero calls to Archicad and no PLN changes**. Choose a new output directory for each call.

## High-level input

`examples/accelerator/building-shell.intent.json` contains 10×8 m, two stories at 0 and +3 m, three room bays per story. All dimensions are examples, **not a calculated architectural/structural solution**.

Story bindings (`label/nativeIndex/floorId/level`) must match the sole active project exactly. Labels are architectural names (`1 этаж`, `2 этаж`), and native indexes are resolved transport identities, not floor names. Mismatch blocks before any writes.

The generator emits native Walls, Slabs, Doors and Windows. Continuous perimeter/partition walls are preserved as single BIM elements per storey; openings reference their exact parent walls. The 25 operations are not 25 building construction details.

## Live limitations and permissions

Do **not** run `--execute` on any protected project. The reused runner currently accepts only the exact legacy test PLN identity with its restrictive guard and requires a fresh explicit operator permission, preflight confirmation hash, unique run ID, and durable ledger. This PR has **no such operator permission**. No live run was performed.

Structural safety, roof, foundation, reinforced slab design, actual product layers/CSE, tested junctions, MEP, Russian building-code approval, drawing release and saving/reopening the PLN are **NOT_VERIFIED / NOT_IMPLEMENTED IN THIS INTEGRATION**. Fail-closed checks and synthetic tests cannot be represented as a building approval.

## Next integration, not another new controller

Extend this **same** executor to the already available native roof / composite / CSE / detail capabilities after verifying their exact write/readback contracts, then run a permitted disposable-project end-to-end test.

Source / task: `APA-P70.A03.S02`, draft PR #34 stacked on PR #16. Status is not DONE until full acceptance.
