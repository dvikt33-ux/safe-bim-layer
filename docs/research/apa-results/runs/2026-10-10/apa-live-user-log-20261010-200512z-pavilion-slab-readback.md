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
