# BDD House — production continuation through the installed unified APA selector

**Status:** `SOURCE_TASK_PUBLISHED / NATIVE_NOT_RUN`. This is a continuation of the existing BDD House, **not** a new executor, test suite, catalog, or standalone Tapir writer.

## Authoritative starting point

- Integrated selector: [PR #132](https://github.com/dvikt33-ux/safe-bim-layer/pull/132), commit `30af6480860ff98995177b91acf47b676d4a52ac`; local installed discovery was verified offline. It must be imported in a **new APA process**; the change did not hot-reload into an already running process.
- Latest **saved** house evidence: [PR #127](https://github.com/dvikt33-ux/safe-bim-layer/pull/127), 290 GUID after the native batch of 13 timber studs and their 13 ColumnSegments. Previously 261 GUID included 21 originals, 125 physical parents, 115 native child segments; then 3 verified Windows and 26 new column/root+segment GUIDs. Treat 290 as the **last reported baseline**, not a substitute for current live inventory.
- The three Windows are **already created**: west `5C63FA89-C4A9-4EC5-811A-D989CF1D8626`, north `C8E2B64E-2D9D-44AD-879F-58E57F8DC2A4` and `0F567C7E-2ADB-40DE-AB0A-D50271B8F8BF`. Native receipts are in `safe-bim-bridge/safe-bim-mailbox/gpt-live/results`. Never replay those CreateWindows operations.
- Working PLN: `C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln`; protected original: `C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln`. The current *saved* working SHA must be read locally, not taken from an old report. Source original SHA in earlier evidence: `33b96850ad07547a9b12524de8bc46479fd98fbbce6772436d388be679836d66`.
- Project: Archicad **29 build 5101**, previous port **19727** (verify in this process). First storey: native index 0, user-visible **Первый Этаж** +0.000; no separate storey named 0.
- Only authoritative structural document is `3_этап_КП_КОМФОРТ_без_замазок.pdf` (2022, Шебаново). Do not mix with 2026 `2_этап_АП_КОМФОРТ.pdf`, a different project.

## First source-qualified APA task — no command names

[Machine input](../../../../examples/accelerator/bdd-house-20261017-auto-selector-source-read.json) is `apa-capability-task/1`: two **READ_ONLY** effects with complete real 6-Wall GUID list, input shapes, output requirements and source hashes. It does **not** specify command names or alternative workflows. Run it using the **installed new** `archicad_strategy_discovery.discover_native_execution_plan(router, intent)` with original APA DynamicCommands catalog and imported matching reviewed policies, then the existing `run_auto_optimized_native_task` / `SceneWriter` authorized route. No direct Tapir invocation or new runner. All local runtime/project/ledger/saved-SHA guards still apply.

This read is a necessary **production snapshot for placement**, not a general functionality retest. The selector should infer matching details/bbox operations; actual chosen commands, registration, preview and readback remain **NOT_RUN** until local execution. The source hashes bind each step's source-specified parameters; source provenance does not authorize PLN mutation.

Before any new writes, verify current full model inventory, all three Window GUIDs, 13 timber studs + 13 segments, all 6 existing exterior Wall GUIDs, the known 49 piles and 48 joists, roof and slabs, their attributes/BREP, and the protected source unchanged. If saved GUIDs do not match the expected 290, **reconcile**, never reset to 290 by replay. Existing 6 exterior Walls must not be created again.

## Actual next construction package (after fresh read, not another adapter)

**Priority: 2022 KR-10 to KR-15 internal timber-frame and remaining openings.** The wall-block elevations 1.9–1.23 are in PDF pages 15–17, their XY positions originate from KR-10 plan PDF page 12; initial 1.1–1.8 blocks and the three verified openings are already partially modeled. Exterior structural axes from dimensioned sheets: X `0/5.34/6.77/8.70/14.28 m`; Y `0/1.09/9.38 m`. General-note dimensions 14.18×9.28 m differ from structural axes 14.28×9.38 m: do not silently substitute them.

**Required for each new physical object:** exact plan coordinates and endpoints or source-approved prototype+translation, actual storey/Z, section/thickness and orientation, approved native building material/favorite/library part, source sheet/dimension chain, conflict-free bounds, project GUID retention set, source data hash, and explicit source-verified modification/creation scope. Treat nominal studs @600 mm as a nominal pitch, not proof of exact placement across openings and corners. Do **not** substitute the 23 framing blocks with 23 guessed Basic Walls. Do not invent Door/Window types or handedness for the three tall block-1.7 openings.

**Use the new selector for all qualified creates.** For each homogeneous and source-qualified packet compose a **new** `apa-capability-task/1` with `CREATE` / `MODEL`, `elementType`, complete native `parameters` and per-step `sourceVerification` (`SOURCE_VERIFIED`, `dataHash`, `evidenceRef`), optionally producer-result bindings and `after` dependencies. There must be **no `command` keys** and no assistant-supplied alternative command list. The existing selector chooses from the installed catalog, reuses original BIM Graph and prepares original APA native-task previews. Two or more uncalibrated eligible strategies require a documented selection, **not** a fictional Fast Downward optimality claim. If geometry or a runtime-qualified contract is missing, return missing fields/status and leave the PLN unmodified.

Use exact current native scopes; each acknowledged write must have a unique intent-before-write SQLite record, fully reconciled GUID/host/geometry/material readback, and zero unexpected changes to retained objects. No blind retry for UNKNOWN or PARTIAL; one save to the **working** PLN only after all accepted operations. No automatically created experimental geometry outside the house. No duplicate Window, Wall, roof, pile, joist, or stud from earlier receipts.

## Roof and completion order

After interiors/remaining openings, construct the 2022 roof from its actual ridge/valley intersections, not by simply changing the existing roof Z. Reference ridge `+6.295 m`; earlier native roof zMax `+6.128 m` and valley topology were not source-resolved. Prefer real native Roof operations; pinned `CreateRoofs` contract currently mismatches the source-roof qualifier, so record a **narrow blocking incompatibility** and only correct it if it actually blocks the qualified roofing task. MORPH remains last resort.

Acceptance sequence: **source geometry → APA catalog selection → BIM Graph → SceneWriter → live Archicad 29 → independent BREP/host/material/GUID readback → saved working PLN**. Keep source PLN, `main`, other feature branches, Archicad 30 and Arena untouched. No mass offline tests or speculative adapters.

## Limit of this GitHub pass

This branch provides **one source-verified input for the actual new selector plus the exact continuation contract**. No live Archicad 29 connection, model mutation, save/reopen, fresh project SHA, new interior coordinates or physical production PASS is claimed in this GitHub pass. The mailbox worker in `safe-bim-bridge` was previously bound only to a different test PLN; do **not** send BDD writes through it as a substitute for installed APA control.

**Next necessary evidence:** local selector result + native current-state readback, then the first committed exact-coordinate internal-frame CREATE packet and its independent Archicad acceptance.
