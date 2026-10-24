# APA №1 — 23.10.2026 18:56 UTC — Tapir 1.7.2 / Cline / Archicad-MCP 0.11.0

## Влияние на BUILD-01

НОВОЕ SOURCE: официальный Tapir 1.7.2 добавил Get3DGeometryOfElements и GH Element3DGeometry для получения полигональных тел Archicad в Rhino/GH, а также нативный CreateCurtainWalls. Это может сократить пробел геометрического readback и дать полноценный Curtain Wall без нового writer. Однако это не BREP и не автоматическая трёхсторонняя синхронизация. В локальной среде APA заявлен Tapir 1.5.10, поэтому новые команды не INSTALLED. Upstream alesdev88/Archicad-MCP 0.11.0 добавил collisions, favorites, library placement, но прямо не проверен на Windows. Cline способен держать два независимых MCP (Rhino + Archicad), но не обеспечивает атомарную синхронизацию.

BUILD-01 issue #192: G0 BLOCKED_RUNTIME; G1 SOURCE_ONLY; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4 NOT_RUN; G5 NOT_RUN. SOURCE=30 технических проверок, OFFLINE=0, BUILD=0, INSTALLED=0, LIVE=0, ACCEPTED=0 для нового маршрута. FULL_THREE_WAY_SYNC=NOT_FOUND_IN_CHECKED_SOURCES. Не изменялись main, код, PLN/APX, установки, NEXT, PROJECT_PLAN, PR и лицензии.

## 30 предметных SOURCE-проверок

Это 30 отдельных технических утверждений, не 30 независимых сайтов, не 30 локальных испытаний. Источники — официальные upstream release notes/PR и внутренний прочитанный отчёт №2.

