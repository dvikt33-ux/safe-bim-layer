# APA — восстановление исследования Tapir: разрезы, ассоциативные размеры, автотекст

- **Дата восстановления:** 2026-10-10
- **Provenance:** `RECOVERED_FROM_CHAT` — текст и выводы из предыдущего видимого отчёта ChatGPT, ранее не опубликованного в GitHub.
- **Run ID исходного отчёта:** `APA-RUN-20261010-132440Z-TAPIR-DOCS-7C3F`
- **ПЛАН:** APA-P10 — Независимый технический аудит Archicad 29
- **ДЕЙСТВИЕ:** APA-P10.A02 — Инструменты и интеграции
- **ТЕКУЩИЙ ПОДШАГ:** APA-P10.A02.S01 — происхождение и API Tapir
- **Статусы:** SOURCE=`REPORTED_FROM_PRIOR_CHAT`; OFFLINE=`NOT_RUN`; BUILD=`NOT_RUN`; LIVE=`NOT_VERIFIED`; PERFORMANCE=`NOT_MEASURED`
- **Цель восстановления:** предотвратить потерю уже сформулированных результатов и передать их независимому аудитору. Никакой новый LIVE PASS не заявляется.

## Источник и версия

Tapir, публичный тег `1.5.9` (в предыдущем отчёте указан release commit `d0dbb11`), лицензия MIT:
- https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.5.9
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/LICENSE
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/README.md

**Ограничение:** установленный у пользователя Tapir 1.5.10 не приравнивать к тегу 1.5.9; источник точной локальной сборки и идентичность команд не подтверждены. Предыдущий отчёт сообщил GitHub 404 для ref 1.5.10; повторная независимая проверка здесь не выполнена.

## Находка 1 — GetSectionElements + CreateAssociativeDimensionsOnSection

**Источник, конкретные проверявшиеся разделы:**
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp#L230-L374 — `GetSectionElementsFromCurrentDatabase`, `GetSectionElementsCommand::Execute`.
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp#L4987-L5144 — `CreateAssociativeDimensionsOnSectionCommand`, `dimensionsData`, создание точек/размеров.
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Examples/get_section_elements.py — пример Python.

**Факт, сообщённый предыдущим аудитом:** чтение изображения разреза даёт `sectionElementId`, `ownerElementId` и при наличии `ownerElementType`; для размеров доступны presets `WallCompositeFaces`, `WallSkinBorders`, `SlabCompositeFaces`, `SlabSkinBorders`, `BeamOrColumnRefLineEndPoints`, `BeamOrColumnBoundingBoxCorners`, `DoorWindowWallHoleCorners`, `DoorWindowModelHotspots`. Несколько `sectionElementIds` могут образовать общую цепочку.

**Риск:** чтение может переключать базу данных вида, а команда создания размеров, по предыдущему анализу, не переключает её явно. Пример может зависеть от активного окна. Обязательно read-only проверка контекста базы до writer-теста. Не путать GUID изображения с GUID исходного BIM-элемента.

**Решение:** интегрировать выборочно; не писать собственный генератор точек до проверки штатных presets.

## Находка 2 — GetAutoTextKeys / GetAutoTextName

**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp#L205-L400 (`GetAutoTextKeysCommand`, `GetAutoTextNameCommand`, `ResolveAutoTextName`).

**Ранее сообщённый факт:** `ACAPI_AutoText_GetPropertyAutoTextKeyTable` возвращает пары `name → key`, с фильтром по элементу; ключи свойств имеют вид `PROPERTY-<GUID>`; имя может разрешаться через `ACAPI_Property_GetPropertyDefinition`. Это ключи, не уже вычисленные значения свойств.

**Решение:** интегрировать штатный автотекст, не разрабатывать свой движок динамических подписей. Риски: применимость свойств, обновление label, поведение разных типов текста — LIVE NOT_VERIFIED.

## Находка 3 — GetDimensionData

**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp#L5895-L6050 (`GetDimensionDataCommand::Execute`).

**Ранее сообщённый факт:** через `ACAPI_Element_Get` и `ACAPI_Element_GetMemo` считываются `direction`, `dimensionLinePosition`, `coordinate`, `coordinate3D`, `dimensionPosition`, `dimensionValue`, `witnessForm`, `witnessVal`, `baseElementId`, а также привязки `line/inIndex/special/nodeType/nodeStatus/nodeId`. Заявлена проверка типа `API_DimensionID`; покрытие иных типов размеров не доказано.

**Решение:** брать готовое чтение, не восстанавливать выносные точки заново по геометрии.

## Сравнение архитектуры

| Вариант | Достоинства | Риски | Выбор |
|---|---|---|---|
| Native Model Dump | Геометрия/материалы/этажи уже реализованы | Не охватывает все данные 2D-разрезов и размеров | Сохранить |
| Tapir Section/Dimension | Штатные привязки и готовые размерные presets | Разные базы данных; локальная версия не проверена | Интегрировать после read-only gate |
| Tapir AutoText | Динамические ключи свойств | Значения/отображение на конкретных label не проверены | Интегрировать |
| Свои генераторы размеров/автотекста | Полный контроль | Большое дублирование и затраты | Отклонить для MVP |

## Следующее испытание / технический вопрос

Можно ли в установленном Archicad 29 build 5101 / Tapir 1.5.10 **без записи в PLN** прочитать `GetSectionElements`, `GetDimensionData`, `GetAutoTextKeys`, `GetAutoTextName` и проверить базу данных и GUID? Только после независимой read-only проверки разрешать создание ассоциативных размеров на изолированном тестовом PLN.

## Передача независимому аудитору

1. Заново прочитать указанные участки исходников **именно 1.5.9** и проверить регистрацию команд.
2. Сопоставить сборку 1.5.10 с опубликованным исходником, запросить подтверждение binary provenance.
3. Проверить active database при `CreateAssociativeDimensionsOnSection`.
4. Проверить значения/свойства и наличие `ownerElementType`.
5. Обновить SOURCE до `SOURCE_VERIFIED` только после нового независимого чтения. Не повышать OFFLINE/BUILD/LIVE по этому recovered-тексту.

**Сохранность результата ≠ подтверждение технической истинности; факт GitHub commit/readback фиксируется вне этого файла, чтобы не создавать самоссылку.**
