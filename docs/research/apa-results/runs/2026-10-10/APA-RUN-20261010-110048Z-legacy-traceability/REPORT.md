# APA-P50.A01.S01 — первый сквозной traceability проход Research → Plan → Evidence

**ПЛАН:** APA-P50 — Объединение тем, знаний и инструментов.
**ДЕЙСТВИЕ:** APA-P50.A01 — Связи исследований и дедупликация.
**ПОДШАГ:** APA-P50.A01.S01 — Карта связей исследований, S-ID, артефактов и PR.
**RUN_ID:** APA-RUN-20261010-110048Z-legacy-traceability.
**Фаза:** SOURCE. **Статус:** PARTIAL / SOURCE_READ. **Среда:** GitHub read-only + запись только в canonical research branch; Archicad/APX/PLN не запускались.

## Проверенный объём

Через GitHub connector прочитаны **пять обычных Markdown-файлов** непосредственно в каталоге runs/2026-10-10 и один отдельный V2 run с manifest/receipt. Это **не** все исторические исследования в 72 ветках. GitHub blob SHA для пяти файлов получены повторным чтением; содержание их технических выводов здесь независимо не перепроверялось.

| Исходный файл | Git blob SHA | Привязка к S-ID | Проверка связи |
| --- | --- | --- | --- |
| [apa-audit-100141Z-event-contract-7c4e.md](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-10/apa-audit-100141Z-event-contract-7c4e.md) | `a47ef947c91ddc760b4d77e87c186c277893417f` | APA-P00.A03.S01 | EXPLICIT |
| [apa-discovery-20261010-102440-slinktrim-9f2b7.md](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-10/apa-discovery-20261010-102440-slinktrim-9f2b7.md) | `e32d13ffbc5370290bfd42023a5e808fc0947f38` | APA-P10.A01.S01 | EXPLICIT |
| [apa-research-os-audit-user-supplied-20261010.md](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md) | `94cf8986c22839ce51e3983e7e4aa757a66f7c4a` | APA-P00.A03.S01 | EXPLICIT / USER_SUPPLIED |
| [apa-sdk-20261010-102452-get3d-connections-source.md](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md) | `aa3b419f72f2ae130ab5aa01acfb155b58a3053d` | APA-P10.A01.S01 | EXPLICIT |
| [apa-technical-20261010-094254-publisher-layout-01.md](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-10/apa-technical-20261010-094254-publisher-layout-01.md) | `19e1e1ad52b968bc27ef8b2293829df57b512cb4` | APA-P10.A02.S01 | CANDIDATE / NO S-ID |

**Итого по каталогу:** 4/5 flat reports содержат явный S-ID и сопоставлены; 1/5 (Tapir Publisher/Layout) не содержит S-ID, поэтому его связь с APA-P10.A02.S01 — **CANDIDATE, NOT_VERIFIED**, а не окончательная. Для этого отчёта нужна ручная проверка владельца технического направления и ссылка на соответствующую задачу/PR.

## Уже существующие пересечения — не повторять исследование

- **APA-P00.A03.S01:** два документа с разными границами: event contract и переданный владельцем Research OS audit. Это **связанные материалы**, но не подтверждённые дубли.
- **APA-P10.A01.S01:** native Solid Links/Trim/Morph и Get3DInfo/contacts. Это **комплементарные SOURCE находки**; SDK headers/BUILD/LIVE по-прежнему не подтверждены.
- **Tapir Publisher/Layout:** отдельный отчёт уже содержит рекомендации reuse Tapir 1.5.9 и read-only preflight. Не открывать новый экспортёр без проверки этого артефакта и версии установленного APX.
- **APA-P00.A03.S04:** [synthetic V2 run](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-10/APA-RUN-20261010-104437Z-publisher-integration-smoke/REPORT.md) имеет [DONE_PUBLISHED receipt](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json), но это тест publisher, не техническое исследование Archicad.

## Разрывы связей и открытые подзадачи

1. **APA-P00.A01.S03:** опубликован снимок 72 веток/22 PR, но ancestry и unique artifacts ещё NOT_VERIFIED; по одному snapshot нельзя считать весь архив исследованным.
2. **APA-P00.A02.S03:** четыре явных S-ID уже связаны, один legacy отчёт остаётся candidate; полная evidence map и superseded_by не готовы.
3. **APA-P50.A01.S01:** связь проверена только для пяти flat отчётов из текущего дневного каталога и одного V2. Для DONE требуется расширить охват на реестр и архивные ветки; поэтому task остаётся PARTIAL.
4. **APA-P50.A01.S02/S03:** после расширения карты — проверять семантические дубли по work_key/source revision/claim и синтезировать комплементарные исследования, не стирая исходники.
5. Старые ручные receipts пользовательского аудита не равны автоматически сформированным V2 receipts; их provenance хранится отдельно.

## Следующий исполнитель

Читать [PROJECT_PLAN.json](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/PROJECT_PLAN.json), [THEMES.md](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/generated/THEMES.md), этот отчёт и ARTIFACT_REGISTER. Продолжать тот же APA-P50.A01.S01 с новой evidence revision, а не создавать третье исследование с другим ID. Без GitHub receipt нельзя объявлять DONE_PUBLISHED.
