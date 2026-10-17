# APA AC29 — reuse existing native CREATE/MODIFY verifiers

**Branch:** feature/apa-ac29-existing-create-verifiers-20261017  
**Review:** draft PR #149, based on PR #148.  
**Target runtime:** Archicad 29 build 5101, Tapir 1.5.10.

## Why this work exists

The shared registry previously contained only two code-owned contracts: `CreateColumns: CREATE` and `MoveElements(copy=false): MODIFY`. The existing APA already had family-specific typed readback in `archicad_connected_components.NativeAdapter` and `archicad_scene_run.verify_readback`. The gap was exposing bounded pre/post callbacks to the same original `DynamicCommands.run_workflow -> SceneWriter`. No second writer, transport, router or scheduler was introduced.

## New source-owned entries (CI only until native acceptance)

| Contract | Native rule reused | Explicit limits |
|---|---|---|
| `CreateBeams: CREATE` | `NativeAdapter('CreateBeams').verify` for typed axis, profile, material and BeamSegment | One source-pinned straight horizontal, axis-aligned Basic rectangular Beam, floor 0, one owned BeamSegment; source/destination collision guard; real closed segment BREP |
| `CreateWalls: CREATE` | `archicad_scene_run.verify_readback('CreateWalls', ...)` | One Basic straight axis-aligned Wall, floor 0, explicit Center reference line/material; no host/body intersections; real closed BREP |
| `CreateRoofs: CREATE` | `NativeAdapter('CreateRoofs').verify` for single-plane pivot/angle/material | One single-plane Basic Roof, floor 0, explicit pivot/angle/thickness, no eaves or arcs/holes, conservative 3D envelope and intersection guard, actual closed BREP |
| `ModifySlabs: MODIFY` | Original `SceneWriter` per-step full retained BREP, typed `GetDetailsOfElements` and `ROOF.geometry_signature` | One already Basic standalone Slab on story 0. Material change **only**: no thickness, level, polygon, holes, host/child change; exact typed and physical material readback, unchanged geometry |

The existing `CreateColumns` and `MoveElements(copy=false)` contracts remain intact. The new registry contains **six code-owned contract entries**. This is not a claim that six commands were newly LIVE-verified. The preflight fails closed on unexpected parameters, unknown native GUIDs/materials, malformed bodies, intersections or unsaved model drift.

## A verified incompatibility: CreateSlabs

The current, committed `schemas/tapir-live-1.5.10/tapir-scene-live.json` shows that `CreateSlabs` lacks `structureType` and `buildingMaterialId` properties. `ModifySlabs` accepts both. Therefore `CreateSlabs` is **not** registered as a generic source-qualified CREATE in this PR. Do not pass unsupported fields, rely on opaque Archicad favorites/defaults, or claim a Basic material before independent readback. A safe composite CREATE+MODIFY pipeline is a later separately scoped task and needs verified initial defaults and a never-replay checkpoint.

## Deployment and evidence

- Focused original dynamic scope tests and only new source/registry/material verification tests in Linux and Windows CI.
- Check real Tapir export property keys directly in tests, not guessed schema.
- **No live model writes, no new approval/grant, no installation** in this PR. The installed release remains `9cfe84c` as last reported, with 298 GUID in the BDD working project. Do not replay previous UNKNOWN copy/150 batch scenes.
- No main change, no Archicad 30, no Arena or separate service.

## Next acceptance

Update the existing APA receiver in place using its audited `update_from_checkout` process, with exact local file/source hashes and the 298-GUID working baseline, but only after preparing and checking an upgrade manifest. Validate read-only registry import first, then native acceptance on an explicitly authorized isolated test PLN. No BDD writes by this release task.
