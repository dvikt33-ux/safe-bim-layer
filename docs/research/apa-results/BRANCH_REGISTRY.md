# APA — карта веток и политика ветвления

**Срез:** 2026-10-10, составлен из доступного GitHub branch search, compare и прочитанных файлов. Это **не** полный git-forensic audit всех refs. Ветки не удалялись, не объединялись и не перемещались.

## Единственная точка записи исследований

**CANONICAL / WRITE HERE:** [research/apa-verified-results-hub-20261010](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010/docs/research/apa-results) — только Markdown-отчёты, план, реестры и ссылки на доказательства.

**PRODUCTION / NO WRITE:** [main](https://github.com/dvikt33-ux/safe-bim-layer/tree/main) — не изменять без отдельного разрешения.

## Снимок всех 72 веток — 2026-10-10

[Машинный JSON с branch/head SHA и PR](inventories/BRANCH_HEADS_20261010.json) и [читаемая таблица 72 веток](inventories/FULL_BRANCH_INVENTORY.md) получены из GitHub REST (20 open + 2 closed PR в полученных страницах). Это **этап 1/2**: точные имена/SHA подтверждены, но ancestry, уникальные файлы и superseded_by ещё не проверены. Все ветки KEEP_PENDING_FORENSIC_REVIEW, deletion_authorized=NO. Ни одна ветка не удалена.

## Обнаруженные ветки и назначение

| Ветка | Класс | Что известно / действие |
| --- | --- | --- |
| [research/apa-verified-results-hub-20261010](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010) | CANONICAL | Пять исходных опубликованных Markdown; сюда добавляется система управления |
| [research/apa-archicad29-independent-audit-20261010](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-archicad29-independent-audit-20261010) | POINTER_ONLY | Дублирующий индекс и ссылки на восстановленные документы; новых исследований сюда не писать |
| [research/archicad-full-capability-audit-20260928](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/archicad-full-capability-audit-20260928) | ARCHIVE_READ_ONLY | Capability ledger, execution architecture, GOST, test matrix |
| [research/apa-tn-gdl-create-01-blocker1-audit-20261009](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-tn-gdl-create-01-blocker1-audit-20261009) | ARCHIVE_READ_ONLY | GDL Blocker 1 forensic audit |
| [research/apa-tn-gdl-create-01-checkpoint-20261009](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-tn-gdl-create-01-checkpoint-20261009) | ARCHIVE_READ_ONLY | GDL checkpoint, нужна сверка дельты |
| [research/apa-tn-gdl-create-01-native-probe-20261009](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-tn-gdl-create-01-native-probe-20261009) | ARCHIVE_READ_ONLY | GDL native probe, нужна сверка дельты |
| [research/apa-20261009-api-mep-batching-audit](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-20261009-api-mep-batching-audit) | ARCHIVE_READ_ONLY | Tapir upstream contract audit; есть много файлов, не все проверены |
| [research/apa-20261009-resource-mep-bridges-audit-v1](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-20261009-resource-mep-bridges-audit-v1) | ARCHIVE_READ_ONLY | Resource/MEP audit, нужна сверка дельты |
| [research/archicad29-tapir159-expansion](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/archicad29-tapir159-expansion) | ARCHIVE_CANDIDATE | Содержимое не проверено в этом проходе |
| [research/architectural-model-quality-v2](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/architectural-model-quality-v2) | ARCHIVE_CANDIDATE | Содержимое не проверено |
| [research/library-system-v3](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/library-system-v3) | ARCHIVE_CANDIDATE | Содержимое не проверено |
| [feature/apa-slack-event-coordinator-20261010](https://github.com/dvikt33-ux/safe-bim-layer/tree/feature/apa-slack-event-coordinator-20261010) | CODE_REVIEW | [PR #21](https://github.com/dvikt33-ux/safe-bim-layer/pull/21), не смешивать с журналом исследований |

Также связаны [PR #16](https://github.com/dvikt33-ux/safe-bim-layer/pull/16), [PR #17](https://github.com/dvikt33-ux/safe-bim-layer/pull/17), [PR #20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20). PR — ссылки на код и reported evidence, не автоматическое доказательство live-результата.

## Правила новых веток

1. **Для исследования новые ветки запрещены по умолчанию.** Новая тема = новый подшаг MASTER_PLAN + новый Markdown в runs/ + индекс.
2. Новая ветка допустима только для отдельного изменения кода, опасного эксперимента или независимой сборки после явного обоснования и с записью назначения здесь.
3. Старые ветки **не удалять и не переписывать** до полной инвентаризации и решения владельца.
4. При обнаружении новых файлов добавлять URL, SHA и статус в ARTIFACT_REGISTER; не копировать непроверенные выводы как VERIFIED.
5. Нет разрешения менять main, тестовые ветки, PLN или установленный Add-On.
