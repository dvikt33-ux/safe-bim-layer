# APA №1 — TRIAD / зоны, маркеры, этажные IFC-ID, ассоциативные связи
**Дата:** 2026-10-23 21:56 UTC (2026-10-24 00:56 МСК). **Режим:** SOURCE-only, no LIVE. **MODEL_MODE_NOT_VERIFIABLE**.

## Влияние на BUILD-01 (#192) — сначала инженерный результат
**Новая ценность:** для двухэтажного контрольного здания обнаружены (а) уже закреплённые в Tapir 1.5.10 read-only контракты для соседства помещений, границ и связей проёмов с зонами, (б) дополнительные готовые upstream-команды Tapir 1.7.1/1.7.2 для маркеров окон/дверей, IFC-идентичности этажей и автоматических зон на неактивном этаже, (в) неустранённый в релизе риск зависания всего JSON API на модальном диалоге перекрывающихся зон. Нативные ассоциативные соединения Archicad 29 автоматически перестраивают зависимую геометрию **внутри Archicad**, но НЕ синхронизируют Rhino/GH. Нового исполнителя/синхронизатора не требуется и не предлагается.
**Гейты:** G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. **SOURCE=27 предметных документарных проверок; OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0 новых.** PR74 имеет исторический 21-элементный LIVE, не новый BUILD-01. FULL_AUTOMATIC_THREE_WAY_SYNC=NOT_PROVEN.

