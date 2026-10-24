# APA №1 | 2026-10-24 09:55Z | BUILD-01: готовые GH MCP, wait-idle, фильтры и границы синхронизации

## 0. Реальное влияние на трёхстороннюю сборку BUILD-01 (#192)

**Дельта P0-A:** найден бесплатный выпущенный мост **wasp-mcp v0.5.2** для Rhino 8 / Grasshopper, который умеет программно дождаться состояния **GH solver idle** (gh_wait_idle), опрашивать типы/схемы установленных компонентов (gh_list_component_types / gh_component_schema), пакетно подготовить изменения с solve=false и одним expire_solution. Это готовые средства для этапов **выбора инструмента GH и определения завершения вычисления**, без нового writer. Но **GH_IDLE ≠ завершение внешней записи Archicad, сохранение GUID или транзакция трёх программ**. Сам мост умеет gh_bake в Rhino, поэтому подключение без ограничения прав записи создаёт конкурирующий writer.

**Дельта P0-B:** найден второй выпущенный MIT-мост **EaseHee/rhino-mcp v0.6.0**, в котором принудительный режим RHINO_MCP_FORCE_MODE=bridge **отказывает при недоступном живом Rhino**, вместо неявного перехода на standalone rhino3dm. Это полезный готовый fail-closed переключатель **правильного режима программы**, но не гарантирует правильный открытый .3dm и тем более PLN. У моста имеются GH run/get/bake и отдельный Rhino .rhp; запретить bake и любые мутации без допуска.

**Дельта P0-C:** в штатном Rhino 8 GH доступны **Intersection Filter** для составных условий по Model Object User Text и числовым атрибутам; Stream Filter/Stream Gate направляют потоки по целочисленному индексу. Это локальный выбор ветви данных, не межпрограммный маршрутизатор и не lock на вычисление/запись.

**Риск P0-D:** штатный Data Dam не является безопасной транзакционной защёлкой: на форуме McNeel задокументирован стартовый проход данных при открытии .gh даже в Never, а Stream Gate/Filter могут приводить к downstream recompute/null. Нельзя считать любой такой компонент гарантией «ничего не записывается до подтверждения».

**Статусы именно этого прохода:** SOURCE=30 документарных/репозиторных сверок ниже; OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0. G0=BLOCKED_RUNTIME, G1=NOT_RUN, G2=SOURCE_PARTIAL, G3=NOT_AUTHORIZED, G4/G5=NOT_RUN. Полная автоматическая двусторонняя трёхсторонняя синхронизация: **NOT_PROVEN**. Не было подключения к Windows, изменения исходников, PLN/APX, main, установки, LIVE или платного API. MODEL_MODE_NOT_VERIFIABLE.

Фиксированная конфигурация: Windows 11, Archicad 29 build 5101, Tapir 1.5.10, Rhino 8 (точный SR неизвестен), Grasshopper; официальный GH–AC29 Live Connection build 3000 для Rhino 7/8 — SOURCE, локальная установка не подтверждена. Исторический PR74 21-element building, не новый BUILD-01. Исходный PROJECT_PLAN rev182 только прочитан.

## 1. Семь карточек новых решений и поручения №2

