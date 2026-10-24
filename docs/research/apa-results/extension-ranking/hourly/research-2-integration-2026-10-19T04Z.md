# APA AC29 — исследователь №2 — 2026-10-19 04:00 UTC

**30 фактических SOURCE-проверок и два независимых контрааудита.** Новых OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED нет. MODEL_MODE_NOT_VERIFIABLE. Никаких установок, live-операций или изменений main/PLN/APX/кода/плана rev182/очереди №3.

## Прочитано перед исследованием
NEXT_RESEARCH_PRIORITIES.md blob 2cb49edc (последний аудит №3 18.10 20Z), priority_matrix_20261018.json blob 9cb5e6f2, candidates.json blob 87ee1c0b (61 кандидат), свежий №1 19.10 04Z blob 926d9314 и 6 карточек, №2 03Z blob 051ed191; канонический PROJECT_PLAN.json revision182 blob c2ab2f9d только чтение. PR154/159/160/162/165/167/170/173 сверены. Аудита №3 новее 20Z не обнаружено.

## Новые монтажные результаты
1. **Tapir 1.5.9 уже имеет GetPropertyValuesOfAttributes**: `PropertyCommands.cpp:571–677`, input `attributeIds,properties`, output `propertyValuesForAttributes`, per-cell error. Готовая точка чтения свойств атрибутов без нового APX; локальный Tapir1.5.10 не проверен.
2. **Tapir GetPropertyValuesOfElements — другой native путь**, использующий `ACAPI_Element_GetPropertyValuesByGuid`, но не доказано, что он исключает аварийное завершение официального `API.GetPropertyValuesOfElements` на ComposeResult. До независимой проверки — DEFER.
3. **XML схем ведомостей можно читать офлайн**, используя tagged v0.8.0 `read_schedule_scheme`/ `round_trips_exactly`. Но AC29 XML import известен потерей `3D Axonometry` (Graphisoft Community, ноябрь 2025); никакого автоматического импорта.
4. **GDL CLI существует автономно от MCP**: `archicad-gdl build-source` → AC29 `LP_XMLConverter.exe hsf2libpart` → GSM. Нужны точные units, SHA converter и лицензии моделей: `_autoscale` угадывает mm/cm/m по габариту.
5. **IFC QA требует fail-closed**: upstream `run_rules` возвращает score=100, если `scored=[]`; `IfcPropertyRequiredRule` пропускается при отсутствии IFC. APA должен выводить NOT_VERIFIED при нуле реально исполненных обязательных проверок.
6. **PR173 уже содержит сохранённый LIVE batch Hotlink**, 69→119 GUID, 2 roots/48 children, reopenVerified=true. Это не независимая ACCEPTED; очередь №3 устарела.

## Пакет доказательств
- [Матрица 10 способов и критерии ГОТОВО](research-2-integration-2026-10-19T04Z-matrix.md)
- [Проверки 01–10](research-2-integration-2026-10-19T04Z-checks-A.md)
- [Проверки 11–20](research-2-integration-2026-10-19T04Z-checks-B.md)
- [Проверки 21–30](research-2-integration-2026-10-19T04Z-checks-C.md)
- [Контрааудит А: версии/лицензии/API](research-2-integration-2026-10-19T04Z-audit-A.md)
- [Контрааудит Б: монтаж/безопасность](research-2-integration-2026-10-19T04Z-audit-B.md)

## Передача
№3: рассмотреть IFC QA fail-closed, Tapir attribute values, whole-plan inventory, XML scheme read-only, property definition inventory, IFC property QA, Hotlink provenance. №1: искать AC29 build5101 fixes для XML Axonometry и ComposeResult, explicit-unit GDL wrapper, safe attribute property example, independent Mesh/CDT validator. Максимум три внешних звена; никаких вторых исполнителей. SOURCE/OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED строго отдельно.
