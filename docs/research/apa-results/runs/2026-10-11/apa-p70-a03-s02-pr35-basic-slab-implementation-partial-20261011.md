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

## Subsequent read-only diagnostic: second-story Z false-positive and 8/25 prefix

Owner's 2026-10-11 read-only diagnostic against the same exact unsaved disposable PLN, port 19726, returned:
- `READ_ONLY_SUFFIX_DIAGNOSIS`; native inventory **28** = original 20 + earlier 5 + new suffix 3, zero removed or unjournaled suffix GUIDs.
- First suffix PASS `s1-partition-1` GUID `E66B647F-885B-4D32-8D47-30960A388426`, PASS `s1-partition-2` GUID `572A37D0-6CEA-42F9-A836-2C1AE43A7812`.
- Created-but-unverified second-floor `s2-wall-south` GUID **`66B28F44-FAAF-404B-BEB7-83CF48BEBB02`**.
- Wall is native story `1`, Basic, height 3m, thickness 0.3m, correct X/Y endpoints/offset/arc; **only** reported mismatch: submitted `zCoordinate=0`, native details `zCoordinate=3`.
- The actual story is at elevation **+3.0m**. This is the expected global native Z for a wall with a 0m story-local offset. No correction or wall move is warranted.

Root cause is **readback coordinate-frame error**, not demonstrated geometry error. The old implementation compared local wall `zCoordinate` to absolute native `GetDetailsOfElements.zCoordinate` for nonzero stories.

