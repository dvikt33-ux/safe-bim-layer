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

## Fourth-suffix live preflight blocked safely: active story mismatch

User executed read-only `continue_apa_after_s2_slab.py --port 19726 --material "Железобетон - Конструкционный"` after fetching PR #35 source head `db064af4566a350f7ffbd46900ad6158845a161a`. The CLI reported:

```json
{"status":"BLOCKED","reason":"ValueError: STORY_MISMATCH: active story must match pinned binding","modelWriteAttempts":0}
```

**Interpretation:** active native story at the time of this preflight did not match the pinned test-story index **0**. This is a safety guard, not evidence of changed BIM geometry or a failed create operation; no Create/Modify calls were attempted by this script. Since PowerShell was still prompting for approval despite a prior `throw` (separately pasted commands), the correct immediate action is **cancel Read-Host using Ctrl+C**, not approve. Set the active tab/story to first floor (index 0, elevation 0) in the **same** open PLN; then rerun **read-only preflight only** and verify `READY_FOR_EXPLICIT_THIRTEEN_STEP_CONTINUATION` and zero writes. Do not reuse earlier approval tokens and do not alter original journals or run any create command before successful fresh preflight.

**Current status:** 12/25 historical planned elements REPORTED LIVE verified; fourth suffix NOT_STARTED; file still unsaved; no automatic replay. Do not close or switch the PLN. Future automation of UI-level story activation remains outside scope and should not be invented in this source-safe workflow.

## Live fourth-suffix read-only preflight succeeded after selecting bound story

Owner activated the required first story in the *same* open Archicad 29 test PLN and reran read-only `continue_apa_after_s2_slab.py --port 19726 --material "Железобетон - Конструкционный"`. Observed result:

```json
{
 "status":"READY_FOR_EXPLICIT_THIRTEEN_STEP_CONTINUATION",
 "binding":{"path":"C:\\LocalAI\\APA_Test_House_01.pln","name":"APA_Test_House_01","port":19726,"tapirVersion":"1.5.10","storyIndex":0},
 "sceneId":"apa-suffix4-20261011-031123-7181b47c",
 "reusedCount":12,
 "remainingCount":13,
 "modelWriteAttempts":0
}
```

**Evidence class USER_SUPPLIED / REPORTED_LIVE_PREFLIGHT_PASS.** The approval token is intentionally omitted from the durable report. No fourth-suffix Create was performed in this preflight; native full-scene results remain unverified and PLN unsaved. The previous `STORY_MISMATCH` is resolved for this read-only call, but a fresh execution must revalidate identity before native writes. Advise explicit user approval for 13 creates; after any partial/unknown outcome, NO blind retry.

## Fourth-suffix approved live execute returned transport timeout; write outcome UNKNOWN

After the previously reported read-only fourth preflight PASS (12 previous GUIDs / 13 planned new), the owner explicitly ran the one-shot fourth suffix command in the same Archicad 29 scratch PLN on Tapir port 19726. The exact externally reported output:

```json
{"status":"BLOCKED","reason":"TimeoutError: timed out","modelWriteAttempts":0}
```

**Do not interpret the displayed `modelWriteAttempts:0` as a measured zero.** Source audit found that the fourth-suffix `main` outer exception handler hardcoded this value **unconditionally**. Depending on where the timeout escaped, there may be no fourth-scene reservation and zero created elements OR there may be a reserved/partially created fourth scene. **LIVE_STATUS = TIMEOUT_UNKNOWN; no repeat, no save/undo/delete.** The original approval token is not reusable for a blind execute.

A new strictly READ ONLY utility `scripts/diagnose_apa_suffix4_timeout.py` is published on PR #35. Its default `--journal-only` performs **zero Archicad calls**, inspects the local historical SHA256 evidence and SQLite journal in `mode=ro`, checks the original 20+12 provenance and two repaired-slab markers, and reports whether the fourth suffix was ever reserved; any created or ambiguous recorded steps and GUIDs are included. Optional `--with-native` performs **only** allowlisted GET calls (GetProjectInfo, GetAddOnVersion, GetStories, GetAllElements, GetDetailsOfElements) and reports whether any original 32 GUIDs vanished, new native GUIDs exist without journal rows, or fourth-suffix registered GUIDs are missing. A transient native timeout does not erase the journal report. This utility never creates or modifies model elements, never modifies the journal, and never licenses automatic replay.