## База и сверка недублирования
- [BUILD-01 #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192), [PR74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74), [TRIAD PIVOT 11Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md).
- [NEXT_RESEARCH_PRIORITIES](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md), [№2 20Z report](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T20Z-triad-report.md), [№2 20Z matrix](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T20Z-triad-matrix.md), [№3 20.10 18Z A](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md) и [B](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-B.md). Более свежий №3 не установлен.
- Матрица 61 прочитана по Git blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`: `count=61`, реально 61 запись, 61 уникальный ID. `GRASSHOPPER` имеет priority 40/100 и решение «ИССЛЕДОВАТЬ_ТОЧКУ_ПОДКЛЮЧЕНИЯ»; это исторический рейтинг, не текущий триадный P0.
- Pinned [Tapir 1.5.10 schema](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json), blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`; это **сохранённый контракт, не текущее состояние APX**. Исторический PROJECT_PLAN rev182 только чтение, в этой сессии не извлечён.
- Уже описанные в 18:56Z `GetQuantitiesOfElements`, `Get3DGeometryOfElements`, Move/Rotate issue #861 НЕ заявляются новыми открытиями.

## 7 карточек (операция → версия/источник/лицензия → направление/контракт → предел → №2)

### C1. Контроль границ и соседства зон без нового writer — НОВАЯ ДЕТАЛИЗАЦИЯ ПРИМЕНИМОГО КОНТРАКТА
**Операция:** после создания двух этажей прочитать площади граничных участков и соседние помещения; сравнить с исходным BIM DAG.
**Версия/источник:** Tapir `GetZoneBoundaries` v1.2.3, присутствует в pinned 1.5.10 (MIT, [upstream](https://github.com/ENZYME-APD/tapir-archicad-automation)); точный schema blob выше.
**Контракт:** READ, вход `zones: Elements` (либо `zoneElementId`, но не оба), ответ `zoneBoundariesOfZones[]` в порядке входа; каждый участок: `connectedElementId`, `isExternal`, `neighbouringZoneElementId`, `area`, `polygonOutline[]`. Вызов списком предпочтителен: дорогой пересчёт границ выполняется один раз на пакет.
**Ограничение:** нет гарантии полной геометрической/нормативной проверки; зона может отсутствовать или иметь ошибочные границы; не заменяет native BREP и требования СП.
**№2:** подготовить read-only ведомость «этаж → зона → граница → смежная зона → ограждение» с ошибками/отсутствующими GUID, без создания зон и изменения SceneWriter.

### C2. Связь окна/двери с помещениями по обе стороны — НОВОЕ ПРАКТИЧЕСКОЕ ПРИМЕНЕНИЕ
**Операция:** проверить, что дверь соединяет ожидаемые помещения, а окно не оказалось на другой стороне перегородки.
**Версия/источник:** Tapir `GetRelationsOfElements` v1.5.7 в pinned 1.5.10, MIT; точный schema blob.
**Контракт:** READ, `elements` обязателен, `otherElementType` опционален; `relations[]` выровнен по входу. Для Window/Door/Skylight/CurtainWallPanel: `openingRelations.fromRoom/toRoom`; для Wall/Beam: `wallConnections/beamConnections`; для Roof/Shell: `roofOrShellRelations.connectedRooms`; для Zone: `zoneRelations`.
**Ограничение:** отношения «слева/справа» не доказывают проходимость, ширину эвакуации или правильность BREP отверстия; не создаёт BIM-элементы и не даёт Rhino↔AC sync.
**№2:** привязать readback отношений к существующим `hostWall`/GUID и отчёту проёмов PR74; не запускать создание/перезапись.

### C3. GDL-маркеры окон/дверей — НОВАЯ ГОТОВАЯ UPSTREAM ФУНКЦИЯ
**Операция:** прочитать и при необходимости менять параметры маркера уже размещённого окна/двери без замены самого проёма.
**Версия/источник:** [Tapir PR #815](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/815), merged 12.10.2026; регистрация v1.7.1, включено в release 1.7.1, доступно в 1.7.2. MIT.
**Контракт:** `GetMarkerParametersOfElements` READ возвращает `libPart` и GDL params (`name/displayName/index/type/value/dimensions/valueDescription/flags`); `SetMarkerParametersOfElements` WRITE изменяет простые scalar параметры по `name` или `index`, оставляя остальные параметры маркера и собственные настройки проёма без намеренного изменения; массивы запрещены.
**Направление:** Archicad JSON API → чтение/запись в Archicad; не Rhino/GH two-way. В pinned 1.5.10 обе команды отсутствуют; **локально недоступность не доказана, но использовать нельзя до разрешённой установки/проверки**.
**Ограничение:** PR изначально был unbuilt/untested; merged/release ≠ подтверждённый AC29 build5101 LIVE. Set — запрещён без отдельного допуска.
**№2:** подготовить только SOURCE-таблицу «маркер → библиотечная деталь → параметры» и сценарий будущего read-only сравнения; не обновлять Tapir.

### C4. IFC GlobalId каждого этажа — НОВЫЙ UPSTREAM ID-КОНТРАКТ
**Операция:** сопоставить этажи native модели с `IfcBuildingStorey` после IFC-публикации G4.
**Версия/источник:** [Tapir PR #802](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/802), merged 12.10.2026; релиз 1.7.1/1.7.2; MIT.
**Контракт:** `GetStories` READ добавляет **необязательное** `stories[].ifcId` (22-character IFC GlobalId) для Archicad 28+; прежние `index/floorId/name/level/height` сохраняются. Pinned 1.5.10 `StoryParameters` поля `ifcId` НЕ имеет.
**Направление:** AC → API → IFC cross-check, не двусторонняя синхронизация. IFC GlobalId ≠ native GUID и не должен заменять `floorId` или `index`.
**Ограничение:** source PR признавал отсутствие DevKit/live на момент открытия; фактическая стабильность `ifcId` после Save/Reopen и Export для AC29 build5101 не проверена.
**№2:** документировать G4 сравнение `GetStories.ifcId` ↔ IFC `IfcBuildingStorey.GlobalId` как условное только после будущего обновления; в текущем 1.5.10 использовать имеющиеся `index/floorId` и IFC readback отдельно.

### C5. Автоматические зоны на другом этаже — НОВАЯ ВЕРСИОННАЯ ПОПРАВКА
**Операция:** создание Zone по `geometry.referencePosition` при неактивном этаже.
**Версия/источник:** [Tapir PR #854](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/854), merged 15.10.2026, включено в 1.7.2 (MIT).
**Контракт:** `CreateZones` WRITE группирует автоматические зоны по `floorIndex`, активирует соответствующий этаж через `APIStory_GoTo`, восстанавливает исходный `actStory`; ответы возвращаются в исходном порядке; при нескольких этажах отдельные undo-шаги. Ручные полигональные зоны не требуют этого.
**Направление:** GH/JSON → Archicad, без обратной записи в Rhino. Pinned 1.5.10 не содержит этого исправления.
**Ограничение:** поведение при активном 3D/Section окне не доказано; переходы этажей — побочный эффект, поэтому readback обязателен.
**№2:** для BUILD-01 пока предпочесть существующие read-only `GetStories` и заранее определённые `floorIndex`; создание зон исключить из обязательного G3 до отдельного допуска.

### C6. Перекрывающиеся зоны могут блокировать ВСЁ API — НОВЫЙ КРИТИЧЕСКИЙ РИСК
**Операция:** повторное `CreateZones` на том же этаже, где зона уже существует.
**Версия/источник:** [upstream issue #822](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/822) воспроизведён на Tapir 1.5.9 / Archicad29 build3200 Win11; [PR #827](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/827) **OPEN** на момент проверки, НЕ входит в release 1.7.2. MIT.
**Контракт:** в старом пути пересечение Zone вызывает модальное окно Archicad; JSON-команда не возвращается, остальные API вызовы блокируются. PR827 предлагает проверку пересечений и `allowOverlap` (default false), но **НЕ ДОСТУПНО в закреплённом APX**. В review обнаружена опасная коллизия с GH `ReplaceExisting`: старые зоны удаляются перед новым Create, что разрушает GUID/связи даже при формальном исправлении модального диалога.
**Направление:** только WRITE AC; не синхронизация. **Не запускать** `CreateZones` или GH `ReplaceExisting` на пользовательском PLN.
**№2:** включить в будущий план G3 правило «никаких повторных CreateZones, при UNKNOWN STOP, read-only inventory, без auto-retry»; не использовать незавершённый PR и не писать обходной синхронизатор.

### C7. Нативные ассоциативные соединения AC29 — ГОТОВЫЙ ВНУТРЕННИЙ МЕХАНИЗМ, НЕ THREE-WAY
**Операция:** при изменении Roof/Wall обновлять геометрию сопряжённых конструкций без самостоятельного пересоздания каждого элемента.
**Версия/источник:** [Graphisoft Archicad 29 — Model Element Connections](https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-269.htm), коммерческая лицензия Archicad.
**Контракт:** внутри AC29 поддерживаются priority-based junctions, Trim to Roof/Shell, Merge Roof/Shell/Morph, SEO, Join Wall↔Curtain Wall. Graphisoft прямо описывает ассоциативное обновление соединённого элемента при изменении исходного.
**Направление:** **только внутренняя AC→AC зависимость**, не AC→GH→Rhino; требует реально созданной/сохранённой связи, материала и корректного типа. Не доказывает сохранение GUID после удаления/пересоздания.
**№2:** для SinglePlane Roof PR74 сравнивать до/после native BREP сопряжённых стен и перечень SEO-связей, не создавать второй updater; сложную MultiPlane Roof не считать принятой.

## 27 предметных SOURCE-проверок (НЕ 27 независимых источников; НЕ тесты)
| № | Проверенный факт / граница | Основание |
|---|---|---|
| 01 | BUILD-01 требует G0→G5 и новый native building, не PR74 replay | issue192 |
| 02 | PR74 описывает исторический 21-элементный двухэтажный прототип | PR74 |
| 03 | TRIAD-PIVOT требует программу/инструмент/ownership, но запрещает новый writer | PIVOT |
| 04 | Матрица 61: 61 записей и 61 уникальный ID | blob61 |
| 05 | Матрица 61: GH — исследовать точку подключения, не считать ACCEPTED | blob61 |
| 06 | pinned schema Tapir 1.5.10 имеет blob e8ad53b6... | PIN |
| 07 | `GetZoneBoundaries` зарегистрирован с версией 1.2.3 | PIN |
| 08 | `GetZoneBoundaries` принимает пакет `zones`, альтернативно single zone | PIN |
| 09 | Ответ границы включает `connectedElementId`, `neighbouringZoneElementId` | PIN |
| 10 | Ответ границы включает `isExternal`, `area`, `polygonOutline` | PIN |
| 11 | Batch предпочтителен по причине единого дорогого пересчёта границ | PIN |
| 12 | `GetRelationsOfElements` v1.5.7 принимает `elements`, optional type filter | PIN |
| 13 | `openingRelations` содержит `fromRoom` и `toRoom` | PIN |
| 14 | `roofOrShellRelations` содержит `connectedRooms` | PIN |
| 15 | Pinned `StoryParameters` имеет `index/floorId/level/name/height`, без `ifcId` | PIN |
| 16 | PR802 добавляет optional story IFC GlobalId для AC28+ | #802 |
| 17 | PR802 не изменяет SetStories и не делает IFC GlobalId native GUID | #802 |
| 18 | PR815 GetMarker возвращает marker libPart + GDL параметры | #815 |
| 19 | PR815 SetMarker изменяет scalar marker параметры, arrays rejected | #815 |
| 20 | Обе marker-команды отсутствуют в pinned 1.5.10 | PIN |
| 21 | PR854 автоматические зоны требуют активации их этажа | #854 |
| 22 | PR854 восстанавливает прежний этаж и имеет отдельные undo группы | #854 |
| 23 | Issue822 фиксирует modal overlap warning, блокирующий JSON API | #822 |
| 24 | PR827 на момент проверки OPEN, `allowOverlap` нельзя считать установленным | #827 |
| 25 | PR827 review описывает риск GH ReplaceExisting delete-before-create | #827 |
| 26 | AC29 native junction/Trim/SEO/Join ассоциативны **внутри Archicad** | GS29 |
| 27 | GH AC29 Deconstruct требует Send Changes, MultiPlane Roof не поддержан | GS-GH29 |

**Обозначения источников:** PIN=[pinned schema](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json); blob61=Git blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`; GS29=[Model Element Connections](https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-269.htm); GS-GH29=[GC.pdf](https://help.graphisoft.com/AC/29/INT/GC.pdf); #802/#815/#854/#827/#822 — ссылки в карточках.

## Контрааудит A — подмена направленной связи трёхсторонней синхронизацией
1. `GetZoneBoundaries`, `GetRelationsOfElements`, `GetStories`, marker GET — AC→API READ; никакой автоматической обратной записи Rhino.
2. Ассоциативное AC→AC обновление — не изменение .3dm/.gh и не восстановление ownership.
3. Grasshopper Deconstruct/Send Changes — не автоматический цикл AC↔GH для всех типов, MultiPlane Roof не поддержан.
4. Native GUID, IFC GlobalId и Rhino Object ID не отождествлять. Сохранение одной строки ID недостаточно.
**Вердикт:** FULL_THREE_WAY_SYNC=NOT_PROVEN, не повышать G2/G3.

## Контрааудит B — надёжность, версии и отсутствие ложного PASS
1. Pinned 1.5.10 содержит GetZoneBoundaries/GetRelations, но **не** marker GET/SET и не story `ifcId`; release 1.7.2 не установлен и не разрешён к установке.
2. PR827 остаётся OPEN; наличие тестовой сборки и GH ReplaceExisting исправления не доказывает безопасности GUID, modal/undo и сохранности библиотек.
3. Issue822 воспроизведён на AC29 build3200 + Tapir1.5.9, **не** на локальном build5101+1.5.10; классификация — риск по аналогии, а не локально подтверждённый баг.
4. Отчёт №2 20Z требует G4 независимого IFC readback и обнаружил missing `GetModelDumpV1` в pinned схеме; текущая находка не устраняет этот блокер.
5. PROJECT_PLAN rev182 не прочитан и не менялся; матрица 61 прочитана; свежий №3 позже 20.10 18Z не доказан.
**Вердикт:** новые знания SOURCE_ONLY, G0 BLOCKED, LIVE/ACCEPTED=0.

## Приоритетное поручение №2 (без исполнения)
**P0:** составить read-only QA-карту BUILD-01 по двум этажам: native `floorId/index` → Zone GUID → boundary polygon/area → connected Wall GUID → Door/Window GUID → `fromRoom/toRoom` → roof/shell connectedRooms; отдельная колонка для IFC GlobalId (NOT_AVAILABLE_PINNED). Проверить, что исходный PR74 не содержит нативных зон: если зон нет, статус `NOT_APPLICABLE`, **не создавать зоны ради проверки**. Указать, какие существующие команды выполняют каждый READ, и где нужны будущие отдельно разрешённые версии/действия. Отдельно занести в G3 риск модального диалога и запрет GH ReplaceExisting.
**Запреты соблюдены:** не создавать writer/synchronizer, не менять main/код/PLN/APX, не устанавливать ПО, не выполнять LIVE, merge, платные API, Work/Codex/Arena. Публикация — только в исследовательскую ветку.
