# APA №2 — TRIAD / BUILD-01 — 2026-10-23 19Z

## Конкретный вклад в ворота BUILD-01

**G2 / P0: обнаружена двухверсионная развилка для нативного материала перекрытий.** Закреплённая схема локального кандидата Tapir **1.5.10** (262 команды; Git blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`) содержит у `CreateSlabs` поля `favoriteName,level,thickness,referencePlaneLocation,polygonCoordinates,polygonArcs,holes,floorIndex`, но **НЕ** `structureType/buildingMaterialId/compositeId`. Upstream Tapir **1.7.1** (PR #785) добавил эти три поля в CreateSlabs; 1.7.2 сохранил изменение. **Нельзя отправлять новый payload в локальную 1.5.10** или утверждать, что она обновлена. Для BUILD-01 сейчас допустим только ранее существовавший путь `Favorite` либо **две независимо разрешённые записи** `CreateSlabs → GUID/readback → ModifySlabs → readback` через тот же SceneWriter/SQLite. Альтернатива с 1.7.2 — лишь отдельная будущая квалификация, НЕ установка в этом цикле.

**G2/G3 / P0: Tapir Grasshopper не является безобидным «визуальным читателем».** Upstream PR #615 (в релизе 1.5.9) добавил `EmbedMetadata` (по умолчанию true) и `ReplaceExisting` (по умолчанию false) для GH Create-компонентов. Первый создаёт/пишет свойства `Tapir GH`; повторный Create при false дублирует элементы; true после создания удаляет прежние элементы по `Component Guid`, что может удалить дочерние проёмы стен. Отказы записи метаданных могут быть предупреждениями, а не блокирующими ошибками. Поэтому **не использовать GH Create* для APA-owned GUID** и не считать Graphisoft `Synchronize=false` общей блокировкой всех иных писателей.

**G4 / P0: Tapir 1.7.2 добавил `Get3DGeometryOfElements` + GH `Element3DGeometry` (PR #865).** Ответ — тела с вершинами/полигонами/отверстиями/поверхностями, GH выдаёт Rhino **Mesh**, а не BREP. Команда отсутствует в закреплённом каталоге 1.5.10 и не является независимым BREP reader: это тот же provider. Поэтому **G4 независимый BREP = NOT_FOUND**, даже если впоследствии будет разрешён переход на 1.7.2.

## Контракт одного исполнителя (не новый writer/router)

`Rhino 8 (.3dm) → Grasshopper 1 (.gh) → явные BIM-поля/единицы/story → jSwan JSON staging + SHA256 → PR74 compile_authored_intent → BIM Graph/DynamicCommands → SceneWriter/SQLite → Tapir 1.5.10 → Archicad 29`.

В Rhino/GH допускается подготовка параметров, контуров, скатов и независимый предварительный расчёт. **Точная автоматическая сериализация произвольной GH-геометрии в полный `apa-authored-project/1` без ручного сопоставления типов НЕ ДОКАЗАНА**. В PR74 `brief.targetProjectPath` сверяется с охраняемым `RUN.EXPECTED_PATH`; новый scratch путь должен быть привязан штатной `bind_authorized_saved_copy` с фактическим SHA256 и разрешением. Ни один локальный preflight не запускался.

После завершения GH-операции: остановить solver/автообновления, записать `.3dm/.gh/staging.json` и SHA, read-only проверить схемы, этажи/атрибуты/хозяев; передать **только** уже существующему PR74. Затем независимое чтение GUID, BIM-типа, story/host, материала, геометрии; GuardedSave/Close/Open и повторное чтение **лишь после отдельного G3-допуска**. В обратном направлении Archicad→GH возможны ограниченные Deconstruct/Send Changes и, в будущем, Tapir Mesh; это не доказательство полного AC→Rhino→GH→AC round-trip с тем же GUID.

## Версии и лицензии — проверено SOURCE

- Graphisoft **Grasshopper–Archicad 29 Live Connection build 3000**, Windows, Rhino 7/8, дата 01.10.2025: https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/ ; бесплатное дополнение, но Archicad/Rhino лицензируются отдельно. **AC29 build 5101 + локальная установка не проверены.**
- Tapir **1.5.10** — pinned SOURCE snapshot в APA, но не доказанный фактически загруженный APX. MIT: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/LICENSE . Upstream **1.7.1** добавил поля CreateSlabs: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785 ; **1.7.2**, релиз 19.10.2026, добавил geometry mesh: https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.2 . Provider version != installed contract.
- jSwan MIT: https://github.com/andrewheumann/jSwan/blob/master/LICENSE ; точная Rhino8 binary compatibility NOT_VERIFIED. Rhino 8 требует отдельной лицензии.
- McNeel Rhino MCP Platform v0.3.0 от 29.09.2026, Yak `rh8_19-win`: https://rhinopackages.github.io/package/Rhino-MCP-Platform ; исходники MIT: https://github.com/mcneel/RhinoAI/blob/rhino-9.x/LICENSE . Позволяет управлять Rhino/GH, **не даёт BIM sync**, имеет риск неправильного окна при нескольких Rhino: https://mcneel.github.io/RhinoAI/docs/troubleshooting/ . Установка и запуск MCP не выполнялись.

## Воспроизводимый безопасный маршрут G0→G5

1. **G0 READ ONLY:** подтвердить фактический Archicad build/port/PLN, `GetProjectInfo`, `GetStories`, `GetAddOnVersion`, `IsAddOnCommandAvailable`, APX SHA, регистрацию/схему конкретных команд, Rhino8 build/окно/.3dm, GH definition, Graphisoft connection build. Не принимать совпадение имени файла вместо identity tuple. **ГОТОВО = RUNTIME_READY receipt. Сейчас BLOCKED.**
2. **G1:** на новом разрешённом scratch получить `GetStories` и материалы/Favorites, подготовить `apa-authored-project/1` с двумя этажами, полным typed DAG, hostWall ссылками, `planHash`; исполнить только read-only preflight. **ГОТОВО = фактический OFFLINE_PASS. Сейчас NOT_RUN.**
3. **G2:** по каждому Create/Modify проверить installed schema; Wall `floorIndex` + `zCoordinate` как offset, Slab `level` как абсолютную Z; `ModifySlabs.polygonOutline` обязан повторить `holes`; material/structure проверить native readback. Roof MultiPlane нативно существует, но PR74 authored не подключён; не выдавать за готовое. **ГОТОВО = typed contract + approvals. Сейчас SOURCE_ONLY.**
4. **G3:** только отдельный допуск владельца для новой PLN/port/planHash. SQLite intent-before-write, один SceneWriter; UNKNOWN → STOP/READ reconciliation, не повторять CREATE. **NOT_AUTHORIZED.**
5. **G4:** GuardedSave→Close→Open→новая инвентаризация GUID/host/story/material/BREP и независимый геометрический источник; Mesh из Tapir 1.7.2 не заменяет независимый BREP. **NOT_RUN.**
6. **G5:** второе отличное задание и отдельная scratch PLN; проверка отсутствия привязки к старому fixture. **NOT_RUN.**

## Нормативные и геометрические ограничения

Rhino/GH допускает вычислительные ограничения (размеры/уклоны/высоты/радиусы/коллизии), но ни один plugin не доказал автоматическую нормативную экспертизу здания. Фиксировать версию СП, правило, исходные параметры, проверку и независимый audit; `GetCollisions` не равен полной BREP/нормативной приёмке. Отсутствие видимой коллизии при отключённом `Participates in Collision Detection` не является доказательством. Не утверждать ускорение 100× без benchmark.

## Доказательность и границы

Новых модельных тестов нет: **SOURCE = 30 предметных сверок** (см. checks; не 30 разных репозиториев), **OFFLINE=0, BUILD=0, INSTALLED=0, LIVE=0, ACCEPTED=0**. Два контрааудита — в отдельном файле. `FULL_THREE_WAY_SYNC=NOT_FOUND`. Исторический PR74 21-элементный прототип не является BUILD-01. Отчёты №1/№3 прочитаны, но не подменяют первоисточники. Исторический PROJECT_PLAN rev182 не изменялся; исходный rev182 в этом цикле не извлекался. 06Z остаётся PARTIAL_NOT_ACCEPTED, без реконструкции отсутствующего оригинала. Никаких изменений main/NEXT/кода/PLN/APX/установок/PR merge. MODEL_MODE_NOT_VERIFIABLE.
