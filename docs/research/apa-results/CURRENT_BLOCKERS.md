# APA — текущие блокировки и условия закрытия

Дата исходной сводки: 2026-10-10; Slack coordinator обновлён по проверке 2026-10-11. Остальная таблица основана на [PR #20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [PR #21](https://github.com/dvikt33-ux/safe-bim-layer/pull/21), [PR #16](https://github.com/dvikt33-ux/safe-bim-layer/pull/16), [PR #17](https://github.com/dvikt33-ux/safe-bim-layer/pull/17) и Slack #apa-research. Это не отчёт о независимом live-тестировании.

| Gate | Текущий статус | Условие закрытия |
|---|---|---|
| GDL target identity and encoding | **BLOCKED before write** | Прочитана точная identity, подтверждены presence/placeability, Unicode и отсутствие неоднозначности в нужном PLN; затем отдельно разрешённый тест создания |
| GDL inventory suffix 92 errors | **NOT_VERIFIED cause** | Документирована причина `GetNum`/`Get` или надёжный fail-closed обход без ложной потери объектов |
| Native Model Dump full coverage | **NOT_VERIFIED current live** | Проверено число/типы элементов, учтены 3D filters, негеометрические BIM элементы, последствия для состояния окна |
| Roof surface modify | **BLOCKED live** | Read-only material provenance; затем отдельное разрешение на тест изменения поверхности без изменения Building Material |
| MEP Tapir registration | **NOT_VERIFIED installed APX** | Read-only availability/response установленной версии; запись разрешать отдельно |
| SomeStuff SyncGuids | **NOT_VERIFIED live** | Проверка отмены и `returned_unverified`, независимый readback в одноразовом PLN |
| APA automatic GitHub publisher | **DEPLOYED / SYNTHETIC_E2E_PASS** | [Actions run 38045964668](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668), [receipt](receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json). Для 24/7 исследования отдельно нужны scheduler/heartbeat и два независимых SOURCE runs; legacy index migration pending |
| Slack Socket Mode coordinator | **LIVE_DEPLOYED / BACKFILL_PASS / API_READBACK_PASS** | [LIVE восстановление + HTTP API readback](runs/2026-10-11/apa-sync-live-sqlite-history-recovery-20261011.md): 20 новых событий, 1 дубль, всего 21, 16 task/phase states, 0 effective conflicts, seq1 сохранён; **повторный restart idempotence LIVE_PASS (02:33: accepted=0, duplicates=21, conflicts=0)**; **HTTP-readback после повторного запуска LIVE_PASS** (21 событий, cursor=21, 16 состояний, исходное seq1 сохранено); 3 malformed legacy events **SOURCE_TRIAGE_PUBLISHED** (см. [V2 reconciliation](runs/2026-10-10/APA-RUN-20261010-234200Z-slack-legacy-three-audit/REPORT.md), [receipt](receipts/APA-RUN-20261010-234200Z-slack-legacy-three-audit.json)): broken smoke semantically replaced, publisher summary is GitHub-deployment duplicate, historical audit phase=AUDIT invalid; full 72-branch source reconciliation OPEN. Не равнозначно 24/7 исследованию и автоэкспорту чатов в GitHub |
| PR20 source parity | **NOT_VERIFIED** | Соответствие исходников PR коммиту сборки APX; локальная EOF-правка не должна теряться |
| Historical vs current models | **CONTEXT DEPENDENT** | Проверять PID/порт/PLN/hash и каталог библиотек перед интерпретацией результатов |

## Механизм перехода в READY

Любой пункт получает статус READY только после сохранения в GitHub: точных команд/шагов проверки, версии SDK/API/APX, результата и ссылки на доказательства. Нельзя опираться только на чатовую формулировку или старый GUID/индекс из другого проекта.
