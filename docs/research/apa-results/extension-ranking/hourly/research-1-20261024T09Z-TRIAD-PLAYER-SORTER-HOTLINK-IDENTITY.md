# APA №1 | 2026-10-24 09Z | BUILD-01: штатный GrasshopperPlayer, Beam/Column Sorter и пределы Rhino/Hotlink

## 0. Реальное влияние на трёхстороннюю сборку BUILD-01 (#192)

**P0-дельта 1 (готовый выбор/вызов инструмента):** Rhino 8 содержит **GrasshopperPlayer / -GrasshopperPlayer**, который запускает выбранное существующее определение *.gh/*.ghx прямо из командной строки Rhino без открытия окна Grasshopper; штатные GH Player Input/Output выводят параметры/результаты в командную строку. Это готовая точка вызова **Rhino→GH**, а не автоматический глобальный маршрутизатор и не native BIM writer. В том же Rhino 8 доступны **-Grasshopper Solver Disable/Enable**, управление открытым GH-документом и **-GrasshopperPluginList** для read-only перечня зависимостей. Для APA это новая, более конкретная точка интеграции, не требующая нового writer. **Выполнять команды в этом исследовании запрещено; SOURCE_ONLY.**

**P0-дельта 2 (готовый выбор нативного BIM-типа):** официальный Archicad 29 Grasshopper–Archicad Guide содержит **Beam/Column Sorter**: вход Curves + Degree Rule; выходы Beam Curves / Column Curves, подключаемые к соответствующим нативным Design-компонентам. Это доказанный *локальный выбор между двумя BIM-инструментами* по наклону, но не выбор между Archicad/Rhino/GH для всех операций. Для колонн нужен End Points→Anchor Point/End Point. Поскольку PR #74 authored allowlist не содержит CreateBeams, результат не разрешает обойти SceneWriter или назначить GH вторым writer для APA-owned элементов.

**P0-дельта 3 (синхронизация и идентичность):** Archicad 29 штатно поддерживает Hotlink исходника **Rhino .3dm** и сохраняет исходный Rhino Object ID/Layer в группе свойств «Rhino» импортированного объекта. Однако это **неизменяемые GDL/.gsm объекты**, а не нативные Wall/Roof/Slab. В отличие от этого GH Hotlink Input по руководству AC29 выбирает **.mod/.pln** и сопоставляет этажи. Следовательно, «Hotlink работает» не означает native BIM roundtrip или GUID-preserving triad. Дополнительно выявлены реальные ловушки: сопоставление атрибутов AC hotlink по *имени*, не по GUID, и удаление вложенных GDL parts при удалении всех экземпляров модуля.

**СТАТУСЫ ЭТОГО ПРОХОДА:** SOURCE=28 проверенных отдельных документарных/репозиторных утверждений в §2; OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0. G0=BLOCKED_RUNTIME, G1=NOT_RUN, G2=SOURCE_PARTIAL, G3=NOT_AUTHORIZED, G4/G5=NOT_RUN. Доказанной 3-way синхронизации/атомарного commit/rollback нет: **NOT_PROVEN**. Ни один источник не означает локальный PASS. MODEL_MODE_NOT_VERIFIABLE.

**Фиксированная база:** Windows 11, Archicad 29 build 5101, Tapir 1.5.10, Rhino 8 (SR неизвестен), Grasshopper; официальный Graphisoft AC29 Live Connection **build 3000 / Windows / Rhino 7–8**, дата страницы Graphisoft **01.10.2025**. Дополнение доступно бесплатно; Archicad и Rhino требуют соответствующих лицензий, GH входит в Rhino. Установка GH Connection на рабочей машине не подтверждена. AC30 build3000 не подменять AC29.

## 1. Семь новых SOURCE-карточек и адресные поручения №2

### F09-01 | Rhino 8 GrasshopperPlayer: готовая точка вызова параметрической операции

- **BUILD-01 операция:** выбрать предсуществующее определение GH для локальной геометрической операции (например, расчёт кровельного профиля/фасада) из Rhino, без создания второго writer.
- **Официальный источник и версия:** McNeel, Rhino 8 Help, раздел `GrasshopperPlayer`: https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm ; официальный feature: https://www.rhino3d.com/features/grasshopper/player/ . Версия Rhino 8, GH включён в Rhino, без отдельной подписки на Player.
- **Точный контракт/направление:** `GrasshopperPlayer` загружает/исполняет *.gh/*.ghx из Rhino; `-GrasshopperPlayer` принимает путь в командной строке, поддерживает `%USERPROFILE%` и quoted path; ищет также в каталоге .3dm и Search Paths. Player Input/Output — входы/выходы в Rhino Command Line. **Rhino→GH→Rhino** только если определение так настроено; нет автоматической передачи в Archicad.
- **Ограничения:** не документирован выбор произвольного инструмента по естественному языку; не документированы гарантии завершения внешней AC-транзакции, GUID или безопасности чужого *.gh. Если определение содержит активные AC Design/Content Cache Push, запуск может вызвать запись: в этом исследовании **не запускать**.
- **№2 I09-01:** SOURCE-only реестр уже существующих .gh/.ghx с точными путями/хешами, их входами/выходами и побочными эффектами; отдельно отметить определения без записи, без создания новых .gh. Запуск GHPlayer — только после отдельного допуска.

### F09-02 | -Grasshopper Solver и -GrasshopperPluginList: штатные границы вычисления и G0

- **Операция:** остановить повторный пересчёт при подготовке исходных данных, затем явным действием возобновить; проверить зависимости активного GH-документа.
- **Источник:** McNeel Rhino 8 Help https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm .
- **Контракт/направление:** `-Grasshopper` → `Solver Disable/Enable/Toggle` блокирует/разрешает вычисления GH; `Document Open/Save/Close` управляет файлом определения; `-GrasshopperPluginList` выводит список использованных GH-плагинов в Command History. Это локальный **контроль GH**, не триада.
- **Ограничения:** Solver Disable не отменяет уже выполненные внешние записи и не гарантирует атомарность при повторном Enable. Close теряет несохранённые изменения. PluginList отражает используемые плагины загруженного файла, не подтверждает версии/лицензии/работоспособность AC add-on. Никаких команд не выполнялось.
- **№2 I09-02:** описать read-only G0 inventory GH filename/hash, required plug-ins/versions и безопасный порядок «solver stopped → проверка owner/документов → explicit enable»; не объявлять solver lock транзакцией.

### F09-03 | Beam/Column Sorter: реальный готовый селектор нативного инструмента

- **Операция:** разделить наклонные оси каркаса BUILD-01 на балки/колонны с заданным порогом угла.
- **Официальный AC29 источник:** Graphisoft `Grasshopper–Archicad Live Connection User Guide for Archicad 29`, раздел `Archicad Utility Components / Beam/Column Sorter`: https://help.graphisoft.com/AC/29/INT/GC.pdf . Версия GH–AC29 build3000, Windows/Rhino8: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ .
- **Контракт/направление:** `Curves + Degree Rule → Beam Curves / Column Curves`; `Beam Curves→Beam Design`, `Column Curves→End Points→Column Design`. Degree Rule — порог классификации, задаётся пользователем. Это GH→native AC **только после разрешённого Design Synchronize**, не AC→Rhino и не сохранение существующего GUID при смене типа.
- **Ограничения:** смена наклона может перевести элемент из Column в Beam, то есть изменить native type/количество/GUID; для APA-owned CreateColumns/CreateBeams второй writer запрещён. PR74 authored allowlist содержит CreateColumns, CreateDoors, CreateWindows, CreateWalls, CreateRoofs, но **не CreateBeams** (pinned code 5a3a9201).
- **№2 I09-03:** SOURCE-only матрица «угол→выходной тип→owner→native tool→ожидаемое количество», stop при смене Beam↔Column для существующего GUID; GH Design разрешать лишь GH-owned элементам при отдельном допуске.

### F09-04 | GH Hotlink Component: источник .pln/.mod, этажи и высотная политика

- **Операция:** параметрически размещать повторяющийся блок здания из уже сохранённого нативного Archicad-модуля.
- **Официальный AC29 источник:** Graphisoft GC.pdf, раздел `Hotlink Module Input Component` (стр. 66) и `Hotlink Component`: https://help.graphisoft.com/AC/29/INT/GC.pdf ; AC29 build3000.
- **Контракт/направление:** GH Hotlink Module Input выбирает **.pln/.mod**, `All Stories` или `Single Story`, и соответствие Source Story→Host Story; GH Hotlink Design принимает `Hotlink Module + Insertion Point`, Hotlink Settings задаёт Master Layer/ID, Rotation, Mirror, Skip Nested Modules, Elevation `Keep Elevation as in Story Structure of Hotlink Source` или `Adjust Elevation to Story Structure of Host Project`. Направление GH→AC instance placement.
- **Ограничения:** это не автоматическое AC→GH→Rhino редактирование дочерних элементов, не сохранение дочерних GUID при source update; GH-owned placement конкурирует с существующими APA Hotlink/Tapir при одном owner. Источник .3dm для **этого** GH Input не подтверждён (не путать с нативным AC Hotlink .3dm).
- **№2 I09-04:** read-only таблица sourcePath/hash, sourceStory/hostStory/elevationPolicy, module identity/instance identity, master layer, expected child count; запрет GH Hotlink записи для APA-owned hotlinks.

### F09-05 | Archicad 29 Rhino .3dm Hotlink: оригинальный Rhino ID есть, native BIM-типа нет

- **Операция:** отображать Rhino-кровлю/фасад как обновляемый **reference** в Archicad и проверять происхождение Rhino объектов.
- **Официальный AC29 источник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-43.htm .
- **Контракт/направление:** Archicad File→External Content→Place Hotlink принимает **Rhino .3dm**, использует Rhino Import Options; импортированные Rhino элементы представлены отдельными не редактируемыми `.gsm` в Embedded Library. В группе Archicad Properties `Rhino` сохраняются исходные **Rhino Layer и original Rhino ID**. Это **Rhino file→AC reference**, обновление source требует штатного Hotlink Update, не доказан real-time commit.
- **Ограничения:** исходный Rhino Object ID в свойствах **не равен** GUID размещённого Archicad Object и тем более native Wall/Roof GUID; .gsm не превращается в Roof/Wall/Window. Нельзя считать этот маршрут полноценной BIM-синхронизацией.
- **№2 I09-05:** подготовить SOURCE-only QA crosswalk `RhinoOriginalID→Archicad Object GUID→source .3dm path/hash` как справочную идентичность, отдельно от `APA native GUID`; в BUILD-01 использовать только для визуальной/геометрической координации после допуска, не как writer.

### F09-06 | Rhino .3dm Import Options: геометрия, скрытые объекты, слои, поверхности

- **Операция:** сопоставить форму Rhino/GH сложной кровли с Archicad reference без ложных изменений материала и контуров.
- **Официальный AC29 источник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm и https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-43.htm .
- **Контракт/направление:** `.3dm→AC .gsm reference`: curved segmentation регулирует полигональность; `Bake Curved Geometry` фиксирует сегментацию и позволяет snapping; скрытые Rhino элементы по умолчанию не импортируются; Rhino Layers можно переносить с префиксом, цвета преобразуются в AC Surfaces или одну существующую Surface. У Rhino Hotlink нельзя менять Segmentation после размещения.
- **Ограничения:** Surface ≠ Building Material; сглаживание/тесселяция не гарантируют BREP-equivalence; скрытый элемент может отсутствовать в AC при сохранённом Rhino Object ID; новые слои/поверхности не равны native BIM semantics. При SOURCE-only ничего не импортировано.
- **№2 I09-06:** G2 read-only таблица import-options fingerprint: segmentation/baked/hidden/layers/surfaces + ожидаемые bbox/normals/volume, отдельный gate `native type==Roof/Wall` не удовлетворяется reference .gsm.

### F09-07 | Hotlink update, атрибуты и embedded library: границы надёжности

- **Операция:** после обновления внешнего .pln/.mod проверять связанные модули, материалы, библиотеки и последствия отката.
- **Официальный AC29 источник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-56.htm и https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-60.htm .
- **Контракт/направление:** source file modified→Hotlink Module Manager status `Modified`→`Update`→все размещённые instances; доступна связка `Update, then Compare` для Model Compare. При Archicad-based Hotlink совпадающие имена атрибутов принимают значения **host**, новые имена добавляются; атрибут, уже попавший в host, **не обновляется** при изменении исходника. Linked library parts не импортируются автоматически, Embedded library parts импортируются и обновляются с source.
- **Ограничения:** при удалении последнего Hotlink instance embedded parts могут удалиться после reopen; использование таких частей вне модуля опасно. `Relink` может очистить всю Undo queue, а несовпадение story structures грозит потерей размеров/выносок. Обновление модуля не гарантирует сохранения всех дочерних GUID; Graphisoft не описывает автоматическую двустороннюю синхронизацию Rhino/AC. Нельзя выполнять Update/Relink без разрешения.
- **№2 I09-07:** подготовить source/host attribute-name+GUID collision table, required library GUID/skippedCount, embedded-part lifecycle, story structure, pre/post Model Compare и Save/Close/Reopen; rollback только отдельной сохранённой копией, не полагаться на Undo.

## 2. Реестр 28 фактически выполненных SOURCE-проверок (утверждения, не runtime тесты)

Метод: первичные страницы McNeel/Graphisoft и GitHub connector; каждый пункт — отдельно сверенное утверждение. Повторное использование одного документа честно обозначено. Не 28 независимых сайтов и не 28 запущенных команд.

| # | Сверенное утверждение | Первичный источник |
|---:|---|---|
| 01 | Исследовательская ветка существует под точным именем | GitHub branches API `research/apa-extension-ranking-hub-20261018` |
| 02 | TRIAD-PIVOT задаёт триаду, роли и запрет второго writer | [P](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md) |
| 03 | NEXT_RESEARCH_PRIORITIES находится внутри extension-ranking, а не в корне | [N](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md) |
| 04 | Матрица имеет declared count=61 и 61 записи | [M](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json) |
| 05 | 61/61 ID уникальны, 61/61 формула priority совпадает | [M](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json) |
| 06 | PR74 открыт, исторический прототип 21 элементов, не новая BUILD-01 | [PR74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) |
| 07 | Pinned PR74 nativeComponents allowlist без CreateBeams | [C](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 08 | №2 08Z не обнаружил generic Rhino/GH→authored JSON converter | [R2](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-24T08Z-report.md) |
| 09 | №3 G0 предупреждает: IsAlive ≠ identity PLN | [A3](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md) |
| 10 | Graphisoft AC29 Live Connection build3000 Windows/Rhino7–8, 01.10.2025 | [D](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/) |
| 11 | Rhino8 `-Grasshopper` поддерживает Document Open/Save/Close | [H](https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm) |
| 12 | Rhino8 `-Grasshopper` Solver Enable/Disable/Toggle | [H](https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm) |
| 13 | `GrasshopperPlayer` исполняет *.gh/*.ghx без окна GH | [H](https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm) |
| 14 | `-GrasshopperPlayer` поддерживает пути с env vars/quotes/search paths | [H](https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm) |
| 15 | Player имеет штатные GH Input/Output для Rhino command prompt | [F](https://www.rhino3d.com/features/grasshopper/player/) |
| 16 | `-GrasshopperPluginList` выводит used plugins в Rhino command history | [H](https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm) |
| 17 | AC29 Beam/Column Sorter принимает curves и degree rule | [G](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| 18 | AC29 Sorter выдаёт Beam Curves / Column Curves; для Column нужен End Points | [G](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| 19 | AC29 GH Hotlink Input выбирает .pln/.mod и source/host stories | [G](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| 20 | AC29 GH Hotlink Design принимает Module+Insertion Point, Settings Elevation policy | [G](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| 21 | AC29 Rhino .3dm принимается как Hotlink в интерфейсе AC | [RH](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-43.htm) |
| 22 | AC29 Rhino импорт создаёт не редактируемые GDL/.gsm объекты | [RI](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm) |
| 23 | AC29 Rhino properties сохраняют original Rhino ID и Layer | [RI](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm) |
| 24 | Rhino .3dm Import Options задают segmentation, hidden, layers, surfaces | [RI](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm) |
| 25 | Rhino Hotlink segmentation нельзя менять после placement | [RH](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-43.htm) |
| 26 | AC-based Hotlink attribute name collision: host wins, existing attribute not updated | [HL](https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-56.htm) |
| 27 | Embedded Hotlink parts удаляются при удалении всех instances; linked parts не импортируются | [HL](https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-56.htm) |
| 28 | Hotlink source Modified→Update; Update then Compare; Relink clears Undo queue | [HM](https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-60.htm) |

**Отдельная проверка запрета:** AC29 `Create Openings from Selection` преобразует пересекающиеся объекты в Opening, но при отсутствии реальной коллизии Opening не создаётся; при Merge Nearby меняется количество. Это штатная UI-операция, а не готовый разрешённый writer APA; поэтому в новых карточках как автоматическая запись **не рекомендована**. Источник: https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-268.htm .

## 3. Два контрааудита (документарные, не независимая приёмка)

### CA09-A: «GrasshopperPlayer + Solver = готовая автоматическая трёхсторонняя транзакция» — ОПРОВЕРГНУТО

**Проверяемая гипотеза:** наличие scriptable `-GrasshopperPlayer` и `Solver Disable/Enable` даёт route «из любой программы → все остальные» с commit/rollback.

**Фальсификация:** официальный McNeel контракт описывает запуск локального GH определения, управление вычислителем и командной строкой Rhino, но **не** (1) выбор owner/AC tool, (2) завершение AC SceneWriter transaction, (3) проверку AC GUID/hosted Window/Roof, (4) AC→Rhino automatic save, (5) согласованный rollback трёх документов. GH Definition может содержать записывающие компоненты, и Solver Enable запускает их без отдельного межпрограммного разрешения.

**Вердикт:** `GHPLAYER_ROUTING_SOURCE_ONLY`, `TRIAD_ATOMIC_SYNC_NOT_PROVEN`. Не запускать Player на неподтверждённом .gh, не объявлять «потоковая запись готова». Для №2 — только inventory определения/побочных эффектов и owner gate.

### CA09-B: «Rhino Hotlink сохраняет ID, значит это нативная BIM-синхронизация» — ОПРОВЕРГНУТО

**Проверяемая гипотеза:** AC29 .3dm Hotlink сохраняет Rhino Original ID, значит он создаёт нативные стены/кровли и сохраняет Archicad GUID.

**Фальсификация:** AC29 Help явно определяет импорт как не редактируемые GDL/.gsm Objects; original Rhino ID — **Property** импортированного Object, не его native Archicad GUID и не BIM-тип Roof/Wall. Цвет→Surface, а не Building Material. При source update host attribute name wins; embedded parts имеют жизненный цикл модуля. GH Hotlink Input .pln/.mod и нативный AC .3dm Hotlink — разные контракты.

**Вердикт:** `RHINO_HOTLINK_REFERENCE_ONLY`, `NATIVE_BIM_ROUNDTRIP_NOT_PROVEN`, `GUID_PRESERVATION_NOT_PROVEN`. Для №2 — отдельные identity maps Rhino reference vs APA native, GDL library lifecycle, full readback.

## 4. Поручение №2, приоритет и стоп-условия

**Приоритет I09-01/02/03:** составить одну read-only матрицу маршрутизации `операция → программа → встроенный инструмент → owner → side effects → момент завершения → проверка`. Для Rhino/GH включить `GrasshopperPlayer`, `-Grasshopper Solver`, `-GrasshopperPluginList`; для Beam/Column — Degree Rule и отдельный native type/cardinality gate. Ни одного нового .gh, writer, APX, установки или вызова записи.

**Приоритет I09-04/05/06/07:** разделить (A) GH Hotlink .pln/.mod placement, (B) AC Rhino .3dm reference, (C) существующий APA/Tapir native Hotlink, не смешивать три маршрута. Сопоставить Story, Elevation, ObjectID/GUID, source SHA, Material/Surface/BuildingMaterial GUID, Embedded Library, Model Compare, Save/Close/Reopen. При unknown owner/source path, unverified GH definition, type mismatch или двойной записи — STOP.

**G0–G5:** только G0 read-only manifest может приблизить BUILD-01; G1/G2 SOURCE/preflight после отдельного допуска, G3 требует отдельного разрешения на конкретную scratch PLN/port/planHash. Исторический PR74 LIVE не приравнивать к новому BUILD-01. Никаких изменений `main`, кода, PLN/APX, установок, платных API, merge. `PROJECT_PLAN` rev182 не изменялся; исследовательская ветка — единственная цель публикации.

## 5. Доказательность и публикация

Источник: Graphisoft AC29 Help/GC.pdf, McNeel Rhino8 Help/Feature, GitHub issue #192, PR #74, TRIAD-PIVOT, NEXT, матрица 61, №2 08Z, №3 20.10 18Z. GC.pdf просмотрен через индексированные выдержки официального PDF, не через локальный установленный add-on; для AC29 Beam/Column Sorter, GH Hotlink использованы конкретные индексированные фрагменты. Файл не означает runtime receipt. Модель не создавалась и не изменялась. Отдельный GitHub commit SHA и проверка fetch/exact content — в квитанции выполнения, не вписывать вымышленный SHA в документ.
