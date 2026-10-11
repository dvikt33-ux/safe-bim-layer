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

## 2026-10-11 user-performed live read-only reconciliation and guarded repair utility

Live diagnostic supplied by the owner using `diagnose_apa_partial_scene.py --latest-partial --port 19726` reported and printed:
- Exact open PLN `C:\\LocalAI\\APA_Test_House_01.pln`, port 19726, Tapir 1.5.10, native story index 0.
- Inventory `20 → 25` GUIDs; **five added, zero removed**.
- Four named wall operations recorded PASS; `s1-slab` marked `CREATED_UNVERIFIED`, exact GUID `BB516C6F-587B-4F51-AFCC-180291542687`.
- Slab type/story/level/polygon match, but native structure type Composite and actual thickness 0.30m, versus required 0.20m.
- `GetAttributesByType(BuildingMaterial)` returned **59** available named materials, including `Железобетон - Конструкционный` and `Бетон - Конструкционный`. The project has materials; no creation is needed.
- Evidence remains **USER_REPORTED_NATIVE_READ_ONLY**, not independently reproduced by the ChatGPT connector.

A separate **one-shot recovery utility** was published in the **same PR #35**, `scripts/repair_apa_partial_slab.py`. It is **read-only by default**. It revalidates actual 25 GUIDs versus journal, native geometry of 4 walls and slab, exact user-selected building-material name and GUID; prints a source/target-bound approval token without writes. Only a subsequent explicit `--confirm-token` makes a durable SQLite reservation before a SINGLE `ModifySlabs` call on the pinned old GUID. The utility verifies Basic structure, 0.20m, exact material GUID, native story, polygon, and unchanged inventory. A timeout or mismatch is a permanent manual-reconciliation stop with no replay.

**Current recovery status: NOT_EXECUTED_IN_ARCHICAD.** User still needs to authorize one-time mutation on the disposable project. Do not rerun the original 25-step create script.

**Latest CI:** https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38139865640 — SUCCESS, 120/120 `test_archicad_*.py` offline tests PASS. The seven additional tests cover exact partial-state preflight with zero writes, successful one-shot ModifySlabs + durable readback, invalid token blocking, unknown timeout and no retry, fake native success without real geometry correction, inventory drift, missing material.

**Task registry unchanged:** APA-P70.A03.S02 still has dependency/owner-approval gates. This is source-safe progress, not DONE_PUBLISHED or live acceptance.

## 2026-10-11 — owner-provided native repair outcome (LIVE_REPORTED)

The owner ran the one-shot recovery utility against the approved single-open disposable `C:\\LocalAI\\APA_Test_House_01.pln`, Tapir 1.5.10, local port 19726, after read-only token preflight. The copied terminal result explicitly reports:

```json
{
  "status": "SINGLE_SLAB_REPAIR_VERIFIED_UNSAVED",
  "guid": "BB516C6F-587B-4F51-AFCC-180291542687",
  "structureType": "Basic",
  "thickness": 0.2,
  "materialGuid": "63DB2CE9-903D-45C0-B93C-B3C604C77394",
  "plnSaved": false,
  "createCalls": 0,
  "modifyCalls": 1,
  "remainingSceneOperations": "NOT_EXECUTED"
}
```

**Classification:** USER_SUPPLIED / REPORTED_LIVE_READBACK. It demonstrates that the utility returned its typed readback success on the owner's Windows Archicad session. Source did **not** directly access Windows or receive independent save/reopen evidence. **The PLN remains unsaved, and the remaining 20 historical operations are NOT EXECUTED.** Historic scene ledger is deliberately not rewritten; a separate reserved repair row is the authoritative second-operation evidence. No automatic replay or scene continuation is authorized. Future work: verified, journaled continuation of ONLY remaining operations after separate explicit permission and fresh guard checks.

## Exact remaining-operation continuation, source implementation (not yet run in live Archicad)

