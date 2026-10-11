# APA-P70.A03.S02 — PR #35: Basic Slab implementation checkpoint

**Date:** 2026-10-11. **Level:** OFFLINE_PASS; LIVE_NOT_VERIFIED; TASK_NOT_CLOSED.

**Source PR:** https://github.com/dvikt33-ux/safe-bim-layer/pull/35  
**Branch:** feature/apa-slab-basic-journaled-20261011  
**Source head:** 5c6ac03684b8d7b31bd639b58b922b49855465ba  
**CI:** https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38130324409 — SUCCESS, 113/113 offline tests PASS.

## Implemented, not yet live-accepted

- The existing building-shell-v1 optionally accepts specification.slabBasicMaterialName, a user/project-specific exact material name, not a fabricated GUID.
- Existing SceneWriter preflight resolves it through read-only GetAttributesByType(BuildingMaterial) in the exact currently open PLN. No match or ambiguous match blocks before creating elements.
- Existing SceneWriter performs CreateSlabs with durable GUID, intermediate readback of type/story/level/polygon, SQLite BASIC_MODIFY_ATTEMPTED reservation and parameters BEFORE a second native mutation.
- The second native mutation is the already available Tapir ModifySlabs; requested result is Basic structure, 0.20m and the resolved project buildingMaterialId.
- Immediate and final whole-scene readback check structureType, thickness, material GUID, story and polygon. Unknown outcome blocks; no automatic retry, delete, save, or rollback.
- Synthetic tests exercise inherited Composite 0.30m; success; missing material; ModifySlabs timeout; false native success; invalid material name.
- Existing code paths preserved. No second writer or new standalone controller.

## Critical constraints

This DOES NOT retroactively recover the partially-created scratch scene. The prior APA_Test_House_01.pln four-wall-plus-slab incident remains journal-reconciliation-blocked and must NOT be replayed. This work has not built, installed, or executed a native Add-On on the user's Windows machine. Never describe PR #35 offline test success as Archicad LIVE_PASS. Existing 25-element generic test intents that omit slabBasicMaterialName still depend on inherited defaults and are not proof of correct native Basic slabs.

## Next step

Independent review; verify installed Tapir 1.5.10 command parity; in a separately approved clean disposable PLN use material-aware intent, confirm 25 element + 2 ModifySlabs native readback and Save/reopen. Only then assess completion of P70.A03.S02, respecting dependency and owner-approval rules in canonical PROJECT_PLAN.json.

This immutable checkpoint does NOT change task status, main/master, previous PR branches, protected PLN, or installed APX.
