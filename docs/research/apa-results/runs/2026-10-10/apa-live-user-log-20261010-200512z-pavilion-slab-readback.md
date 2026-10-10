# APA-P20.A02.S03 — первый live-запуск павильона: частичный результат и блокировка slab readback

- **Источник:** текст консольного отчёта, предоставленный владельцем 2026-10-10; локальный JSON: `C:\Users\Admin\Downloads\APA_MVP_Windows11_v1_3_COLUMN_PARENT\APA_MVP_Archicad29\results\execute-20261010T200512Z.json` (локальный путь из пользовательского лога, сам файл JSON не получен). Доказательство ниже — **REPORTED_FROM_USER_LIVE_LOG**, а не независимый LIVE readback по установленному APX.
- **План:** APA-P20 → APA-P20.A02 → APA-P20.A02.S03. Этот документ **не меняет** статус задачи в PROJECT_PLAN.json; никакого DONE_PUBLISHED/live PASS полной сцены.
- **Инструмент:** локальный APA MVP v1.3 COLUMN_PARENT с исходниками из PR #16, проверка Git blob 13/13; применённая локальная оболочка v1.3 не сверялась побайтово с GitHub.
- **Контекст:** Archicad 29; модифицированный Tapir 1.5.10; target TEST MER (название в консоли отображается с заменой кириллицы), порт 19724; `storyIndex=0`; якорь (300,300) м. Test PLN не был автоматически сохранён.
- **Сценарий:** `sceneId=apa-pavilion-live-02`; `sourcePlanHash=28361d6e066364f5c6193404a0f25e395a183729ad44fb1cbe6cb07d2d6bd7dc`; один пользовательский ввод `EXECUTE TEST`.
- **Preflight:** `READY_FOR_EXPLICIT_TEST_RUN`, 38 native elements inspected; четыре `ColumnSegment` с inverted bbox были консервативно сопоставлены с bbox их родительских колонн; geometry envelope check PASS на момент preflight.
- **Execution:** `PARTIAL_OR_UNKNOWN_OUTCOME`, `failedStep=slab`, `reason=ValueError: SLAB_READBACK_MISMATCH`, `manualReconciliationRequired=true`, `plnSaved=false`, `automaticRetry=false`.
- **Four wall steps reported PASS and independently named by returned GUID in operator log:**
  - south: `6C6CB42D-8368-4749-81F9-D5FA8748AB20`
  - east: `BD622995-16E6-4C9B-BF42-4934AD40A931`
  - north: `1B95F857-025F-457F-A369-E455F33B7861`
  - west: `79B92DDC-9B38-44F3-9768-0F08CEC0274E`
- **Slab outcome:** not known. Write may have succeeded before geometry readback raised mismatch. No evidence that Columns/Window/Door mutations ran after slab; complete scene **NOT_VERIFIED**.
- **Implementation clue, NOT diagnosis:** PR #16 pinned `scripts/archicad_scene_run.py` `verify_readback(CreateSlabs,...)` rejects if any of `thickness`, `level`, `polygonOutline` differ from plan. Without raw slab GUID/readback/SQLite row, exact mismatching field is **UNKNOWN**. v1.3 local modifications are not independently examined.
- **Safety and next action:** NO retry, NO reused scene ID/hash, NO deletion/undo/save/switch before manual reconciliation. Read-only inspection of currently open PLN plus durable SQLite step journal `slab` row (state and GUID), inspect native slab `GetDetailsOfElements` and 3D bbox; compare thickness/level/polygon to plan. If no trustworthy recovery data, keep BLOCKED/PARTIAL and do not infer 12/12.
- **Reproducibility limitation:** the supplied console report is a user-authored log transcript; no remote connection to Archicad or direct confirmation of unsaved current model was possible from this chat.
- **Source reference for reader logic:** https://github.com/dvikt33-ux/safe-bim-layer/blob/bcac2e821a95f927fa6ae9f5fa5742b45d9ca2dd/scripts/archicad_scene_run.py
- **No main/master, existing PR branch, PLN or installed APX modified by this GitHub report commit.**