Fourth-suffix outer exception reporting is corrected to `OUTCOME_UNKNOWN_NEEDS_JOURNAL_RECONCILIATION` and `modelWriteAttempts:null` rather than a false zero count. **These code changes were published, but the original live timeout occurred before their installation**.

- [Latest offline CI run #38148329249](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38148329249): **175/175 tests PASS**.
- Source head `9db6fdcb588c2a8c28c7b386600ffe3fcc4793d0` on PR #35.
- Remaining live acceptance **NOT_VERIFIED**. Next check: run read-only journal-only utility. Do not rerun any Create token or assume 13 operations are missing until journal + native reconciliation.


## Owner screenshot plus full fourth-suffix diagnostic — 1 unjournaled native GUID

The owner supplied a screenshot of Archicad's Russian informational modal:

> В результате выполнения последней операции были созданы и/или изменены Элементы, расположенные на невидимых в текущий момент Этажах.

Buttons `Отменить` and `Продолжить`. This is consistent with a native Create on story 1 (+3m) while the active story is 0 and story 1 is hidden. **Causality is plausible, not yet proven by runtime traces:** the modal may delay native request completion until acknowledged.

The owner also supplied results from `diagnose_apa_suffix4_timeout.py --journal-only` and `--with-native --port 19726`:
- Fourth-suffix scene **reserved**, state `PARTIAL_OR_UNKNOWN_OUTCOME`, failed `s2-partition-1`, `TimeoutError: timed out`, `automaticRetry: false`.
- The only fourth-suffix journal step `s2-partition-1` is **ATTEMPTED / guid=null**. No later steps dispatched.
- First **32** native GUIDs still present; inventory now **33**.
- Exactly one unjournaled new native GUID: **`bcfc99f0-50d2-4cd5-bf27-8f436c21683a`**.
- Active story 0 at read-only diagnosis; no other missing or extra model GUIDs.
- **DO NOT rerun fourth suffix or infer the orphan's BIM type from inventory alone.** The orphan needs exact typed readback; preserve open test PLN and journal.

Published `scripts/inspect_apa_orphan_s2_partition.py` in [PR #35](https://github.com/dvikt33-ux/safe-bim-layer/pull/35): strictly read-only, validates the original fourth-step approved durable CreateWalls parameters, original 32 + exactly one new GUID, pinned project/stories, native Wall type and story 1 (+3m), reference coordinates, thickness, height, offset and Z. Emits `READ_ONLY_ORPHAN_S2_PARTITION_VERIFIED` only on full typed match, and never rewrites original journal or grants a replay. Synthetic tests recreate the exact failure mode where native Create succeeds but response times out because UI waits, leaving `ATTEMPTED` / GUID null in SQLite. [GitHub CI run #38148800622](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38148800622) **SUCCESS: 185/185 offline tests PASS**.

**Next step:** close the Archicad informational modal with `Продолжить` once (do not silently disable warnings), then run the new read-only typed GUID audit. No additional native creates are authorized until the exact orphan is read back and a new unique, journal-backed 12-step suffix is independently approved. The original scene remains unsaved; full 25-element acceptance remains **NOT_VERIFIED**.

## Live independent typed readback: fourth-suffix timeout orphan IS s2-partition-1

After modal review, owner ran `scripts/inspect_apa_orphan_s2_partition.py --port 19726`. The command produced:

```json
{
 "status":"READ_ONLY_ORPHAN_S2_PARTITION_VERIFIED",
 "sceneId":"apa-suffix4-20261011-031123-7181b47c",
 "operation":"s2-partition-1",
 "guid":"bcfc99f0-50d2-4cd5-bf27-8f436c21683a",
 "journalState":"ATTEMPTED",
 "nativeType":"Wall",
 "nativeFloorIndex":1,
 "expectedAbsoluteZ":3.0,
 "nativeAbsoluteZ":3,
 "plannedElementsVerified":13,
 "totalModelElements":33,
 "remainingPlannedCreates":12,
 "journalRewritten":false,
 "modelWriteCalls":0,
 "replayOfFourthSceneAllowed":false,
 "outcome":"RECONCILED_IN_NATIVE_NOT_IN_ORIGINAL_CREATE_LEDGER"
}
```

**Classification: USER_SUPPLIED / LIVE_TYPED_READ_ONLY_PASS.** All native wall geometry fields from the historical `s2-partition-1` CreateWalls intent were verified, including endpoints, height, thickness, offset, arc and absolute story Z. The model now contains original 20 + verified planned 13 = **33**. Zero old GUIDs missing. The native GUID above remains absent from the *old* fourth Create journal (`ATTEMPTED, guid=null`), and that journal must never be rewritten to pretend the transport response succeeded. Do not replay the fourth reserved scene. The next step is a uniquely reserved **fifth** continuation using 13 proven existing GUIDs, only the remaining **12** planned creates, preserving original graph and all old partial records. The missing-visibility modal is consistent with the earlier 15-second HTTP timeout, but timing causality is not formally proven.

**Status:** 13/25 reported live verified, 12 unbuilt, unsaved project, no fifth scene created.

## Fifth suffix published and offline verified — only 12 remaining creates

Source published in draft [PR #35](https://github.com/dvikt33-ux/safe-bim-layer/pull/35) with `scripts/continue_apa_after_orphan_partition.py`. This source is **not** evidence that the last 12 elements have been created live.

The new default read-only gate:
- validates original 25-step historical graph from pinned original SHA256 evidence, story bindings and Tapir 1.5.10 schema;
- requires fourth suffix journal `PARTIAL_OR_UNKNOWN_OUTCOME` on exactly `s2-partition-1` with 1 `ATTEMPTED` row, fourth plan hash `f426fb1f7c8363850440226ad949aab39729dd5927a63bf0854cb043e8874b75`, no fourth GUID; independently reruns read-only native orphan geometry checks;
- pins verified orphan native GUID `bcfc99f0-50d2-4cd5-bf27-8f436c21683a`, revalidates first 12 historical GUIDs, both slab repair material and intent hash, strict 33 native GUIDs, active floor 0, existing floor levels, structure, geometry, and project identity;
- refuses immediately if a new fifth scene already exists; never replays fourth, never rewrites old journal; reserves new distinct `apa-suffix5-20261011-031123-7181b47c` only after a fresh explicit owner token, then creates **exactly 12** pending operations through the existing journaled SceneWriter, followed by all 25 typed readbacks and expected total 45 native GUIDs;
- improves transport for this continuation only: native Create HTTP timeout is `120s` rather than `15s`; all GET calls remain `15s`. No auto-acknowledgement of Graphisoft dialogs, no auto-retry. User must be present to click `Продолжить` promptly if the invisible-story modal appears. Longer timeout reduces the risk of orphan responses but cannot guarantee a dialog will complete or prevent native errors.

The shared Tapir helper remains default 15 seconds; it now accepts an opt-in bounded timeout `0 < timeout <= 120s`. The old attempts remain immutable.

Synthetic GitHub [CI #38149533972](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38149533972) **SUCCESS — 195/195 offline tests PASS**, including new 13+12 complete final-model result, no-retry after timed-out fifth scene, fail-closed native inventory mismatch, exact orphan GUID constraint and 120s-create/15s-read transport boundary. Intermediate CI failures from synthetic mocked fourth token and reservation-order regression were corrected; only latest successful head is acceptance evidence.

**Status:** READY_FOR_OWNER_LIVE_PREFLIGHT; 13/25 reported live verified unsaved; 12 remaining NOT_LIVE_VERIFIED. Future source improvements: fix the generic second-story slab global-Z placement, and independently analyze/suppress modal warnings with an explicit user-approved UI preference rather than circumventing native dialogs.

## Fifth suffix owner live read-only preflight PASS — awaiting explicit Create approval

Owner's PowerShell fetched source to commit `f125c063031117cf8a77a83fd0fed8e1c288a047`, then executed `continue_apa_after_orphan_partition.py --port 19726 --material "Железобетон - Конструкционный"` with **no** `--confirm-token`. The CLI reported:

```json
{
  "status":"READY_FOR_EXPLICIT_TWELVE_STEP_CONTINUATION",
  "sceneId":"apa-suffix5-20261011-031123-7181b47c",
  "binding":{
    "path":"C:\\LocalAI\\APA_Test_House_01.pln",
    "name":"APA_Test_House_01",
    "port":19726,
    "tapirVersion":"1.5.10",
    "storyIndex":0
  },
  "reusedCount":13,
  "remainingCount":12,
  "modelWriteAttempts":0,
  "maxCreateTimeoutSeconds":120
}
```

**Evidence: USER_SUPPLIED / LIVE_READ_ONLY_PASS.** A fresh continuation approval token was returned but is intentionally omitted from the durable report. This is a preflight only; no fifth-suffix writes have yet been independently reported. The prescribed next action is one user-approved native Create of the 12 remaining steps in this uniquely reserved fifth scene. User should be present to acknowledge any invisible-story Archicad modal promptly; only Create calls have a 120s HTTP timeout. No automatic retries, file switch, PLN Save, rollback or journaling rewrite. Expected completion `COMPLETE_UNSAVED`, 13 reused + 12 created, full typed GUID readbacks, **45** total model elements; live completion and PLN persistence remain **NOT_VERIFIED** pending execution logs.

## Owner-proposed mitigation: keep Archicad in 3D during cross-story writes

After the fourth-suffix timeout and invisible-story modal, the project owner identified an operational workaround: **open the 3D model view instead of a 2D floor-plan view before sending native creation operations**. In 3D, story-based visibility warnings may no longer interrupt edits to elements on a different story. This mitigation is **USER_PROPOSED / NOT_YET_LIVE_VERIFIED FOR APA**; it must not be documented as an established elimination of the modal until independently checked in the disposable PLN.

**Minimal safe test protocol for the next fifth-suffix attempt:** In the same already-open test PLN, manually open the 3D window (not a new project). Run `continue_apa_after_orphan_partition.py --port 19726 --material "Железобетон - Конструкционный"` without any confirmation token. Confirm the read-only result still reports the exact PLN path, Tapir 1.5.10, active native story 0, 13 reused / 12 remaining and zero attempted writes. **If story guard rejects the 3D state, do not weaken/override it or use the old token; investigate the native story semantics and adapt safely.** If read-only preflight passes in 3D, a separate explicit owner approval may run the same one-shot fifth suffix with the freshly returned token while the 3D window stays active. Never automatically open 3D, hide dialogs or manipulate UI without the owner's request. No old scene replay.

Keep `120s` Create HTTP timeout and immutable SQLite reservation checks until a live run establishes this mitigation's effectiveness. Record if a modal still appears, the step, actual outcome and whether final typed readbacks pass. Do not infer completion before live output.

## MILESTONE — owner LIVE whole-scene 25/25 typed acceptance, UNSAVED (2026-10-11)

After the previously recorded successful fifth-suffix **read-only** preflight (reused 13 / remaining 12), the owner explicitly executed the one-shot continuation on **Archicad 29 + Tapir 1.5.10**, local test PLN `C:\\LocalAI\\APA_Test_House_01.pln`, Tapir port `19726`, story index `0`:

```json
{
  "status": "COMPLETE_UNSAVED",
  "sceneId": "apa-suffix5-20261011-031123-7181b47c",
  "reusedCount": 13,
  "newCreatedCount": 12,
  "allGuidsReadback": true,
  "failedStep": null,
  "reason": null,
  "plnSaved": false,
  "automaticRetry": false
}
```

**Evidence classification: USER_SUPPLIED / REPORTED_LIVE_TYPED_READBACK_PASS_UNSAVED.** A new 12-step suffix was created after exact native readback verified the preceding 13 elements, including the orphan GUID `bcfc99f0-50d2-4cd5-bf27-8f436c21683a` that was created despite earlier transport timeout. The last run returned **COMPLETE_UNSAVED**, reported **12 newly created and 13 reused** planned elements and **allGuidsReadback=true**. Across the original 25-element graph, all **25/25** planned elements therefore passed in-session typed post-write acceptance. With 20 original elements, the expected live inventory is **45 elements**; this count is derived from the scene's verified inventory gate, not from a separately captured final manual `GetAllElements` printout. The scripted final readback covers existing host/story/geometry/material and GUID reconciliation according to the validated source, and uses the same SceneWriter; no user-confirmed PLN save occurred.

**Boundary:** This does **not** prove PLN persistence across Save As/reopen, independent visual suitability, cross-session stability, or structural/design correctness. User's workaround of opening the same model in 3D was proposed; the supplied last CLI output does **not** independently prove which view was active or that modal suppression caused success. The 120s native Create timeout was enabled. Do not claim the 3D tactic is independently causal from this log alone.

**Current gate result:** `APA-P70.A03.S02` slice `scratch-25-element-two-storey-shell` = **REPORTED_LIVE_COMPLETE_UNSAVED**. Do NOT mark the full controller S02 `DONE`, since its broad acceptance requires the upstream semantic structural graph and persistent/reopen/real-project gates; the canonical controller was not mutated. Next gated verification:
1. No further native writes, replays, or closing the test PLN before persistence.
2. Save a **new copy** of the disposable test PLN to a distinct, human-chosen path using Archicad Save As, without overwriting protected PLN or changing original journals (requires separate owner action).
3. Independent read-only verification of **saved copy** after reopen: precise project path/story bindings, native 45 GUID inventory, all 25 planned elements' typed wall/slab/opening geometry, owner host references, materials, and expected story elevations. A new path binding may require a distinct read-only verifier; do not loosen exact existing Test_House pinned writer guards.
4. Record explicit SAVE_REOPEN_PASS or FAIL from actual user output; only then consider promotion from `UNSAVED`.

**Source:** [draft PR #35](https://github.com/dvikt33-ux/safe-bim-layer/pull/35), fifth suffix `scripts/continue_apa_after_orphan_partition.py`; [last 195/195 offline CI](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38149533972). All original failed/partial journals remain historical evidence, no retry.

## Owner-supplied Save As destination; independent read-only re-open verification ready

**Owner-supplied saved-copy path:** `C:\\институт проект\\Улучшенная копия APA_Test_House_01.pln`. The owner supplied this path after the successful in-memory 25/25 scene. Path alone does **not** establish that the file exists on disk, has been closed/reopened, or has retained all the geometry after serialization. **SAVE_REOPEN = NOT_VERIFIED** until direct native readback from the reopened exact-copy path.

Source `scripts/verify_apa_saved_copy_read_only.py` is published in [draft PR #35](https://github.com/dvikt33-ux/safe-bim-layer/pull/35) to verify the *new exact path*, not the original approved scratch writer path. The verifier:
- checks physical file existence/nonzero size and `GetProjectInfo.projectPath` / `projectName` matching the owner's Unicode saved-copy path, exact Tapir 1.5.10 version and local, non-Teamwork saved project; no active-story requirement on a reopened copy;
- independently loads the SHA256-checked original graph and the immutable first/second/third/fourth/fifth SQLite journals in **mode=ro**, demands final fifth scene `COMPLETE_UNSAVED`, exactly 12 fifth PASS GUIDs, 13 previously verified elements including the orphan GUID, both prior slab repair states/hashes;
- requires an exact `GetAllElements` set of **45 GUIDs** = original 20 + planned 25 (no duplicates, no missing, no unexpected);
- for *each* of the original 25 steps performs typed `GetDetailsOfElements` and validates Wall positions/heights/thickness/absolute native story Z, Slab Basic/thickness/polygon/building-material GUID/absolute 0m and +3m Z, hosted opening width/height/sill/offset and owner Wall GUID, and story mapping; checks copy identity and inventory once more before PASS;
- allows **only** `GetProjectInfo`, `GetAddOnVersion`, `GetStories`, `GetAllElements`, `GetDetailsOfElements` native commands, makes no file or SQLite writes, and does not call original write utilities' exact old-file guard. Reports `OPEN_SAVED_COPY_TYPED_READBACK_PASS` only on full native matches, otherwise blocks without any mutation.

**Explicit limitation:** native API and local path cannot independently prove that a user truly closed and reopened a file. Owner must **manually reopen** this specific copy before running the verifier; record this owner action separately. A file-path match alone must not be promoted to `SAVE_REOPEN_PASS` without that manual transition and a successful fresh readback.

[GitHub CI #38150899253](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38150899253) **SUCCESS: 207/207 offline tests PASS**. Tests exercise synthetic fully created 45 GUID copy, exact UTF-8/Unicode copy path, wrong/old path, missing file, GUID drift, bad upper Slab Z and zero native writes. **No actual saved copy was accessed by CI.** Source commit `62789eca361df59b7749f3930aa77f269c5258ed` (script originally at `8b2e816`). **Next gate:** owner confirms actual copy exists, manually reopens that copy in Archicad 29, runs the read-only verifier, returns full JSON for independent publication.