### F0955-01 | Wasp MCP v0.5.2: ожидание окончания GH-решения
- **Операция BUILD-01:** после выбора GH-операции, например пересчёта профиля кровли/фасада, получить сигнал завершения вычисления до чтения GH output; не считать этот сигнал разрешением записи в Archicad.
- **Версионированный первоисточник:** авторский [wasp-mcp release v0.5.2 от 11.07.2026](https://github.com/liangjunglj-cpu/wasp-mcp/releases/tag/v0.5.2), [PROTOCOL.md@v0.5.2](https://github.com/liangjunglj-cpu/wasp-mcp/blob/v0.5.2/PROTOCOL.md), [README@v0.5.2](https://github.com/liangjunglj-cpu/wasp-mcp/blob/v0.5.2/README.md).
- **Версия/лицензия:** bridge v0.5.2, GH_MCP_Wasp.gha и wasp-mcp-bridge-0.5.2-rh8_0-win.yak; MIT для кода сервера/bridge; данные server/knowledge лицензируются отдельно. Rhino 8 Windows, Grasshopper, локальный Python MCP server.
- **Точный контракт:** gh_wait_idle / протокол wait_for_idle с timeoutMs (default 30000, max 120000) проверяет GH doc.SolutionState/SolutionDepth; требует два последовательных idle-считывания через 100 мс; возвращает idle:true, waitedMs либо wait_timeout. Направление MCP client→GH status; НЕ GH→Archicad.
- **Ограничение:** GH idle не означает, что внешний Archicad завершил запись/сохранение, и не гарантирует отсутствие side effects до idle. Внешние BIM GUID, story, hosted openings, material не сверяет.
- **№2 I0955-01:** SOURCE-only описать применение gh_wait_idle как **необходимого, но недостаточного** шага после GH solve. За ним — независимый read-only Archicad readback, а не автоматическое разрешение G3. Ничего не устанавливать.

### F0955-02 | Wasp MCP v0.5.2: discovery по component GUID и пакетное вычисление
- **Операция:** выбрать доступный инструмент GH по фактической схеме установленного компонента, подготовить несколько соединений без промежуточного solve.
- **Источник/версия/лицензия:** тот же [PROTOCOL.md@v0.5.2](https://github.com/liangjunglj-cpu/wasp-mcp/blob/v0.5.2/PROTOCOL.md), MIT на код.
- **Контракт:** gh_list_component_types возвращает name/nickname/category/subCategory/guid/description; gh_component_schema создаёт proxy IN MEMORY, читает входы/выходы и не помещает компонент на canvas; connect_components/set_slider/... принимают solve:false, затем один expire_solution. В протоколе зафиксирована неоднозначность поиска по имени и предпочтение component GUID.
- **Направление:** MCP→GH canvas/introspection; GH output→MCP. Никакого выбора native AC инструмента по GUID.
- **Ограничение:** GUID компонента Grasshopper не равен Rhino Object ID и не равен Archicad GUID. В README main описан gh_verify v0.6, но **в закреплённом release v0.5.2 он отсутствует**; не заявлять этот инструмент доступным в v0.5.2. gh_bake — явная запись в Rhino.
- **№2 I0955-02:** матрица «требуемый GH tool→GUID component→input/output schema→side effects→owner» только из реально установленной конфигурации после отдельного допуска. Никаких новых gh-файлов или компонентов пока не создавать.

### F0955-03 | EaseHee/rhino-mcp v0.6.0: fail-closed режим live Rhino
- **Операция:** исключить молчаливую подмену активной Rhino 8 модели headless-операциями в другом .3dm при недоступном GUI.
- **Источник:** [release v0.6.0 от 20.05.2026](https://github.com/EaseHee/rhino-mcp/releases/tag/v0.6.0), [README@v0.6.0](https://github.com/EaseHee/rhino-mcp/blob/v0.6.0/README.md), [GH guide@v0.6.0](https://github.com/EaseHee/rhino-mcp/blob/v0.6.0/docs/en/grasshopper-guide.md), [MIT LICENSE](https://github.com/EaseHee/rhino-mcp/blob/v0.6.0/LICENSE).
- **Версия/лицензия:** v0.6.0 MIT; готовый rhino-mcp.rhp, wheel rhino3dm_mcp-0.6.0; Python >=3.11, rhino3dm>=8.9; Rhino 8 нужен для bridge mode. Нет подписки на сам MCP, Rhino требует лицензии.
- **Контракт/направление:** RHINO_MCP_FORCE_MODE=bridge заставляет server подключаться к живому Rhino, fail-fast при отсутствии; auto режим может перейти в standalone; RHINO_MCP_BRIDGE_OPTIONAL=1 вновь разрешает fallback. GH инструменты работают только в bridge с загруженным .rhp и GH canvas: gh_run, gh_get_parameter, gh_bake_to_rhino. MCP↔Rhino/GH, **нет AC native API**.
- **Ограничения:** не проверяет active .3dm path/hash и PLN/port; при --allow-external отключается DNS-rebinding protection, не применять. Документированный bake создаёт Rhino-объекты, не native AC Wall/Roof. MCP умеет скриптовые/модифицирующие действия: при SOURCE-only не запускать.
- **№2 I0955-03:** сравнить этот мост с уже найденными 3d-mcp и официальным Rhino MCP по read-only doc identity, принудительному bridge и наличию side effects. Никакой установки; если когда-нибудь одобрят — требовать forced bridge, localhost, точный .3dm hash и отключённый fallback.

### F0955-04 | Rhino 8 Intersection Filter: составная селекция BIM-подобных атрибутов
- **Операция:** выбрать в Rhino только объекты нужного типа/этажа/диапазона площади до подготовки геометрии BUILD-01.
- **Официальный версионированный источник:** [McNeel Rhino 8, Grouping and Filtering Data](https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/).
- **Версия/лицензия:** Grasshopper 1 в Rhino 8, штатно включён в лицензионный Rhino 8; отдельного плагина/подписки нет.
- **Контракт:** Query Model Objects (Layer), Match Text Filter (Model Object→User Text, Equals), Greater Than Filter и Smaller Than Filter по User Text Area, Intersection Filter объединяет все условия через AND, Filter Content возвращает совпавшие Model Objects. В официальном примере из 31 floor surface остаются 5 после трёх условий.
- **Направление:** Rhino attributes→GH выборка; НЕ Archicad native selection/update. User Text Area может быть строковым/неавторитетным: проверять тип и единицы, не принимать как нормативный расчёт.
- **№2 I0955-04:** составить SOURCE-only готовые фильтры для этажной отметки, APA owner, класса элемента и геометрических порогов; при неизвестном атрибуте STOP, не преобразовывать геометрию в native BIM без typed intent.

### F0955-05 | Grasshopper Stream Filter / Stream Gate: выбор ветви, не межпрограммный lock
- **Операция:** выбрать один из подготовленных GH потоков по индексу: вариант простой Roof / вариант Beam / Column; не разрешать второму writer.
- **Первоисточник/оговорка:** [McNeel Rhino 8 filtering guide](https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/) подтверждает штатную фильтрацию; [Grasshopper Docs Stream Filter](https://grasshopperdocs.com/components/grasshoppersets/streamFilter.html) и [Stream Gate](https://grasshopperdocs.com/components/grasshoppersets/streamGate.html) дают точный I/O, но это **не официальный versioned Rhino 8 manual**. Версию конкретного GH binary надо сверить в G0.
- **Контракт:** Stream Filter: G=Integer, входы 0/1=Generic Data→S; Stream Gate: S=Generic Data, G=Integer→Target0/Target1. Это выбор ветви данных **внутри GH**, не выбор активной программы, не атомарное прекращение пересчёта.
- **Лицензия:** встроенные GH components в лицензируемом Rhino 8; отдельной лицензии нет.
- **Ограничение:** Stream Filter/Gate не гарантируют, что невыбранные upstream ветви не вычисляются или что downstream не получит null/expiration; данные без identity/owner не являются безопасным dispatch.
- **№2 I0955-05:** таблица селекции по явному integer index и GH component GUID, а также запрет считать Stream Gate подтверждением отсутствия write side effects. Не собирать новый router.

### F0955-06 | Melanoplus Idempotent: НЕ КВАЛИФИЦИРОВАНО к установке
- **Операция-кандидат:** передавать обновление downstream по событию, а не каждый раз после изменения параметра.
- **Авторский источник:** [lin-ycv/Melanoplus](https://github.com/lin-ycv/Melanoplus), [release 1.0.6.1 от 29.03.2024](https://github.com/lin-ycv/Melanoplus/releases/tag/1.0.6.1), [McNeel forum, автор рекомендует Idempotent](https://discourse.mcneel.com/t/toggle-data-dam/190183/2).
- **Версия/лицензия:** 1.0.6.1; README в корне не найден; GitHub repository license не указан, отдельный LICENSE не подтверждён; следовательно **не объявлять open-source/MIT и не рекомендовать установку**. Автор различает .NET Framework x.0.x и .NET7 x.1.x; конкретную сборку v1.0.6.1 надо проверить отдельно.
- **Направление:** локальный GH event gating; не AC native roundtrip.
- **№2 I0955-06:** только уточнить авторский I/O Idempotent, лицензирование и доступность стабильной Rhino 8 сборки. До этого NOT_QUALIFIED, не ставить.

### F0955-07 | aphollis/rhino-gh-mcp: идемпотентные GH-рецепты, но нет релиза
- **Операция-кандидат:** повторно применять одну GH-рецептуру без размножения компонентов по ключам.
- **Авторский источник:** [aphollis/rhino-gh-mcp README](https://github.com/aphollis/rhino-gh-mcp), [MIT](https://github.com/aphollis/rhino-gh-mcp/blob/main/LICENSE).
- **Версия/лицензия:** MIT; автор указывает тестирование Rhino 8.32, Node.js 18+ и Python listener; на 24.10.2026 latest GitHub release отсутствует (404). Нет закреплённого бинарного дистрибутива/релизного контракта.
- **Контракт/направление:** gh_build_recipe с одинаковыми keys обновляет компоненты GH canvas in place, gh_get_output читает вычисления, gh_bake записывает Rhino. Это **GH component identity**, не Archicad GUID; никакого AC native writer.
- **№2 I0955-07:** SOURCE-only сравнить GH recipe idempotency с Wasp v0.5.2, без установки/сборки и без трактовки как BIM идемпотентности. Статус RESEARCH_ONLY_NOT_RELEASED.

## 2. Журнал 30 выполненных проверок SOURCE (каждая — проверенное отдельное утверждение, не LIVE)

| № | Проверка | Результат |
|---:|---|---|
| 01 | GitHub branch search: research/apa-extension-ranking-hub-20261018 | точное имя ветки найдено |
| 02 | GitHub fetch_file нового имени отчёта до публикации | NOT_FOUND: путь свободен |
| 03 | TRIAD-PIVOT 20261023T11Z | P0=трёхсторонняя модель, без нового writer |
| 04 | Issue #192 | G0–G5, scratch+Save/Reopen; старый прототип не BUILD-01 |
| 05 | PR #74 | draft/open, исторический 21-element prototype, SceneWriter |
| 06 | NEXT_RESEARCH_PRIORITIES.md в extension-ranking | BUILD-01 выше SOURCE-каталога |
| 07 | priority_matrix_20261018.json | schema count=61, не переписана |
| 08 | №2 20261024T09Z report | Beam есть через existing connected CLI, но не authored one-shot |
| 09 | №2 20261024T09Z audits | GHPlayer/solver не транзакция; Beam-route условен |
| 10 | №3: дерево исследовательской ветки | файлов audit/research-3 за 24.10 не обнаружено; прочитан 20.10 18Z-A |
| 11 | PROJECT_PLAN.json в этой ветке | revision=182, read-only |
| 12 | wasp-mcp public repo | существующий Rhino8 GH MCP |
| 13 | wasp-mcp v0.5.2 release | опубликован 11.07.2026, .gha + .yak |
| 14 | wasp-mcp LICENSE | MIT для исходников сервера и bridge |
| 15 | wasp-mcp LICENSE caveat | server/knowledge отдельно лицензирован |
| 16 | wasp-mcp README@v0.5.2 | GH component WaspMCP, localhost:8090 |
| 17 | wasp-mcp README@v0.5.2 | token optional; по умолчанию локальный endpoint без token |
| 18 | wasp-mcp PROTOCOL@v0.5.2 | wait_for_idle/gh_wait_idle, two idle reads, timeout |
| 19 | wasp-mcp PROTOCOL@v0.5.2 | gh_component_schema / list types, GUID-based resolution |
| 20 | wasp-mcp PROTOCOL@v0.5.2 | solve:false + expire_solution; gh_bake = Rhino write |
| 21 | wasp-mcp README main vs tag v0.5.2 | gh_verify v0.6 есть в main, отсутствует в v0.5.2 |
| 22 | EaseHee/rhino-mcp public repo + LICENSE | MIT, Rhino8/GH bridge |
| 23 | EaseHee v0.6.0 release | 20.05.2026, готовый .rhp + Python wheel |
| 24 | EaseHee GH guide@v0.6.0 | GH tools только bridge, rhino-mcp.rhp |
| 25 | EaseHee README@v0.6.0 | FORCE_MODE=bridge fail fast; auto может fallback |
| 26 | EaseHee README@v0.6.0 | --allow-external ослабляет DNS-rebinding protection |
| 27 | Официальный Rhino8 Grouping and Filtering | Intersection Filter объединяет AND text+numeric |
| 28 | GrasshopperDocs Stream Filter / Gate | подтверждены G/0/1/S и S/G/Target0/1; источник не официальный |
| 29 | McNeel forum Toggle Data Dam | documented startup leakage; не считать safe gate |
| 30 | Melanoplus release/license и aphollis repo/release | Idempotent без проверенной лицензии; aphollis MIT без release |

Источники сверок: [pivot](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md), [priorities](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md), [matrix 61](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json), [№2 report](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-24T09Z-report.md), [№3 older audit](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md), [Wasp v0.5.2](https://github.com/liangjunglj-cpu/wasp-mcp/releases/tag/v0.5.2), [EaseHee v0.6.0](https://github.com/EaseHee/rhino-mcp/releases/tag/v0.6.0), [McNeel filter](https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/), [McNeel Data Dam](https://discourse.mcneel.com/t/toggle-data-dam/190183).

## 3. Контрааудит A — «GH idle + branch gate = безопасная трёхсторонняя синхронизация»
**Проверяемый ложный вывод:** gh_wait_idle, Stream Gate и Data Dam исключают циклы, подтверждают commit в Archicad и позволяют автоматически включить GH Design/Content Cache.

**Опровержение:** wait_for_idle опрашивает только GH solver, а не SceneWriter/SQLite, Archicad AddOn или файл PLN. Stream Gate выбирает ветвь данных, не владеет внешней транзакцией. Data Dam может пропускать данные при открытии .gh. Wasp gh_bake и EaseHee gh_bake_to_rhino являются отдельными write side effects. Нет GUID reconciliation, AC native readback, host/story/material/SEO проверки или cross-app rollback. **TRIAD_COMMIT_NOT_PROVEN**; не давать G3.

## 4. Контрааудит B — «новый MCP заменяет PR74 / умеет native Roof»
**Проверяемый ложный вывод:** 245 Rhino MCP tools, GH recipe idempotency и Rhino .3dm block/IFC достаточно, чтобы создавать/изменять native Archicad Roof/Wall/Window с тем же GUID.

**Опровержение:** Wasp и EaseHee управляют Rhino/GH, но не подтверждают AC29 native writer. GH component GUID, Rhino Object ID, IFC GlobalId и Archicad native GUID различны. GH bake/IFC/.3dm Hotlink не заменяют PR74 authored typed JSON→SceneWriter и не гарантируют native Roof/hostWall. №2 отдельно обнаружил существующий Beam CLI без второго writer, поэтому дублировать writer не нужно. **NATIVE_ROUNDTRIP_NOT_PROVEN**; не давать ACCEPTED.

## 5. Приоритет следующего интеграционного исследования №2

1. **I0955-01/02 (P0):** SOURCE-only сравнительная матрица Wasp v0.5.2 и уже известных GH мостов: gh_wait_idle, component schema, version gating, side effects; проверить, есть ли готовый read-only путь в существующий APA без новой записи.
2. **I0955-03 (P0):** EaseHee forced bridge против auto fallback, полная идентичность открытых .3dm/.gh/PLN/port, риск подмены проекта; ни одна проверка bridge не даёт права менять BIM.
3. **I0955-04/05 (P1):** официальные GH фильтры/селекторы; явно разделить выбор данных и выбор программы; контролировать единицы/владельца/число элементов.
4. **I0955-06/07 (P2):** лицензия/релизность Melanoplus и aphollis, без установки.
5. **№3:** независимо проверить формулу «GH idle != AC commit», отсутствие гарантии no-write у Data Dam/Stream Gate, и версионное расхождение main v0.6 vs released v0.5.2.

**Условие приёмки BUILD-01 остаётся прежним:** отдельный разрешённый scratch, verified runtime G0, typed intent G1/G2, единственный существующий SceneWriter, GUID+native type+host+floor+material readback, Save/Close/Reopen G4, независимая приёмка. До этого только SOURCE.

## 6. Ограничения
Отчёт не меняет PROJECT_PLAN rev182, NEXT_RESEARCH_PRIORITIES, матрицу 61, main, код, PLN/APX. Внешние репозитории и версии изучены документарно; они не установлены, не запускались и не интегрированы в APA. Проверка ветки/имени отчёта до записи выполнена. Два контрааудита внутренние, не независимый аудит №3. MODEL_MODE_NOT_VERIFIABLE.
