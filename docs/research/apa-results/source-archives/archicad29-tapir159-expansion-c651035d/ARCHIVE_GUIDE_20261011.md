# Навигатор по архиву 71 источника Archicad 29 / Tapir 1.5.9

**Классификация:** `LEGACY_SOURCE_ARCHIVED_BYTE_EXACT / TECHNICAL_FINDINGS_NOT_REVERIFIED`. 71 оригинальный MD/JSON-файл из source commit [`c651035d`](https://github.com/dvikt33-ux/safe-bim-layer/commit/c651035ddc77869fbc5a04bf23170b4f1188a9ab) сохранён в canonical ветке отдельным Git-коммитом [`477ba54a`](https://github.com/dvikt33-ux/safe-bim-layer/commit/477ba54a0620ce7c0efc1b835f1d0ad2f1a03ba5), без изменения существующих source Git blobs. Прямое Git tree readback дало **71/71 SHA и размер совпали**, 0 mismatches, `truncated=false`, 487455 bytes. Исходные документы и их `README.md` не переписаны.

[ARCHIVE_MANIFEST_20261011.json](ARCHIVE_MANIFEST_20261011.json) содержит полный список `source_path`, `archived_path`, `source_blob_sha`, `archived_blob_sha`, `bytes`, `associated_existing_task_ids`.

## Навигация по темам

| Архив | Содержание | Объём подтверждения |
| --- | --- | --- |
| [00_master](00_master/RESEARCH_MASTER_AUDIT.md) | Project Profile и итоговые принципы Safe BIM | historical SOURCE, не код текущего APA |
| [01_missing_data_audit](01_missing_data_audit/MISSING_DATA_AUDIT_PASS_01_10.md) | Недостающие данные native API, первые 20 исследовательских проходов | source research |
| [02_tapir_159_delta](02_tapir_159_delta/TAPIR_159_DELTA.md) | Отличия Tapir 1.5.9 от 1.5.8 | историческое, для 1.5.10 нужен fresh-diff |
| [03_archicad_api_contracts](03_archicad_api_contracts/SINGLE_ELEMENT_GABLE_ROOF_RESEARCH_PASSES_01_20.md) | Multi-plane Gable Roof, Composite, flat roof/parapet | source candidate; LIVE NOT_VERIFIED |
| [04_safe_bim_semantics](04_safe_bim_semantics/assistant_recipe_envelope_v0_1.schema.json) | Typized job/profile/snapshot/recipe drafts | концепция, сравнить с текущим SceneWriter |
| [05_expansion_candidates](05_expansion_candidates/PARAMETRIC_GDL_LIBRARY_FACTORY.md) | Factory GDL, оптимизация архитектуры и project recipe | proposal, не работающий GDL producer |
| [06_integration_audits](06_integration_audits/INTEGRATION_BACKLOG.md) | Backlog/архитектуры project context, resources, AI | источник для существующих S-ID |
| [07_live_probe_backlog](07_live_probe_backlog/NEXT_CONTROLLED_PROBES.md) | Список Roof/Mesh/Morph/SEO/Hotlink/GDL probes | **не** разрешение на реальные записи PLN |
| [08_sources_evidence](08_sources_evidence/SOURCE_MANIFEST.md) | GitHub/Graphisoft первоисточники | первичная ссылка, повторить на актуальном SDK |
| [09_final_audit](09_final_audit/FINAL_RESEARCH_AUDIT_V2_AFTER_PASS_90.md) | Итоги и исправления после 90/160/180/200 проходов | исторический research |

## Выбор решения для APA

1. **Не писать второй BIM writer.** Уже реализованы `archicad_project_accelerator.py`, BIM Graph, существующий guarded SceneWriter и synthetic building shell с Wall/Slab/Window/Door. Рекомендации о deterministic recipe compiler сопоставлять с этим кодом, расширяя существующие контракты.
2. **Roof/Gable:** исторический [Gable addendum](09_final_audit/GABLE_ROOF_FINAL_AUDIT_ADDENDUM.md) обосновывает одну `API_PolyRoofID` Multi-plane Roof с per-edge settings. Реальный текущий Tapir 1.5.10 контракт и создание/чтение должны пройти отдельные тесты. Две Single-plane крыши не тождественны одной native Roof.
3. **Composite/Attributes:** [исследование](03_archicad_api_contracts/COMPOSITE_STRUCTURES_RESEARCH_PASSES_01_18.md) предлагает использовать native `CreateComposites` / `GetComposites`, project materials и точно прочитанный fingerprint, а не изобретать структуру слоёв. Реальная актуальная доступность команды требует проверки.
4. **GDL:** [factory proposal](05_expansion_candidates/PARAMETRIC_GDL_LIBRARY_FACTORY.md) зависит от актуальной проверенной идентичности library part и compiler; блокер 92 inventory errors при Tapir 1.5.10 остаётся отдельным.
5. **Project Context:** [bridge audit](09_final_audit/FINAL_PROJECT_CONTEXT_BRIDGE_AUDIT_AFTER_160.md) требует identity/stamp, свежий model-state snapshot, защиту от stale changes и отказ от blind retry; это не подтверждение существующего сквозного live context mirror.
6. **Transport:** [sync after pass 200](09_final_audit/FINAL_TRANSPORT_SYNC_OUT_OF_BOX_AUDIT_AFTER_200.md) — историческая проектная архитектура. Отдельная проверка Slack→SQLite доказала транспорт событий, но **не** автоматическую публикацию произвольных ChatGPT-чats или direct Archicad writer.

## Контроль изменений

`APA-P00.A02.S03` отвечает за объединение архивов и логические дубли, `APA-P50.A01.S01` — за traceability, `APA-P70.A01.S02` — за соответствие кода конечным функциям, `APA-P10.*` — за актуальные SDK/контракты. Предложение нового `APA-P00.A02.S05` рассмотрено как [DUPLICATE существующего S03](../../control/reviews/APA-CAND-20261011-source-archive-71.md); новый S-ID не нужен.

**Любые Tapir 1.5.9 claims не равнозначны текущей Tapir 1.5.10 или Archicad 29 LIVE.** Архив не изменяет `main`, исходную ветку, PLN, APX, установленный Archicad и SQLite.