## Follow-up read-only observation (operator log: inspect-20261010T200754Z)

- **INSPECT_READ_ONLY: PASS** on same reported bound TEST MER PLN and port `19724`, Tapir `1.5.10`, story index `0`.
- Before live execution preflight inspected **38** elements; after live execution read-only inspect reported `element_count: 43` (**delta +5**).
- This delta is consistent with 4 verified wall writes and one attempted slab creation, but **does not independently establish identity or validity of the fifth element**. Do not mark slab PASS on count alone.
- **Evidence:** second user-supplied console transcript, lines 363–377 (reported UI log); path `C:\Users\Admin\Downloads\APA_MVP_Windows11_v1_3_COLUMN_PARENT\APA_MVP_Archicad29\results\inspect-20261010T200754Z.json`; underlying JSON artifact was not provided.
- **Investigation priority:** read SQLite durable `steps` row for `scene_id=apa-pavilion-live-02`, `step_id=slab`; verify whether recorded `guid` is present and whether `state=CREATED_UNVERIFIED`. Fetch `GetDetailsOfElements` and bbox for that GUID READ-ONLY and compare to `CreateSlabs` intent fields: `thickness`, `level`, `polygonCoordinates` / returned `polygonOutline`. Preserve file/SQLite records. DO NOT replay writes.
- **No additional automatic or manually initiated writes were performed for this follow-up.**

## Durable SQLite evidence — attached primary artifact

- **Source:** user uploaded actual `scene-v1-attempts(1).sqlite3`; inspected using SQLite **read-only, immutable** connection; `PRAGMA quick_check = ok`; tables `scenes`, `steps`. This is stronger than console transcript evidence, but NOT native Archicad geometry readback.
- `scenes` contains exactly the targeted `scene_id=apa-pavilion-live-02` with state `PARTIAL_OR_UNKNOWN_OUTCOME` and matching plan SHA `28361d6e066364f5c6193404a0f25e395a183729ad44fb1cbe6cb07d2d6bd7dc`.
- `steps` has five rows for this scene: four `PASS` walls (GUIDs listed above) and one **`slab` with `state=CREATED_UNVERIFIED`, `guid=7539799C-D432-42F5-9F31-FED10E1047C4`**. Its `output` is a prior committed intent and approval, not the raw `GetDetailsOfElements` readback.
- **Slab intent:** `CreateSlabs` `floorIndex=0`, `level=0.0`, `thickness=0.2`, `referencePlaneLocation=Top`, vertices `(300,300),(304,300),(304,303),(300,303)`. Exact target path stored in journal is Unicode `C:\\LocalAI\\SafeBIM_Global_Library_Test_Projects\\Тест MER .pln`, port `19724`, Tapir `1.5.10`, story index `0`.
- **Interpretation:** Archicad/Tapir returned a syntactically valid GUID for the slab, and the writer committed it durably before `verify_readback` failed. This plus element count change 38→43 strongly supports creation of a fifth element, but slab geometry correctness remains **UNVERIFIED**, and we cannot assign which of the three fields mismatch without the actual `GetDetailsOfElements` response.
- **Next read-only check:** `GetProjectInfo` (exact expected project identity), `GetAddOnVersion` (1.5.10), `GetDetailsOfElements` for slab GUID, `Get3DBoundingBoxes` for slab GUID; compare returned `type`, `floorIndex`, `details.thickness`, `details.level`, `details.polygonOutline`. Do not issue any create/modify/delete/save or replay the full scene, and do not remove the scene journal.
- **Root-cause status:** `SLAB_READBACK_MISMATCH` confirmed as failure gate; specific offending parameter and whether API-normalization vs true geometry defect is **NOT_YET_VERIFIED**.
