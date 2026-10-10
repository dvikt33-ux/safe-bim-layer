# APA / Archicad 29 — independent technical audit



> **ПОСТОЯННЫЙ АДРЕС РЕЗУЛЬТАТОВ:** [APA Research Hub](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010/docs/research/apa-results) и [GitHub Issue #23](https://github.com/dvikt33-ux/safe-bim-layer/issues/23). Эта ветка — **только исторический указатель**, не место новых отчётов. Актуальные план, подшаг, очередь, карта веток и журнал находятся в canonical hub. Не создавать здесь дополнительные файлы.


> **Status:** RESEARCH_IN_PROGRESS. This is a publication index and verification checklist, **not** a completed technical report. No Archicad API claim is considered verified merely because it appears in this index.

## Scope

Independent technical audit of Archicad Project Accelerator (APA) for **Archicad 29**, focused on native BIM geometry, building materials, stories, library objects, MEP, interoperability, tests, and shortest credible MVP path.

Primary codebase: [safe-bim-layer](https://github.com/dvikt33-ux/safe-bim-layer). Priority review target: [PR #21](https://github.com/dvikt33-ux/safe-bim-layer/pull/21).

## Planned deliverables

- [ ] `RESEARCH_INDEX.md` — evidence map and navigable findings index (this file will be expanded)
- [ ] `VERIFIED_FINDINGS.md` — independently checked facts, API signatures, source lines, versions
- [ ] `TOOLS_AND_INTEGRATIONS.md` — tool and library assessment; adopt/integrate/algorithm/reject
- [ ] `ARCHITECTURE_COMPARISON.md` — materially different options and decision matrix
- [ ] `BLOCKERS_AND_TESTS.md` — reproducible blockers, verification status, test procedures
- [ ] `MVP_IMPLEMENTATION_PLAN.md` — ordered, testable milestones and acceptance criteria

## Evidence policy

- **VERIFIED:** primary source or directly inspected code, with a precise URL, version, and relevant signature/line/section.
- **NOT_VERIFIED — DOCUMENT_NOT_READ:** a source was not read, was inaccessible, or only a title/summary/snippet was available.
- **TEST_REQUIRED:** source suggests an integration path but Archicad 29 behavior has not been validated experimentally.
- **BLOCKED:** a concrete, reproducible technical constraint is documented with its evidence and reproduction steps.

Archicad **29** must be distinguished from earlier releases and Archicad 30. Do not infer API behavior from a README or search snippet.

## Publication and safety

Research output belongs on this isolated branch. Do not alter `main`/`master`, PLN files, installed add-ons, or already validated implementations. No automatic merge.

## Найденные ранее сохранённые результаты GitHub (2026-10-10)

**Статус: EXISTING_ARTIFACTS_LOCATED; NOT_A_RECOVERY_OF_MISSING_DEEP_RESEARCH_REPORT.** Ниже перечислены реально существующие файлы в других ветках. Ссылки и содержимое указанных документов были прочитаны через GitHub connector; их технические утверждения не были независимо перепроверены в этом проходе. Наличие файла не означает завершённое исследование или LIVE PASS.

### Уже существующий центр публикации

Ветка: [research/apa-verified-results-hub-20261010](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010), **5 коммитов относительно main, 5 новых Markdown-файлов** (по GitHub compare API):

- [README — навигация](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/README.md)
- [Реестр APA-01…APA-12 от 10 октября](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/2026-10-10-research-register.md): GDL, 92 ошибки каталога, MEP, Generic Opening, материалы Roof, Model Dump, этажи, SomeStuff, координатор, writer, воспроизводимость
- [CURRENT_BLOCKERS](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/CURRENT_BLOCKERS.md)
- [PUBLISHING_PROTOCOL](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/PUBLISHING_PROTOCOL.md)
- [APA-DOC-PIPELINE-01: Publisher/Layout](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-10/apa-technical-20261010-094254-publisher-layout-01.md)

### Другие прочитанные архивные документы

- [Archicad full capability audit — индекс от 28 сентября](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/archicad-full-capability-audit-20260928/research/INDEX_20260928.md) — указывает на capability ledger, execution architecture, GOST attributes, live test matrix
- [GDL Blocker 1 offline forensic audit — 9 октября](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-tn-gdl-create-01-blocker1-audit-20261009/docs/research/APA_TN-GDL-CREATE-01_BLOCKER1_AUDIT_2026-10-09.md) — статус BLOCKED / NOT_VERIFIED; исторические данные не приравнивать к текущему PLN
- [Tapir 1.5.10 upstream contract audit — 9 октября](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-20261009-api-mep-batching-audit/docs/tapir-1510-upstream-contract-audit-20261009.md) — различает опубликованные теги 1.5.8/1.5.9/1.6.0 и локальную версию 1.5.10

### Чего НЕ удалось восстановить

- Полный текст ранее показанного и исчезнувшего отчёта Deep Research не доступен через эти файлы.
- Шесть запланированных файлов независимого аудита **не** были созданы из этого отчёта.
- Нет доказательства, что непушенные локальные файлы сохранились где-либо на GitHub.
- Нельзя автоматически считать сводки/прошлые исследовательские ответы в GitHub независимо верифицированными первоисточниками.

Не удалять/не перезаписывать существующие результаты; ссылаться на них и выполнять только дельта-проверки.

## Current publication status

This branch was created to host the results. The independent Deep Research report has not yet been transferred into this branch; technical findings and the five remaining deliverables are pending. Do not interpret this index as proof that the audit is complete.
