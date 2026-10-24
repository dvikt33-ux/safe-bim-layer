# APA №1 | 2026-10-24 11:56Z | BUILD-01: штатный RhinoCode CLI, Story Plane, контроль происхождения и версий

## 0. Реальное влияние на трёхстороннюю сборку BUILD-01

**P0-дельта:** обнаружен встроенный в **Rhino 8.11+** официальный `rhinocode` CLI: `list --json` возвращает PID, pipeId, точную версию процесса, `activeDoc.title` и `activeDoc.location`, а `--rhino <pipeId> command ...` адресует действие выбранному экземпляру. Это готовая, не требующая нового MCP-моста точка **выбора правильного процесса Rhino и проверки активного .3dm** перед операцией. Однако она НЕ выбирает Archicad-инструмент, НЕ проверяет хеш .3dm, НЕ подтверждает GH/AC commit и НЕ предоставляет двустороннюю BIM-синхронизацию. Сначала надо подтвердить Rhino SR>=8.11 и включённый `StartScriptServer`; сейчас локальная версия не установлена из доказательств. Источник: [McNeel RhinoCode CLI, updated 2026-05-28](https://developer.rhino3d.com/guides/scripting/advanced-cli/).

**Вторая дельта:** официальный **Archicad 29 Story Plane Input** предоставляет в Grasshopper плоскости реальных отметок этажей Archicad; это уменьшает риск ручного дрейфа Z при генерации Wall/Slab/Beam, но НЕ заменяет `storyBindings` PR74 и не создаёт/изменяет этажи через APA. [Graphisoft AC29 User Guide, Story Plane](https://help.graphisoft.com/AC/29/INT/GC.pdf).

**Третья дельта:** Rhino 8 Document User Text имеет скрытую ловушку: **`ExportDocumentUserText=false` по умолчанию**, поэтому перенос .3dm через экспорт/буфер обмена не гарантирует перенос документационного provenance. Это препятствие для хранения crosswalk только в Rhino metadata. [McNeel Rhino 8 Document User Text](https://docs.mcneel.com/rhino/8/help/en-us/commands/setdocumentusertext.htm).

| Уровень | Фактическое состояние этого прохода |
|---|---|
| SOURCE | 29 адресных документарных/репозиторных сверок (журнал ниже); 8 карточек, 2 контрааудита |
| OFFLINE | 0 новых фактических запусков |
| BUILD | 0 новых |
| INSTALLED | Не проверено на Windows 11; AC29 Live Connection и Rhino SR не установлены из доступных доказательств |
| LIVE | 0 новых |
| ACCEPTED | 0 новых |
| BUILD-01 G0/G1/G2/G3/G4/G5 | G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_PARTIAL; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN |
| Полный круг AC↔GH↔Rhino с GUID-preserving native BIM | **NOT_PROVEN / NOT_FOUND** |

**Границы:** исходная конфигурация Archicad 29 build 5101, Tapir 1.5.10, Windows 11, Rhino 8 (точный SR неизвестен), Grasshopper. Официальный [Graphisoft AC29 GH Live Connection build 3000, Windows, Rhino 7/8, 2025-10-01](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/) доступен как SOURCE; INSTALLED не подтверждено. Встроенные средства Rhino/Grasshopper включены в лицензируемый Rhino 8, не являются отдельным бесплатным Rhino; Graphisoft add-on не требует собственного нового writer. Исторический [PR #74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) имеет ограниченный 21-элементный прототип; [BUILD-01 #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) требует нового контрольного здания всей тройки, G0–G5. Никакого нового результата здания в этом проходе.

## 1. Восемь карточек новых готовых возможностей и точные поручения №2

### F1156-01 | RhinoCode CLI: read-only идентификация нужного процесса и активного .3dm — приоритет P0
- **Операция:** до выбора программы для редактирования кровли/фасада установить, какой Rhino 8 реально запущен, какой .3dm открыт и какой PID/pipeId/версия относятся к нему.
- **Первоисточник:** [McNeel RhinoCode Command Line Interface (New in 8), 2026-05-28](https://developer.rhino3d.com/guides/scripting/advanced-cli/). **Версия:** Rhino **>=8.11**, встроенный `rhinocode`; отдельно лицензируется Rhino 8, отдельного плагина/подписки нет.
- **Точный контракт:** после `StartScriptServer` в Rhino: `rhinocode -V`, `rhinocode list --json`. Пример официальных полей: `pipeId`, `processId`, `processVersion`, `activeDoc.title`, `activeDoc.location`, `activeViewport`. Направление: **Rhino process/document → JSON CLI → наблюдатель**. Сопоставление полного пути с разрешённым .3dm — необходимое условие.
- **Ограничения:** `StartScriptServer` не запускается автоматически; запуск сервера/CLI в пользовательской среде не производился. Нет .3dm SHA, несохранённого состояния, GUID Archicad, PLN/port, GH .gh, гарантий завершения solve или блокировки записи. При Rhino<8.11 — NOT_AVAILABLE.
- **№2 I1156-01:** SOURCE-only описать проверку `rhinocode -V` и `list --json` без запуска, матрицу полей PID/pipeId/path/version, проверку ровно одного разрешённого активного .3dm и fail-closed при пустом/неверном пути. Не добавлять новый сервис.

### F1156-02 | RhinoCode CLI: адресный вызов штатной команды в конкретном Rhino
- **Операция:** после разрешённого выбора инструмента направить Rhino-команду в конкретный экземпляр, а не в «первый доступный» процесс.
- **Источник/версия/лицензия:** тот же [официальный RhinoCode CLI](https://developer.rhino3d.com/guides/scripting/advanced-cli/), Rhino >=8.11, часть лицензии Rhino.
- **Контракт:** `rhinocode --rhino <pipeId> command "<Rhino command>"` и `rhinocode --rhino <pipeId> script <path>` адресуют **CLI → Rhino instance**. `list --json` предшествует вызову; `--rhino` выбирает конкретный process ID.
- **Ограничения:** `command` и `script` потенциально **пишущие**; без явного допуска не выполнять. Нет гарантии «операция завершена в GH/Archicad», rollback, AC GUID и BIM semantics. `script` не основание создавать новый writer. Ни один вызов в этом исследовании не исполнен.
- **№2 I1156-02:** сопоставить с ранее найденными Wasp MCP v0.5.2 / EaseHee rhino-mcp v0.6.0: где достаточно штатного CLI, где нужен только read-only статус, и какие команды строго запрещены до G3. Отдельно доказать, что CLI не создаёт второй Archicad writer.

### F1156-03 | Graphisoft Story Plane Input: реальные этажные Z вместо вручную повторённых отметок
- **Операция:** геометрия Wall/Slab/Beam BUILD-01 должна строиться на плоскостях, полученных из Archicad Story heights.
- **Первоисточник:** [Graphisoft AC29 Grasshopper–Archicad User Guide, Story Plane Input, стр. 64](https://help.graphisoft.com/AC/29/INT/GC.pdf). Версия AC29; точный дистрибутив [Live Connection build 3000](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/). Лицензия: готовый Graphisoft add-on, Archicad/Rhino лицензируются отдельно.
- **Контракт:** **AC story elevations → GH Story Plane Input → horizontal XY planes → reference input curves → GH Design elements**. Официальный текст прямо называет Wall, Slab, Beam. Это направленный источник этажных отметок, а НЕ двустороннее редактирование Stories.
- **Ограничения:** не подтверждена запись этих planes в PR74 `storyBindings`; не создаёт нативные этажи, не гарантирует правильный floorId/index при GH→AC. Прямой GH Design writer конкурирует с SceneWriter; в BUILD-01 его не включать.
- **№2 I1156-03:** подготовить таблицу `AC floorId/index/elevation ↔ GH Story Plane Z ↔ PR74 storyBindings` с критериями mm/m, координат и допуска; источник AC→GH только read-only, без вызова GH native writer.

### F1156-04 | Deconstruct Wall: адресные поверхности проёмов и контактов для независимого GH QA
- **Операция:** после изменения окна или контакта кровли проверить именно поверхности стеновых проёмов/примыканий, а не только bbox.
- **Первоисточник:** [Graphisoft AC29 User Guide, Deconstruct Brep, стр. 40–41](https://help.graphisoft.com/AC/29/INT/GC.pdf). Версия AC29, Live Connection build 3000; условия лицензирования как выше.
- **Контракт:** **Archicad native Wall → GH Deconstruct Wall → Brep/Settings**, контекстное `Select Wall Surface Type` добавляет типизированные outputs, в том числе `Reference Side Surfaces` и `Wall Opening Side Surfaces`; для Beam/Column/Slab/Wall/Mesh/Zone/Shell/Single-Plane Roof доступен Brep из поверхностей. Направление **AC→GH readback**, без записи.
- **Ограничения:** Brep GH не заменяет нативный GUID/BREP/SEO readback APA; surface-type classification зависит от геометрии и не доказывает hostWall identity. Multi-Plane Roof Deconstruct официально не поддерживается. Нет автоматического сравнения с сохранённым PLN.
- **№2 I1156-04:** SOURCE-only задать выборку «одна стена с окном → opening side surfaces → изменение окна → GH surface count/area + native Wall/Window GUID/BREP»; отдельно контроль Single-Plane Roof/SEO и отказ на Multi-Plane.

### F1156-05 | Rhino 8 Document User Text: хранение provenance и доказанный риск потери при экспорте
- **Операция:** хранить в .3dm человекочитаемую связь с BUILD-01, hash исходного плана, единицы, owner, не выдавая текст за гарантированный crosswalk.
- **Первоисточник:** [McNeel Rhino 8 SetDocumentUserText/GetDocumentUserText](https://docs.mcneel.com/rhino/8/help/en-us/commands/setdocumentusertext.htm), Rhino 8, штатная функция лицензируемого продукта.
- **Контракт:** `SetDocumentUserText` сохраняет key/value **в документ .3dm**, `GetDocumentUserText` читает; ключ с точкой скрыт от обычной панели, но не является защищённым секретом. Документ допускает import/export key-value из .3dm/.csv/.txt.
- **Критическое ограничение:** `ExportDocumentUserText` в Advanced settings **false by default**; перенос через экспорт/clipboard не гарантирует переноса Document User Text. Метаданные не создают AC GUID, не являются защищённой подписью, не обеспечивают rollback. Никакой записи в пользовательский .3dm не выполнялось.
- **№2 I1156-05:** составить READ-only таблицу полей provenance и тест будущей копии .3dm «native save vs export/clipboard» с явной проверкой потери key/value; не применять к живому файлу без разрешения.

### F1156-06 | Rhino 8 Attribute User Text: штатный выбор объектов по ключу+значению
- **Операция:** выделить только Rhino-объекты определённого APA owner / story / semantic type перед подготовкой GH-геометрии.
- **Первоисточник:** [McNeel Rhino 8 Attribute User Text](https://docs.mcneel.com/rhino/8/help/en-us/properties/attributeusertext.htm), [Rhino 8 command reference SelKeyValue/SelID](https://docs.mcneel.com/rhino/8/help/en-us/commandlist/command_list.htm). Встроено в лицензируемый Rhino 8.
- **Контракт:** `Select objects by key and value` выбирает только объекты с **совпадающими key и value**, а не лишь одним из них; `SelKeyValue` и `SelID` — штатные команды. Направление **Rhino attributes → Rhino selection → потенциально GH reference**.
- **Ограничения:** User Text редактируем, может быть утерян при пересоздании объекта; совпадение ключа не доказывает соответствие AC GUID/IFC GlobalId. `SelID` относится к Rhino Object ID, не к Archicad GUID. Выбор не является блокировкой записи.
- **№2 I1156-06:** описать без установки селекцию по `apa_owner`+`story`+`type` с проверкой отсутствующих/дублированных ключей; не заменять этим native GUID crosswalk.

### F1156-07 | Rhino 8 G0: SystemInfo + GetIssueState + PackageManager — фиксация реальной версии
- **Операция:** перед решением использовать Rhino Content Cache / RhinoCode исключить незамеченный version drift.
- **Первоисточники:** [McNeel Rhino 8 SystemInfo](https://docs.mcneel.com/rhino/8/help/en-us/commands/systeminfo.htm), [Rhino 8 GetIssueState в списке команд](https://docs.mcneel.com/rhino/8/help/en-us/commandlist/command_list.htm), [подробный контракт GetIssueState](https://docs.mcneel.com/rhino/8mac/help/en-us/commands/getissuestate.htm), [Rhino 8 PackageManager](https://docs.mcneel.com/rhino/8mac/help/en-us/commands/packagemanager.htm), [Rhino 8 updates](https://docs.mcneel.com/rhino/8/help/en-us/options/updates_and_statistics.htm). Встроено в Rhino 8.
- **Контракт:** `SystemInfo` показывает OS/железо/плагины; `GetIssueState <YouTrack-ID>` возвращает true, если фикс содержится в запущенной сборке, false если нет; `PackageManager → Installed` показывает установленные пакеты. Rhino 8 **может автоматически обновлять пакеты**; Rhino SR updates могут загружаться автоматически с уведомлением об установке.
- **Ограничения:** нет readback локального Rhino в этом исследовании. True фикс не доказывает отсутствие регрессий. Для GH Content Cache прежние RH-89804/RH-89952 — **предыдущие** находки №1, здесь новым является штатный способ проверки фактического runtime. Никакого запуска команд не было.
- **№2 I1156-07:** SOURCE-only G0 checklist `SystemInfo + rhinocode -V + PackageManager Installed + GetIssueState RH-89804/RH-89952` (последние только если номера поддерживаются локальной командой), записать точные версии, даты, GH components; исключить auto-updated version drift при сравнении receipts. Не менять настройки/пакеты без допуска.

### F1156-08 | Graphisoft Reshape Polygon — исторический готовый кандидат, но НЕ подтверждён для AC29
- **Операция-кандидат:** параметрическое отверстие/добавление контура Slab или Single-Plane Roof без произвольного Rhino Brep.
- **Первичный источник с точной границей:** [Graphisoft AC25 GH User Guide, Reshape: Subtract Polygon / Add Polygon](https://help.graphisoft.com/AC/25/INT/GC.pdf), исторический функционал (руководство 2.3); для AC29 build3000 наличие именно этих компонентов в текущем установленном бинарнике **NOT_VERIFIED**. Встроенная функция исторического add-on, лицензия зависит от Archicad/Rhino.
- **Контракт исторической версии:** **GH Fill/Slab/Single-Plane Roof + projected XY closed Curve → Reshape output того же типа**. На наклонной кровле контур отверстия задаётся вертикальной призмой. При контуре вне элемента документ предупреждает о результате как **дополнительной копии без отверстия**.
- **Ограничения:** формулировка «existing element» не гарантирует сохранение GUID при GH recompute; в BUILD-01 это потенциальный второй native writer и риск дубликатов. Нельзя заявлять поддержку AC29/PR74/сложной Multi-Plane Roof без бинарной проверки. **NOT_QUALIFIED_FOR_BUILD-01**.
- **№2 I1156-08:** только сравнить список фактически доступных GH компонентов после отдельного G0-допуска с историческим Reshape; если отсутствует/identity не доказана — закрыть NOT_FOUND, не создавать новый writer.

## 2. Направления обмена и жёсткие границы владения

| Поток | Доказанный контракт SOURCE | Native BIM write | Для BUILD-01 |
|---|---|---|---|
| Rhino process → `rhinocode list --json` | PID/pipeId/activeDoc/version | НЕТ | G0 read-only identification после разрешённого локального подключения |
| `rhinocode --rhino ... command` → Rhino | Адресная Rhino команда | МОЖЕТ писать Rhino | Только отдельное разрешение; никакого нового writer |
| Archicad Stories → GH Story Plane | AC Z → GH plane | НЕТ на входе | Read-only reference; сверка с PR74 bindings |
| Archicad Wall/Window geometry → GH Deconstruct | AC surfaces/settings → GH | НЕТ | Вторичный QA, не native acceptance |
| Rhino UserText → selection/GH | Rhino metadata → Rhino/GH | НЕТ при чтении | Provenance hint, не authority |
| GH Design → AC | GH-native creation/update | ДА | **ЗАПРЕЩЕНО для APA-owned элементов**: конкурирует с SceneWriter |
| APA authored intent → SceneWriter/SQLite/Tapir → AC | typed native writer | ДА | **Единственный разрешённый контур native write**, только после G3 допуска |
| AC→GH→Rhino→AC полный цикл | Нет подтверждённого общего commit/identity resolver | НЕ ДОКАЗАНО | **NOT_PROVEN** |

**Особое ограничение:** `rhinocode` даёт процессный селектор Rhino, но не автоматический маршрутизатор «операция → программа → инструмент» и не общий AC/GH/Rhino rollback. Успешная адресация не является завершением GH solve или native AC write. Проверять `activeDoc.location` перед каждым потенциальным действием, а не один раз за сессию.

## 3. Журнал 29 реальных SOURCE-сверок

Под «проверкой» понимается отдельная проверка конкретного утверждения по указанному источнику/репозиторию, **не 29 независимых LIVE/тестов**. Все проверки сделаны без доступа к пользовательскому Windows.

| # | Предмет | Наблюдение / доказательство |
|---:|---|---|
| 01 | Branch GitHub | `search_branches` вернул точную `research/apa-extension-ranking-hub-20261018` |
| 02 | BUILD-01 issue #192 | Открыта; G0–G5, новый scratch, single writer [issue](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) |
| 03 | PR #74 | Open, ограниченный 21 native element, SceneWriter/SQLite, не универсальная тройка [PR](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) |
| 04 | TRIAD-PIVOT 23.10 11Z | P0 сменён на трёхстороннюю модель, не создание нового writer [pivot](research-1-20261023T11Z-TRIAD-PIVOT.md) |
| 05 | NEXT_RESEARCH_PRIORITIES | BUILD-01 приоритетнее SOURCE-каталога [priorities](../NEXT_RESEARCH_PRIORITIES.md) |
| 06 | Matrix count | `priority_matrix_20261018.json`: count=61, фактических items=61 |
| 07 | Matrix uniqueness | 61 уникальных id из 61 |
| 08 | Matrix formula | 61/61 совпадений `12*need+7*(5-effort)+confidence` |
| 09 | PROJECT_PLAN | `control/PROJECT_PLAN.json` revision=182; только чтение |
| 10 | Latest #2 | [11Z GH lifecycle report](research-2-integration-2026-10-24T11Z-report.md): GH false=PAUSE≠DELETE, AC→GH auto, no native roundtrip |
| 11 | Latest available #3 | [20.10 07Z](audit-2026-10-20-07.md), более свежий независимый №3 в прочитанном дереве не доказан |
| 12 | Latest #1 previous | [10:56Z Speckle/reference QA](research-1-20261024T1056Z-TRIAD-SPECKLE-RHINO-REFERENCE-QA.md), не дублировать |
| 13 | Graphisoft AC29 package | build3000, Windows, Rhino7/8, 01.10.2025 [official](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/) |
| 14 | RhinoCode minimum | Rhino>=8.11, built-in CLI [official](https://developer.rhino3d.com/guides/scripting/advanced-cli/) |
| 15 | RhinoCode server | `StartScriptServer` нужен, по умолчанию не стартует |
| 16 | RhinoCode version | `rhinocode -V` выдаёт версию утилиты, связанную с Rhino |
| 17 | RhinoCode instance | `rhinocode list --json` имеет PID/pipeId/processVersion/activeDoc path |
| 18 | RhinoCode targeting | `--rhino <pipeId> command` адресует конкретный Rhino |
| 19 | RhinoCode script | `--rhino <pipeId> script` существует, но потенциально пишет |
| 20 | AC29 Story Plane | Плоскости из реальных story heights для Wall/Slab/Beam [Graphisoft](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| 21 | AC29 Deconstruct | Native Beam/Column/Slab/Wall/Mesh/Zone/Shell/Single-Plane Roof → GH Brep |
| 22 | AC29 surface types | Wall opening side / reference side surfaces доступны как выбор outputs |
| 23 | AC29 Multi-Plane | Deconstruct Roof только Single-Plane, Multi-Plane не поддержан |
| 24 | Rhino Doc User Text | key/value в .3dm, `GetDocumentUserText` [McNeel](https://docs.mcneel.com/rhino/8/help/en-us/commands/setdocumentusertext.htm) |
| 25 | Rhino export metadata | `ExportDocumentUserText=false` по умолчанию |
| 26 | Rhino object selection | Attribute User Text key AND value; `SelKeyValue` [McNeel](https://docs.mcneel.com/rhino/8/help/en-us/properties/attributeusertext.htm) |
| 27 | Rhino version/plug-ins | `SystemInfo` + `PackageManager Installed` [McNeel](https://docs.mcneel.com/rhino/8/help/en-us/commands/systeminfo.htm) |
| 28 | Rhino fix/auto-update | `GetIssueState` и PackageManager auto-update documented [McNeel](https://docs.mcneel.com/rhino/8mac/help/en-us/commands/getissuestate.htm) |
| 29 | Historical Reshape + target path | AC25 Subtract/Add Polygon не доказывает AC29; до публикации `fetch_file` целевого нового пути вернул 404 [AC25](https://help.graphisoft.com/AC/25/INT/GC.pdf) |

## 4. Контрааудит A — не выдавать процессный CLI за двустороннюю BIM-синхронизацию

**Проверка утверждения:** «`rhinocode list --json` + GH Live Connection обеспечивают автоматическое изменение в любой из трёх программ с сохранением GUID». **ОТКЛОНЕНО.** CLI определяет процесс и файл, но не строит native typed intent и не даёт Archicad GUID. GH→AC Design является другим writer и может нарушить строгий APA inventory. Story Plane и Deconstruct — только направленные AC→GH данные. Доказательств общего conflict-free commit, anti-loop и rollback для PLN+3DM+GH нет. **G3 не разрешён.**

## 5. Контрааудит B — не подменять сохранение идентичности сохранением текста и не предполагать версию

**Проверка утверждения:** «Rhino Object UserText + Doc UserText сохраняют BIM identity и все свойства при экспорте, а Rhino 8 имеет нужный CLI/фиксы». **ОТКЛОНЕНО.** UserText — изменяемые строки, экспорт документационных данных по умолчанию может их исключить; Rhino Object ID ≠ AC GUID ≠ IFC GlobalId. RhinoCode требует >=8.11, точный SR неизвестен; автоматические обновления плагинов могут изменить среду. Исторический Reshape не подтверждён для AC29; even when present, не доказано сохранение GUID. **INSTALLED/LIVE/ACCEPTED не повышены.**

## 6. Практический handoff №2 и критерии принятия

**I1156-P0 (без нового кода и без LIVE):** подготовить одну воспроизводимую G0→G2 схему «разрешённый PLN/port/SceneWriter → AC story index/floorId/Z → GH Story Plane/Deconstruct → Rhino `rhinocode list --json` → точный .3dm/processVersion → tool decision». На каждый шаг: фактическое поле, read-only/write, владелец, отказ при несовпадении, доступность в конкретном Rhino SR/AC29 build. Не создавать новый writer, роутер, .gh, PLN или .3dm.

**I1156-QA:** для будущей авторизованной проверки Wall+Window и Single-Plane Roof подготовить сравнение native GUID/host/story/material/BREP/SEO против GH opening-side surfaces; передача только read-only до G3. Для Multi-Plane Roof и произвольных holes оставлять NOT_FOUND, не подменять Morph/GDL.

**I1156-VERSION:** список `SystemInfo`, `GetIssueState`, `PackageManager Installed`, `rhinocode -V`, `list --json`; фиксировать версии и активные пути до/после операции. Не устанавливать и не переключать ничего в этом исследовании.

## 7. Публикационный контроль и ограничения

Ветка до записи проверена `search_branches`, целевой новый файл до записи отсутствовал (`fetch_file` 404). Публиковать только через `create_file` с явным `branch`; затем `fetch_file` по ветке и по конкретному commit, точное сравнение строк и Git blob SHA. При ошибке — `WRITE_BLOCKED`; `DONE_PUBLISHED` только после PASS.

Не выполнялись установки, RhinoCode CLI, `StartScriptServer`, GH solve, Archicad native calls, offline компиляция, LIVE, PLN/APX edits, изменение main, merge, Work/Codex/Arena или платные API. PROJECT_PLAN rev182 только чтение. **MODEL_MODE_NOT_VERIFIABLE**.
