# APA-P70.A03.S02 — live saved-copy preflight + exact unnamed-story pins, source/offline CI PASS

**Date:** 2026-10-11. **Task:** `APA-P70.A03.S02` / live read-only story-material preflight + actual native story resolution. **Task status: PARTIAL**.  
**User live evidence:** console output in chat (no local Archicad action by assistant). **Source patch:** [draft PR #45](https://github.com/dvikt33-ux/safe-bim-layer/pull/45), `feature/apa-unnamed-native-story-pins-20261011`, stacked on existing [draft PR #44](https://github.com/dvikt33-ux/safe-bim-layer/pull/44). **CI:** [run #38160976956](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38160976956) **SUCCESS, 267/267 tests**. No native writes, no PLN/APX/main mutations.

## 1. User's real Archicad 29 / Tapir 1.5.10 read-only measurements

PowerShell here-string forwarded ASCII-only Python source with `\\u` escapes to avoid `?` substitution of Cyrillic in expected PLN path. `GetProjectInfo` was checked before and after two subsequent native GET commands; `GetStories`, `GetAttributesByType(BuildingMaterial)` were executed; user supplied:

```json
{
  "status":"READ_ONLY_PREFLIGHT_PASS",
  "projectUnchanged":true,
  "stories":[
    {"index":0,"floorId":1,"dispOnSections":true,"level":0,"height":3,"name":"Первый Этаж"},
    {"index":1,"floorId":2,"dispOnSections":true,"level":3,"height":3,"name":""},
    {"index":2,"floorId":3,"dispOnSections":true,"level":6,"height":3,"name":""}
  ],
  "materialMatches":[
    {"attributeId":{"guid":"63DB2CE9-903D-45C0-B93C-B3C604C77394"},
     "index":10,"name":"Железобетон - Конструкционный","modificationTime":1400849103}
  ],
  "nativeWriteCalls":0
}
```

Immediately preceding native identity probe confirmed the exact currently open saved project path `C:\\институт проект\\Улучшенная копия APA_Test_House_01.pln`, projectName `Улучшенная копия APA_Test_House_01`, `isUntitled=false`, `isTeamwork=false`, port `19726`. This is **read-only binding evidence**, not proof of full source graph execution.

**Interpretation:** Three **native stories** exist, not two. Earlier 25-building-element saved-copy test was scoped to native indices 0 and 1 (13+12); no claim was made about building elements on index 2 in this live preflight. The architectural label `1 этаж` should bind to native index 0/floorId 1/Z0 with native name `Первый Этаж`; architectural `2 этаж` to native index 1/floorId 2/Z3 with native name `""` (blank), **only on explicit authored mapping**, not a guessed index or synthetic `Второй Этаж`. Native index 2/floorId 3/Z6 remains a distinct existing level and is not implicitly selected.

## 2. Root cause of prior failed PowerShell path comparisons

The prior `WRONG_OPEN_PLN` and `WRONG_PROJECT` errors were caused by `PowerShell @'...'@ | python` replacing Cyrillic in **expectedPath** source literal with ASCII `?`; actual path from GetProjectInfo was correct. This is distinct from an earlier independently observed `.bpn` backup file being open. No argument for loosening exact PLN checks or switching project.

## 3. Source change: existing semantic brief/one BIM graph

Before PR #45, `scripts/archicad_semantic_brief.py` required every `existingNativeLabel` to be nonempty, so it could not resolve the unnamed actual native story. PR #45 adds optional ***explicit*** `existingNativeIndex` + `existingFloorId` + literal `existingNativeLabel`, which may be empty **only when both native identity fields are pinned**; it requires exact `level` matching and rejects mismatches, duplicate pinned native index/IDs, unauthored empty names and any pins on `GENERATE_FROM_ZERO` mode. Unpinned previously named GetStories mapping remains backward compatible.

No automatic modification of Archicad story names, file selection, Z-levels, source BIM wall/slab geometry or SceneWriter is introduced. Architectural floor labels remain logical, separate from native index. Existing Project Library Pack and native DAG consume the resulting `nativeStoryBindings` unchanged; exact material GUID is reused as a project-local proof, not a global attribute ID.

**Explicit two-floor example for current PLN (not auto-applied):**

```json
{
  "stories": [
    {"id":"level-1","label":"1 этаж","level":0,"existingNativeLabel":"Первый Этаж","existingNativeIndex":0,"existingFloorId":1},
    {"id":"level-2","label":"2 этаж","level":3,"existingNativeLabel":"","existingNativeIndex":1,"existingFloorId":2}
  ]
}
```

## 4. Offline CI and next gate

[CI #38160976956](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38160976956) on commit `65346da2f79b7427fefbcf18b7e9a02d1cae4b91` ran **267 tests, OK**. Added 5 semantic story-pinning regression cases and 1 cross-component story/material-to-existing-DAG test using the user-observed native 0/1/2 story inventory, 0/1 selection, 3m heights and RC material GUID. The first CI attempted the integration fixture with an incorrect test keyword `api=` instead of existing `read_api=`; corrected and final CI SUCCESS.

Previously automatic CI did not trigger for these new semantic module paths. PR #45 also updates existing `.github/workflows/archicad-contracts.yml` path filters to cover the actual semantic brief/spatial/CSE/native source and tests, without adding an independent CI system. This caused the final valid CI to run.

**Still blocked:** overall `APA-P70.A03.S02` is **PARTIAL**; user-approved disposable PLN native command execution, staged Basic slab material/absolute-Z readback for authored plan, wall CSE construction/structural acceptance and real building completion are NOT_VERIFIED. The owner-designated saved copy remains evidence, not a test writable target. No repeat of known-good 45/45 GUID scene without regression, and no new manual user test requested for this narrow fix.