A follow-up change to [PR #35](https://github.com/dvikt33-ux/safe-bim-layer/pull/35) added `scripts/continue_apa_partial_scene.py`, which delegates native Create calls to the **existing** `SceneWriter._execute_verified_plan` rather than introducing a competing executor. The SceneWriter was refactored to accept an independently verified prefix and perform whole-scene verification before marking completion.

Read-only continuation preflight requires: historical SHA256 evidence, exact original source graph and pinned schema, original PARTIAL journal containing four PASS walls and one CREATED_UNVERIFIED slab, matching separate READBACK_PASS slab repair record and material GUID, the unchanged 25-GUID current inventory, current typed native readback for five existing elements, valid 2-story mapping, and explicit whole-operation confirmation token. It does not repeat any old Create call. Execution is a **new** journaled suffix scene: exactly 20 Create operations, plus one ModifySlabs for the second-story slab. Every new operation is durably logged before dispatch. Final verification targets all **25 scene elements**, exact 45 native model GUIDs, expected structure/material/story and hosted opening parent GUIDs; no autosave, no rollback, no retry after ambiguous write.

- Code source head (CI-tested): `f6b7244a7cf616d9e019135091c410c04dac16d9`.
- [GitHub CI #38141606034](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38141606034) **SUCCESS: 125/125 offline tests**.
- New offline cases: 5-prefix/20-suffix/1-ModifySlabs; exact GUID and ledger preservation; token mismatch; native unknown-outcome no replay; inventory drift; tampered historical evidence.
- **Acceptance remains OFFLINE_PASS / LIVE_NOT_VERIFIED for continuation.** The user's recent live success refers **only** to the one-slab modification; no new 20 steps were executed by this assistant. A separately approved, exact-scope single-shot live trial is required.

Do not promote APA-P70.A03.S02 to DONE_PUBLISHED until its dependency/owner-approval and full live acceptance gates are met.

## Subsequent owner LIVE suffix trial: PARTIAL_OR_UNKNOWN_OUTCOME

The owner executed the separately confirmed exact 20-step suffix on `C:\\LocalAI\\APA_Test_House_01.pln`, via Tapir 1.5.10, port 19726. Read-only preflight reported `READY_FOR_EXPLICIT_TWENTY_STEP_CONTINUATION`, reusedCount=5, remainingCount=20, modelWriteAttempts=0. Owner entered `ПОСТРОИТЬ`. Native attempt returned:

```json
{
  "status":"PARTIAL_OR_UNKNOWN_OUTCOME",
  "sceneId":"apa-suffix-20261011-031123-7181b47c",
  "newCreatedCount":null,
  "reusedCount":5,
  "plnSaved":false,
  "allGuidsReadback":false,
  "reason":"ValueError: WALL_SIZE_READBACK_MISMATCH",
  "failedStep":"s2-wall-south",
  "manualReconciliationRequired":true
}
```

**Evidence class: USER_SUPPLIED, REPORTED_LIVE_PARTIAL, NOT a full model PASS.** The suffix journal has been reserved and MUST NOT be replayed. Subsequent operations are not accepted; the failing second-story south wall may already exist and possess a durable returned GUID, pending read-only reconciliation. No native parameter mismatch field can be established solely from the generic exception; do NOT assume second-story elevation cause until exact actual-vs-requested fields are read.

A new **strictly read-only** diagnostic was committed to the same PR branch:
`scripts/diagnose_apa_suffix_wall_readback.py`. It checks exact PLN/version/two-storey map, original journal + repaired slab reservation, suffix reserved scene and last failed step, current GUID inventory, and typed live GetDetailsOfElements for the failed wall; prints each requested-versus-actual geometric field plus any unjournaled GUIDs. The diagnostic refuses any write command at its transport boundary.

Source commit `35c280583cafb4829bb5929f6f679c5c7b7e2de0`; CI https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38143324357 — **SUCCESS, 126/126 offline tests PASS** including synthetic second-story native wall readback drift with read-only diagnosis and unchanged write-attempt count.

**Next gate:** owner runs only `python .../diagnose_apa_suffix_wall_readback.py --port 19726`, preserving the open unsaved scratch project and original journal. Repair or continuation must be grounded in this output, separately authorized and single-shot. No automatic retry, save, rollback, or write has been attempted by ChatGPT.
