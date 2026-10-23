# APA — восстановленный отчёт: MEP Designer, маршруты, порты и полнота графа

**ПЛАН:** APA-P10 — Независимый технический аудит AC29. **ДЕЙСТВИЕ:** APA-P10.A02 — Инструменты и интеграции. **ПОДШАГ:** APA-P10.A02.S04 — native MEP и Tapir.

- Дата оригинального ответа: **2026-10-10**; тип: **RECOVERED_FROM_CHAT**, ранее `GITHUB_PUBLISH_BLOCKED`.
- Указанный оригиналом source: [Tapir 1.5.9 commit d0dbb11](https://github.com/ENZYME-APD/tapir-archicad-automation/tree/d0dbb11b13942e014661e1402b07958b70cd9dba).
- Исходные статусы: SOURCE_VERIFIED, **7/7 SYNTHETIC PASS — REPORTED**, LIVE NOT_VERIFIED.
- Независимое повторное исполнение synthetic tests в этом акте публикации: **нет**. Локальный изменённый Tapir 1.5.10: NOT_VERIFIED.

## Гипотеза 1 — тихие пропуски в MEP readback

По прежнему отчёту функции `GetMEPElements`, `GetMEPRoutingElements`, `GetMEPPorts` способны продолжить обработку при ошибке извлечения элемента, узла маршрута, сегмента или порта. В частности, конструкции с `continue` могут возвращать корректный JSON неполной инженерной модели без записи причин пропуска. Дополнительно в `GetMEPElements` предположительно не проверяется результат `ACAPI_Element_GetElemList`.

**Source для независимого аудита:** [Tapir 1.5.9 MEPCommands.cpp строки 232–491](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/MEPCommands.cpp#L232-L491), [SDK 29.3100 MEP Element](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_element.html).

**Для MVP:** не писать новый MEP writer. Сначала добавить внешний completeness gate: `elementId -> expectedPortIds -> returnedPortIds -> physical connections`; если независимый список ожидаемых портов отсутствует, `NOT_VERIFIED`, а не PASS. Невозможно исправить скрытую ошибку простым `succeeded: true`.

## Гипотеза 2 — MEP system membership != physical topology

Сообщённый анализ `GetMEPDistributionSystems` показывает отсутствие в её JSON-ответе полного графа физических портов. Возможны `Unknown` для MEP domain и пустая выборка `elements` после ошибок без явного кода ошибки. Физическая топология — отдельный слой, определяемый порт-порт соединениями.

**Источники:**
- [Tapir 1.5.9, GetMEPDistributionSystems](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/MEPCommands.cpp#L536-L570)
- [Graphisoft AC29.3100 PortBase](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_port_base.html)
- [Graphisoft AC29.3100 DistributionSystemsGraph](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_distribution_systems_graph.html)
- [Graphisoft AC29.3100 DistributionSystem](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_distribution_system.html)

Системная принадлежность не доказывает соединение труб. `connectedPortId`, `connectedElementId` и `isPhysicallyConnected` требуют взаимной согласованности. По предыдущему анализу домен порта может не совпадать с доменом целого оборудования.

## Reported synthetic checks

Оригинал сообщил 7/7 PASS для: взаимно связанных портов; isConnected без link; соседний порт отсутствует в выборке; несовпадение обратных ссылок; несовпадение флагов connected; отсутствие expected порта; два несвязанных элемента в одной системе. Это synthetic classification checks, **не** гарантия runtime Tapir.

## Архитектура A vs B

| Критерий | A — Tapir + внешняя graph validation | B — C++ MEP native graph adapter |
|---|---|---|
| Готовые операции | Tapir команды | Нужна нативная реализация |
| Физические связи | `GetMEPPorts` и readback | Нативный `DistributionSystemsGraph` |
| Проверка полноты | Требуется внешний эталон | Можно возвращать expected GUID и ошибки |
| Новая сборка | Не требуется для валидатора | Да |
| Время/производительность | NOT_MEASURED | NOT_MEASURED |

**Выбор MVP:** A, пока read-only опыт не докажет необходимость B.

## Read-only тест / аудит

В изолированном AC29 проверить зарегистрированные команды установленного APX, прочитать GUID маршрутов/портов/систем и сверить их со списками SDK. PASS — все ожидаемые порты присутствуют, пары обратных ссылок согласованы, пропуски явно отражены; FAIL — независимое расхождение; NOT_VERIFIED — нет контролирующего источника. Сборка/запись PLN НЕ допускаются этим отчётом.

**Вопрос аудитору:** хватит ли `GetMEPPorts` + `GetMEPDistributionSystems` установленной 1.5.10 для доказуемого графа либо нужен минимальный read-only bridge с per-port error reporting?

**Безопасность:** отчёт восстановлен из беседы без новых LIVE-вызовов, изменений PLN, APX, main.
