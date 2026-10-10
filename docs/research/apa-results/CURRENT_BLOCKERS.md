# APA — текущие блокировки и условия закрытия

Дата: 2026-10-10. Сводка основана на [PR #20](https://github.com/dvikt33-ux/safe-bim-layer/pull/20), [PR #21](https://github.com/dvikt33-ux/safe-bim-layer/pull/21), [PR #16](https://github.com/dvikt33-ux/safe-bim-layer/pull/16), [PR #17](https://github.com/dvikt33-ux/safe-bim-layer/pull/17) и Slack #apa-research. Это не отчёт о независимом live-тестировании.

| Gate | Текущий статус | Условие закрытия |
|---|---|---|
| GDL target identity and encoding | **BLOCKED before write** | Прочитана точная identity, подтверждены presence/placeability, Unicode и отсутствие неоднозначности в нужном PLN; затем отдельно разрешённый тест создания |
| GDL inventory suffix 92 errors | **NOT_VERIFIED cause** | Документирована причина `GetNum`/`Get` или надёжный fail-closed обход без ложной потери объектов |
| Native Model Dump full coverage | **NOT_VERIFIED current live** | Проверено число/типы элементов, учтены 3D filters, негеометрические BIM элементы, последствия для состояния окна |
| Roof surface modify | **BLOCKED live** | Read-only material provenance; затем отдельное разрешение на тест изменения поверхности без изменения Building Material |
| MEP Tapir registration | **NOT_VERIFIED installed APX** | Read-only availability/response установленной версии; запись разрешать отдельно |
| SomeStuff SyncGuids | **NOT_VERIFIED live** | Проверка отмены и `returned_unverified`, независимый readback в одноразовом PLN |
| Slack Socket Mode coordinator | **NOT_DEPLOYED** | Реальный daemon + credentials + приём/дедупликация событий; offline 18/18 не считать live |
| PR20 source parity | **NOT_VERIFIED** | Соответствие исходников PR коммиту сборки APX; локальная EOF-правка не должна теряться |
| Historical vs current models | **CONTEXT DEPENDENT** | Проверять PID/порт/PLN/hash и каталог библиотек перед интерпретацией результатов |

## Механизм перехода в READY

Любой пункт получает статус READY только после сохранения в GitHub: точных команд/шагов проверки, версии SDK/API/APX, результата и ссылки на доказательства. Нельзя опираться только на чатовую формулировку или старый GUID/индекс из другого проекта.