Source patch in [PR #35](https://github.com/dvikt33-ux/safe-bim-layer/pull/35) now passes exact pinned `GetStories` elevation through SceneWriter, hosted wall checks, final whole-model readback and existing Project Accelerator. It verifies `nativeZ = storyLevel + requestedLocalZ` (for the observed AC29 native contract) and fails closed when no unique nonzero-story binding exists.

A narrowly scoped second recovery script `scripts/continue_apa_after_story_z.py` follows the original immutable 20/5/3 provenance, historical SHA256 manifest, verified slab repair, first suffix partial journal with exactly two PASS partitions and one CREATED_UNVERIFIED south wall, exact 28 present native GUIDs and typed readback of all eight existing planned elements. **Read-only default** returns a fresh explicit token; after separate owner confirmation it reuses the *same* SceneWriter for **only 17 missing** Create operations, durable per-operation journal and 25-element final typed readback. It never replays earlier reserved suffixes or alters old operation states.

**GitHub CI:** https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38143964970 — **SUCCESS, 136/136 offline tests PASS**, including an 8-element verified prefix → 17 new operations → full synthetic 25-element acceptance and fail-closed Z-drift, journal-replay and inventory-drift cases.

**Status remains:** past slab REPORTED_LIVE_PASS_UNSAVED; attempted previous suffix REPORTED_LIVE_PARTIAL; second Z fix / 17-op continuation OFFLINE_PASS only; actual save/reopen and full Archicad model remain NOT_VERIFIED. **Do not use old `ПОСТРОИТЬ` token or old continuation script again.** No protected PLN, main, installed Add-On or existing protected PR branches were changed by these source commits.

## Live 17-step suffix: PARTIAL on second-storey slab; read-only diagnostic published

After a clean read-only preflight `READY_FOR_EXPLICIT_SEVENTEEN_STEP_CONTINUATION` confirmed 8 existing GUIDs and 17 missing, owner explicitly approved `СОЗДАТЬ17`. The live Archicad 29 trial, exact disposable `C:\\LocalAI\\APA_Test_House_01.pln`, Tapir 1.5.10 at port 19726, returned:

```json
{
  "status": "PARTIAL_OR_UNKNOWN_OUTCOME",
  "sceneId": "apa-suffix3-20261011-031123-7181b47c",
  "reusedCount": 8,
  "newCreatedCount": null,
  "allGuidsReadback": false,
  "failedStep": "s2-slab",
  "reason": "ValueError: SLAB_READBACK_MISMATCH",
  "plnSaved": false
}
```

**Classification: USER_SUPPLIED / REPORTED_LIVE_PARTIAL.** This log does *not* prove the third suffix completed. Further elements may already exist. Do **not** repeat any earlier suffix or run a new create workflow until this third suffix journal is reconciled. The live native slab's GUID, journal phase (CREATED_UNVERIFIED vs BASIC_MODIFY_ATTEMPTED), actual level and thickness are **not established by the generic exception**; do not assume a story-level mismatch yet.

Source update: `scripts/diagnose_apa_suffix3_slab_readback.py` on PR #35 is strict READ ONLY, with command allowlist limited to GetProjectInfo, GetStories, GetAddOnVersion, GetAllElements and GetDetailsOfElements. It validates the original and prior two suffix journal structures, lists third suffix operations and GUIDs, compares inventory with the original 28 verified GUIDs, and prints the *actual* s2-slab native story/type/thickness/level/globalZ/polygon/material fields alongside requested local level and pinned story absolute elevation. No Create, Modify, Save, rollback or automatic retry is attempted.

GitHub source commit `876d697ab8abf97d5aa104dda613259c7ad2105e`; [CI #38144329697](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38144329697) **SUCCESS, 137/137 offline tests PASS**, including a synthetic second-storey slab readback-frame mismatch reproducer and proof that diagnosis adds zero writes.

**Next gate:** user runs only the read-only third-suffix diagnostic in the same open unsaved PLN. Any fix must be gated on that evidence and use a *new* uniquely reserved durable scene, preserving all existing GUIDs and old journals. P70.A03.S02 still NOT_DONE; never equate CI success with live completed BIM or save/reopen.

## Live third suffix s2-slab diagnostic: real misplaced Composite at global Z=0

Owner supplied exact read-only diagnostic against approved disposable `C:\\LocalAI\\APA_Test_House_01.pln`, Tapir 1.5.10, port 19726. The result reports **32 total** = preexisting 20 + original recovered 5 + first suffix 3 + third suffix 4; zero missing GUID and zero unjournaled creations.

Third scene journal `apa-suffix3-20261011-031123-7181b47c`: `s2-wall-east` PASS GUID `C78C8979-0231-40A8-9C7E-6193237E7CB6`; `s2-wall-north` PASS GUID `ADFC2BCB-D90E-428C-BCB6-8ED1E5E7DC6E`; `s2-wall-west` PASS GUID `73B3FC6E-0168-4F9B-9919-B05EB8C9D44A`; `s2-slab` CREATED_UNVERIFIED GUID **`1020BDF5-AFEC-455E-BAB9-D17999AC1567`**.

Native slab readback: native story index **1** at +3m, actual slab `zCoordinate=0`, story-relative `level=-3`, structure **Composite**, thickness **0.30m**, expected position **global +3m**, Basic **0.20m**. Polygon coincides, `referencePlaneLocation=Top`. Therefore this is a **true generator-placement/defaults defect**, not just a readback-coordinate frame mismatch. Do not mark slab geometrically correct, do not simply relax the verifier, and do not retry any previously reserved scene.

Code remediation added `scripts/repair_apa_suffix3_slab.py` on PR #35. Read-only preflight requires exact original 20/5/3/4 journaling and 32 unchanged native GUIDs, rechecks all previous walls, first repaired slab and pinned story elevations, then resolves user-chosen exact material. Only owner confirmation triggers **ONE** durable journal-reserved `ModifySlabs` for the specific existing GUID, requesting `zCoordinate=3.0`, Basic, 0.20m and the exact existing buildingMaterialId. Readback checks absolute Z +3m, story-relative level 0m, polygon, thickness, material, floor and unchanged 32 GUID inventory. No recreate, save, retry or automatic cleanup.

**New code status:** [CI #38145083946](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38145083946) **SUCCESS, 148/148 offline tests PASS**. No live mutation has been performed by this newly authored recovery tool yet. A previous CI run on intermediate commit failed due to a synthetic GUID fixture mismatch and was corrected; final tested head `e17a25a4ef482db8a4136bca736da7f4f8b8c8c1`. **Remaining original building scene steps: 13** (12 existing built planned elements + 13 missing). A future fourth suffix requires separate journal proof, write confirmation and retest.

## LIVE reported: second-floor slab repaired at +3m (owner readback)

The owner reported successful execution of the one-time exact-GUID slab recovery on disposable `C:\\LocalAI\\APA_Test_House_01.pln` through local Tapir port 19726. CLI outcome:

```json
{
  "status":"S2_SLAB_REPAIRED_VERIFIED_UNSAVED",
  "guid":"1020BDF5-AFEC-455E-BAB9-D17999AC1567",
  "floorIndex":1,
  "zCoordinate":3,
  "localLevel":0.0,
  "thickness":0.2,
  "structureType":"Basic",
  "buildingMaterialId":"63DB2CE9-903D-45C0-B93C-B3C604C77394",
  "createCalls":0,
  "modifyCalls":1,
  "plnSaved":false
}
```

**Evidence class: USER_SUPPLIED / REPORTED_LIVE_TYPED_READBACK, unsaved and not reopened.** This verifies in-session correction only, not full live 25-element creation, not persistent PLN save/reopen. Current in-memory model should be **32 total (20 original + 12 planned)**; this inventory still needs fresh native readback before new writes.

## Fourth prefix-safe source implementation: exact 13 pending creates

New source script `scripts/continue_apa_after_s2_slab.py` in [PR #35](https://github.com/dvikt33-ux/safe-bim-layer/pull/35) provides a default strictly read-only preflight for the sole authorized historical scratch PLN. Revalidates:

- original SHA256 evidence and pinned 25-step, 2-story historical graph; no graph rewrite;
- previous three immutable, partial Create scene ledger states (5 + 3 + 4), two separate `READBACK_PASS` slab repair reservations, and exact repair intent/token/result provenance;
- reconstructed second and third suffix approval hashes, not simply state labels;
- exact current 32 GUID inventory, with no unexpected or missing GUIDs;
- typed native readback of all 12 existing model elements, including second-floor walls at +3m and both slabs with correct Basic structure, 0.2m thickness, material GUID, local level 0 and absolute elevation.

For a separately confirmed new approval token ONLY, the utility calls existing `SceneWriter._execute_verified_plan` with seeded 12 GUIDs and a **new fourth scene id** to create only the remaining **13** elements, with per-write durable ledger and fail-closed stop on any native error. Final acceptance verifies all 25 generated elements plus expected model inventory 45, all hosted parent GUIDs, and slab story elevation. No auto-retry, no Save, no delete or rollback. Any failure requires read-only ledger reconciliation, not replay.

**Source CI:** https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38145934082 — **SUCCESS; 159/159 offline tests PASS**. Synthetic test cases include 12+13 success, no duplicate GUIDs, exact approval required, unexpected native inventory, second-floor slab Z drift, interrupted fourth suffix cannot be replayed. Earlier intermediate CI failures in synthetic fixture due to repeated mock GUIDs were corrected; last PASS is the acceptance basis.

**Current task:** APA-P70.A03.S02 remains INCOMPLETE / LIVE_FULL_MODEL_NOT_VERIFIED / requires controller approval. The live construction of remaining 13 elements is not yet performed. Generic future two-floor slab generator still has a coordinate-frame defect: it initially created second-floor Slab at global 0. A future separately accepted generator fix must not mutate the immutable historical graph or weaken native verification.
