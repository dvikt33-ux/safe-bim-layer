# TASK_PROPOSAL_V1 — физическое сохранение 71 SHA-идентичного исследовательского файла

```yaml
schema: TASK_PROPOSAL_V1
proposal_id: APA-CAND-20261011-source-archive-71
origin: audit
proposer_run_id: APA-RUN-20261011T000452Z-branch-blobs-69
source_substep_id: APA-P00.A02.S03
proposed_parent_plan: APA-P00
proposed_action: APA-P00.A02
suggested_substep_id: APA-P00.A02.S05
work_key: preserve-pinned-source-blobs-71
title: "Сохранить исходный архив Archicad29/Tapir 1.5.9 в canonical research hub с byte-SHA проверкой"
kind: CONSOLIDATION
priority: 0
depends_on: [APA-P00.A02.S02]
related: [APA-P00.A02.S03, APA-P50.A01.S01]
inputs: [ART-BRANCHES, ART-REGISTER]
outputs: [source_copy_manifest, 71 source MD/JSON files byte-for-byte, GitHub readback evidence]
acceptance: "Каждый из 71 source path представлен в canonical research archive, Git blob SHA всех 71 совпадает с source HEAD c651035d..., источник/версия/статус указаны и readback пройден; исходная ветка и main без изменений."
requires_approval: false
expected_mvp_benefit: "Избавляет от поиска нужных аудитов по веткам, даёт локально доступную для ChatGPT/Publisher единую проверяемую базу с provenance. Не означает Archicad LIVE PASS."
evidence_urls:
  - https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json
  - https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/CANONICAL_BLOB_COVERAGE_20261011.json
  - https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/receipts/APA-RUN-20261011-001922Z-eighty-head-blob-inventory.json
risks: "Atomic low-level multi-file Git write was blocked in this chat. This proposal is NOT APPROVED until independent audit. Never claim copies from source index alone. Reconcile with existing S03; prefer safe file-level publisher or dedicated audited archival writer, not force-push."
```

## Статус предложения

**PENDING_INDEPENDENT_AUDIT / NOT_REGISTERED_IN_PROJECT_PLAN.** Нового S-ID ещё нет. Аудитор должен проверить пересечение с существующей `APA-P00.A02.S03` (общая дедупликация). При semantic duplicate принять решение `DUPLICATE` и встроить acceptance без нового S-ID. Только если независимая миграция 71 byte-identical source является самостоятельным измеримым deliverable и не конфликтует с графом, назначить уникальный work_key/S-ID в `PROJECT_PLAN.json` и проверить controller CI.

## Основание

- 83 ветки / 80 точных HEAD по текущему снимку, 80/80 деревьев GitHub без усечения.
- Внутри source HEAD `c651035ddc77869fbc5a04bf23170b4f1188a9ab` ровно **71 MD/JSON** файл под `research/archicad29-tapir159/`. Каждый source blob SHA и pinned permalink записан в `ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json`.
- По SHA сравнениям с canonical snapshot ни один из этих 71 исходных blob не включён byte-for-byte. Отсутствие SHA не означает, что не существует похожего исследовательского вывода в другом тексте.
- В этом проходе атомарная bulk-copy операция была заблокирована инструментом; проверка GitHub показала отсутствие `ARCHIVE_MANIFEST`. **Оригинальные source docs не копировались.**
- В исторических исследованиях Tapir **1.5.9** указан как установленный, но пользовательский проект сейчас использует **1.5.10**; перенос исходных текстов не может повысить статус их технических утверждений.

## Необходимый аудит / acceptance

1. Сверить source HEAD и SHA 71 исходного файла с GitHub branch pointer; следовать sha-pinned URL и не изменять original.
2. Выбрать поддерживаемый и проверенный путь записи в canonical branch без `force`, без массового перетирания файлов и без однообразных 71 несовместимых коммитов, если существует аккуратный publisher workflow.
3. Записать отчёт происхождения и 71 byte-exact текстовую копию в отдельную директорию, не смешивая их с source-certified V2 runs.
4. После коммита повторно прочитать Git tree и доказать все 71 `target_path→blob_sha` равными `source_path→blob_sha`. Не считать SHA файлов одинаковыми по имени.
5. Дать ссылку на receipt/commit/readback и обновить ARTIFACT_REGISTER. Документы остаются `LEGACY_SOURCE_ARCHIVED / TECHNICAL_FINDINGS_NOT_REVERIFIED`, а не `DONE` для Archicad.