| ID | Проверенное утверждение / ограничение | Первоисточник |
|---|---|---|
| S01 | Tapir 1.7.2 выпущен 19.10.2026, локально у APA указан 1.5.10; новые функции нельзя считать установленными. | [T](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.2) |
| S02 | Релиз Tapir 1.7.2 включает Get3DGeometryOfElements и GH Element3DGeometry. | [T](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.2) |
| S03 | Тот же релиз включает GetQuantitiesOfElements и SaveCurrentWindowAsImage. | [T](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.2) |
| S04 | Get3DGeometryOfElements возвращает вершины тел в мировых координатах и индексы полигональных граней. | [G](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/865) |
| S05 | Грани поддерживают наружный контур и отверстия; это полигональные данные, не true BREP. | [G](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/865) |
| S06 | Для грани заявлен surfaceId при наличии проектного атрибута поверхности. | [G](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/865) |
| S07 | Для Stair/Railing/Curtain Wall описано включение геометрии подэлементов. | [G](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/865) |
| S08 | GH Element3DGeometry формирует Rhino Mesh по GUID и сообщает ошибки на входной элемент. | [G](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/865) |
| S09 | Автор PR865 прямо отмечает отсутствие BREP output и per-face coloring в GH-компоненте. | [G](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/865) |
| S10 | PR865 на стадии бота описан как не собранный с DevKit; после merge видны CI checks, но Windows AC29 BUILD-01 live не подтверждён. | [G](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/865) |
| S11 | Старые MoveElements/RotateElements могли возвращать NoError при отсутствии реального изменения на locked/hidden layers. | [M](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/861) |
| S12 | PR861 добавил per-element editability checks с отказом для locked/hidden layer и недоступного GUID. | [M](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/861) |
| S13 | Для PR861 описан отдельный manual test, но upstream запросил его ручной запуск. | [M](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/861) |
| S14 | CreateCurtainWalls появился в Tapir 1.7.2 как создание нативного Curtain Wall по 2D polyline. | [W](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/867) |
| S15 | CreateCurtainWalls принимает curtainWallsData.coordinates, остальные поля могут использовать Favorite/defaults. | [W](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/867) |
| S16 | Поддерживаются primaryPattern, secondaryPattern и cells с классами панелей и рам. | [W](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/867) |
| S17 | Автор PR867 сообщает AC29 macOS live и readback child panels/bbox; Windows не заявлен. | [W](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/867) |
| S18 | PR867 прямо исключает ModifyCurtainWalls, curved segments и создание новых panel/frame classes. | [W](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/867) |
| S19 | alesdev88 Archicad-MCP v0.11.0 выпущен 23.10.2026 12:38 UTC, pin Tapir 1.7.2. | [A](https://github.com/alesdev88/Archicad-MCP/releases/tag/v0.11.0) |
| S20 | v0.11.0 добавил learn_library_part/record_library_part/list_library_part_records для ориентации GDL. | [A](https://github.com/alesdev88/Archicad-MCP/releases/tag/v0.11.0) |
| S21 | v0.11.0 принимает placement для объектов, окон и дверей через footprint/hinge/swing ориентиры. | [A](https://github.com/alesdev88/Archicad-MCP/releases/tag/v0.11.0) |
| S22 | v0.11.0 добавил find_collisions и правило no-collisions на Tapir GetCollisions. | [A](https://github.com/alesdev88/Archicad-MCP/releases/tag/v0.11.0) |
| S23 | v0.11.0 добавил apply_favorites с dry-run, сохранением Element ID и отчётом изменённых полей; ID не GUID. | [A](https://github.com/alesdev88/Archicad-MCP/releases/tag/v0.11.0) |
| S24 | Разработчик v0.11.0 отмечает отсутствие испытаний на Windows и части новых предупреждений в live create. | [A](https://github.com/alesdev88/Archicad-MCP/releases/tag/v0.11.0) |
| S25 | v0.10.0 поддерживает classification, GDL и marker properties с dry-run/readback; AC29 property read crash остаётся риском. | [A10](https://github.com/alesdev88/Archicad-MCP/releases/tag/v0.10.0) |
| S26 | Cline официально поддерживает несколько local STDIO MCP servers в mcpServers через command/args. | [C](https://github.com/cline/cline/blob/main/docs/mcp/mcp-overview.mdx) |
| S27 | Cline рекомендует autoApprove только для безопасных инструментов, конфигурация допускает пустой список. | [C](https://github.com/cline/cline/blob/main/docs/mcp/mcp-overview.mdx) |
| S28 | Cline имеет Apache-2.0 лицензию; это не лицензия модели или API. | [CL](https://github.com/cline/cline/blob/main/LICENSE) |
| S29 | lgradisar/archicad-mcp поддерживает readonly/safe/all, ARCHICAD_PORT, bundled Tapir definitions 1.5.9. | [L](https://github.com/lgradisar/archicad-mcp) |
| S30 | №2 18Z подтвердил на pinned Tapir различие Wall relative zCoordinate и Slab absolute level, а также удаление holes при неосторожном ModifySlabs. | [I](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T18Z-triad-report.md) |

## Шесть карточек готовых решений / версионных обновлений

### C1856-01 P0 — Cline как общий MCP-клиент (SOURCE_ONLY)
Операция: агент в Cline выбирает инструмент Rhino MCP для геометрии и отдельный Archicad MCP для read-only проверки. Первоисточники: [Cline](https://github.com/cline/cline/blob/main/docs/mcp/mcp-overview.mdx), [McNeel Rhino MCP](https://mcneel.github.io/RhinoAI/docs/getting-started/), [lgradisar](https://github.com/lgradisar/archicad-mcp). Версии/лицензии: Cline Apache-2.0; Rhino MCP MIT; lgradisar MIT; требуются Rhino8 и AC29. Контракт: два независимых local STDIO MCP, один AI-клиент; нет встроенной атомарной операции и общего GUID. Риск: неверное окно Rhino/порт AC, произвольный write tool, конфликт двух writers. №2: составить без установки конфигурационный маршрут с autoApprove пустым, фиксированными PLN/.3dm/портом и списком read-only инструментов.

### C1856-02 P0 HOLD_VERSION — Get3DGeometryOfElements + GH Element3DGeometry (SOURCE_ONLY)
Операция: AC29 → JSON vertex/face loops/holes/surfaceId → GH Mesh для геометрической сверки. Первоисточник: [Tapir PR865](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/865), [релиз 1.7.2](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.2). Лицензия Tapir MIT. Ограничения: нет BREP; AC29 Windows не проверен; installed Tapir 1.5.10 не квалифицирован; не доказано сохранение GUID при GH→AC write. №2: составить таблицу сравнения Get3DBoundingBoxes / mesh / native BREP; G0 read-only inventory, не устанавливать APX.

### C1856-03 P0 HOLD_VERSION — защита Move/Rotate от ложного NoError (SOURCE_ONLY)
Операция: MoveElements/RotateElements при locked/hidden layers → отказ по элементу вместо успеха без движения. [PR861](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/861), Tapir 1.7.2, MIT. Ограничение: upstream manual test не является нашим Windows LIVE. №2: предусмотреть координатный readback после любого MOVE/ROTATE на старой версии; при UNKNOWN — STOP, не повторять CREATE.

### C1856-04 P1 HOLD_VERSION — CreateCurtainWalls нативно (SOURCE_ONLY)
Операция: GH-generated polyline/pattern → Tapir CreateCurtainWalls → Archicad Curtain Wall с child panels/frames. [PR867](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/867), Tapir 1.7.2 MIT, upstream AC29 macOS LIVE. Контракт: curtainWallsData.coordinates, favoriteName, zCoordinate, floorIndex, height, primaryPattern, secondaryPattern, cells. Ограничения: нет ModifyCurtainWalls/curved segments/new panel classes; Windows и установленная 1.5.10 не проверены. №2: подготовить отдельный необязательный CW сценарий с child GUID readback, без второго writer.

### C1856-05 P1 HOLD_VERSION — alesdev88 Archicad-MCP v0.11.0 (SOURCE_ONLY)
Операция: find_collisions/no-collisions для QA, apply_favorites dry-run, placement по направлению петли/створки, learn_library_part для определения ориентации. [Релиз 0.11.0](https://github.com/alesdev88/Archicad-MCP/releases/tag/v0.11.0), MIT, Tapir 1.7.2. Ограничения: не тестировался на Windows; learn_library_part временно размещает и удаляет элементы (НЕ read-only); create/modify конкурируют с SceneWriter. №2: изучить QA-only маршрут и запретить все writes в APA-owned BIM до отдельного допуска.

### C1856-06 P0 MINIMAL — lgradisar MCP read-only discovery (SOURCE_ONLY)
Операция: ARCHICAD_MCP_MODE=readonly, ARCHICAD_MCP_SEARCH=1, ARCHICAD_PORT pinned → TestConnection/search_tools/call_tool только чтения. [README](https://github.com/lgradisar/archicad-mcp), MIT; bundled definitions 1.5.9, installed 1.5.10 отличается. Ограничения: schema ≠ runtime, readonly не выполняет запись, автоматическое переключение инструментов не подтверждено на ПК. №2: документировать проверку порта/версии/command inventory, не выполнять LIVE.

## Контрааудит A — источники, лицензии, версии

- Tapir 1.7.2 (19.10.2026) и alesdev88 0.11.0 (23.10.2026) реально опубликованы; локальная 1.5.10 не обновлена и не исследована на наличие этих новых команд. SOURCE ≠ INSTALLED.
- PR865 прямо признаёт отсутствие BREP и первоначальную неопределённость DevKit; upstream CI не равен local AC29 Windows acceptance. PR867 upstream LIVE только AC29 macOS. alesdev 0.11.0 Windows NOT_TESTED.
- Cline Apache-2.0, Tapir/lgradisar/alesdev MIT; McNeel Rhino MCP бесплатен как мост, но Rhino/Archicad требуют свои лицензии. Никакой платный API не включался.
- Прочитаны [issue192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192), [PR74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74), [№2 18Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T18Z-triad-report.md), NEXT_RESEARCH_PRIORITIES (blob 6f074693360231c5cb42ada815984a6b0dd504c0), матрица 61 (blob 9cb5e6f2a59f80762cc77073eeb10404829af75a), pivot 11Z (blob 896fa3af0953468ca58fca710f32cb926504f582) и последний доступный №3 20.10 07Z (blob 40742adbf7ec945b31d125aac6912d95e5f07920). Исторический PROJECT_PLAN rev182 не изменён, прямой файл не извлечён.

## Контрааудит B — реальная инженерная применимость

- Единственный writer BUILD-01 — PR74/DynamicCommands→BIM Graph→SceneWriter/SQLite. Cline с двумя MCP не даёт атомарного cross-app commit; direct GH native write и сторонний MCP create_elements для APA-owned элементов запрещены без допуска.
- Tapir 1.7.2 Get3DGeometry выдаёт полигональные тела/holes, но не точный BREP. Проверка GUID/host/material/story/library/Save-Close-Reopen остаётся обязательной. Mesh нельзя выдавать за исходную CAD BREP.
- Старый Tapir Move/Rotate может вернуть NoError без движения: требуется независимое чтение координат/GUID и запрет повтора CREATE после UNKNOWN.
- alesdev v0.11.0 find_collisions — QA-утилита, не нормативная проверка СП и не доказательство корректных конструктивных соединений. learn_library_part пишет временные объекты; его нельзя считать чистым чтением.
- Из [№2 18Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T18Z-triad-report.md) следует риск удвоения Z стены второго этажа и потери holes при ModifySlabs. Новые MCP не исправляют семантику старого authored компилятора автоматически.
- В [alesdev README](https://github.com/alesdev88/Archicad-MCP) зафиксирован риск аварии AC29 при GetPropertyValuesOfElements даже на одном элементе; не выполнять property-read на несохранённом оригинале.

## Адресная передача №2

Сначала G0 read-only: версии/порт/PLN/Rhino8 build, локальный Tapir command inventory, существующий SceneWriter; затем G1 GH→jSwan→typed JSON с раздельными Z semantics и сохранением Slab holes. Отдельно подготовить SOURCE-only сценарии mesh-readback, native CW, collisions и favorites для будущего разрешённого обновления, без нового writer/router. Ни одного локального изменения.

MODEL_MODE_NOT_VERIFIABLE.
