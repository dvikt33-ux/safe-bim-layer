# APA №1 — 2026-10-24 02Z: нативная маршрутизация Rhino 8, пределы Hops и риск BakeName

**Исследователь:** №1. **Дата:** 2026-10-24 02Z / 05:00 МСК. **Режим:** SOURCE_ONLY; MODEL_MODE_NOT_VERIFIABLE. **Ветка:** `research/apa-extension-ranking-hub-20261018`. Никаких LIVE, OFFLINE-прогонов, установки ПО, нового writer, изменений main/кода/PLN/APX, Work/Codex/Arena, платных API или merge.

## 0. Прямое влияние на BUILD-01 #192

**Новая полезная возможность:** в **штатном Grasshopper 1 для Rhino 8** существуют `Query Model Objects → Group Content / Match Text Filter → Filter Content`, позволяющие маршрутизировать *объекты и ветви данных* по `User Text`, слою и типу, без нового расширения, скрипта или второго writer. Это частичный, документированный компонент P0 **выбора геометрической операции** (например, отделить стены, перекрытия, кровли и элементы с owner=APA). **Это НЕ автоматический выбор исполняемого приложения, НЕ вызов Archicad API и НЕ трёхсторонняя синхронизация.** Для BUILD-01 допустим только направленный маршрут: Rhino8/GH READ/parametric → существующий authored JSON PR74 → SceneWriter/SQLite → Tapir 1.5.10 → Archicad29 native readback. Прямой GH–AC `Synchronize=True` для APA-owned GUID не разрешён.

**Новый риск:** `eleFront Bake` с `BakeName` **удаляет ранее созданные им объекты Rhino и создаёт новые**, то есть подавление дублей не равно сохранению Rhino Object ID. **Второй риск:** `Hops` / `rhino.compute` выполняет GH в другом контексте документа; `Query Model Objects` и `eleFront Reference By Layer` не смогли увидеть активные объекты в задокументированном случае Rhino 8 SR15. Для identity-sensitive BUILD-01 это **SOURCE_RISK**, а не доказанная несовместимость всех будущих версий.

**Статусы данного прохода:** SOURCE=26 предметных документарных сверок (не 26 независимых источников); OFFLINE=0 новых; BUILD=0 новых; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0 новых. G0=BLOCKED_RUNTIME, G1=NOT_RUN, G2=SOURCE_PARTIAL, G3=NOT_AUTHORIZED, G4/G5=NOT_RUN. Трёхсторонняя автоматическая native GUID-preserving sync=NOT_PROVEN. Исторический PR74 21-элементный результат не является BUILD-01.

**Версии и лицензии:** Rhino 8/Grasshopper 1 — штатные компоненты в коммерчески лицензируемом Rhino 8 (точный локальный SR неизвестен); Graphisoft GH–AC29 Live Connection **29 build 3000**, Windows/Rhino7–8, официальный пакет от 01.10.2025, бесплатный add-on при отдельно лицензированных продуктах; Archicad executable build 5101 не равен build3000 дополнения. Tapir локально заявлен 1.5.10, actual APX/registration не проверены. eleFront — бесплатное дополнение по документации разработчика VIA 2026, **точная версия установленного пакета и его лицензия на перераспространение не проверены**; никакой установки не делалось. Hops case: Rhino **8 SR15 8.15.25019.13001** на Windows, форум McNeel 14.04–18.06.2025; версия самого Hops в сообщении не указана.

## 1. Пять карточек новой предметной дельты

### C01 — Встроенная маршрутизация геометрии по BIM-метаданным без Elefront
- **Операция BUILD-01:** в Rhino8 выбирать все объекты, относящиеся к этажу, зданию, типу или владельцу, затем подавать соответствующие контуры в готовые GH-ветви (Wall/Slab/Roof/Opening).
- **Официальный первоисточник:** McNeel, *Rhino 8 — Grouping and Filtering Data*, https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/ ; *Object Attributes in Grasshopper*, https://www.rhino3d.com/docs/guides/grasshopper/object-attributes/ .
- **Точный контракт:** `Query Model Objects` (Rhino tab → Object) фильтрует активный Rhino документ по `Layer` (поддерживает wildcard `Floors*`); `Group Content` выбирает `Key → Model Object → User Text → <key>` и группирует по значениям; `Match Text Filter` с `Equals` и `Filter Content` выбирают подходящие объекты; `Greater Than Filter` поддерживает числовые ограничения. Пример производителя: `Use Type=Office`, площади 2250–2500 sq ft. 
- **Направление:** Rhino active document → GH READ / filtering / routing; НЕТ Archicad WRITE. `User Text` — пользовательский тег, **не Archicad GUID, не классификация AC**. Возможны пустые/дублированные значения, ошибочный owner, отсутствующие слои. 
- **Поручение №2 I02-01:** SOURCE-only таблица `UserText: APA_Type / APA_Story / APA_Owner / APA_ExternalId` → фильтр → разрешённая authored ветвь; перечислить обязательные проверки uniqueness, non-null, type allowlist, units, story binding, запрет прямого `Synchronize`. Не создавать новый сериализатор или writer. Для APA-owned всегда SceneWriter.

### C02 — Rhino8 Model Object pass-through и Import Model: атрибуты + нормализация единиц
- **Операция:** принять внешний .3dm/другую 3D-модель и сохранить при подготовке GH геометрию, имя, слой, материал и пользовательские свойства; проверить масштаб перед передачей этажей/стен/кровли в PR74.
- **Официальный первоисточник:** McNeel, *Object Attributes in Grasshopper* (Rhino8), https://www.rhino3d.com/docs/guides/grasshopper/object-attributes/ .
- **Контракт:** `Model Object` (Rhino tab) — pass-through: первый вход/выход несёт объект, дополнительные входы могут переопределить отдельные атрибуты, не требуя вручную собирать остальные; `Query Layers`/ `Query Materials` возвращают объекты активного Rhino-документа. `Import Model` (Params → Input) раскрывает атрибуты импортированного 3D-файла и предоставляет `Transform` для приведения геометрии к единицам активного документа. Это **возможность выполнить преобразование**, не гарантия автоматической нормализации при любом импорте.
- **Направление:** file → GH/Rhino read/transform, GH preview; `Bake` → Rhino WRITE только при явном действии; **не** AC native write. Материал Rhino display ≠ AC BuildingMaterial GUID. Rhino ID ≠ AC GUID.
- **Поручение №2 I02-02:** до JSON зафиксировать `sourceUnits, targetUnits=meters, scaleFactor, transform, objectId, layer, materialName, userText`; сверить Z с `GetStories`, материал AC по реальному GUID, хеш `.3dm/.gh/JSON`; ни одного нового WRITE.

### C03 — eleFront бесплатен, но BakeName не сохраняет идентичность
- **Операция:** параметрическая повторная сборка фасадных деталей/блоков в Rhino с метаданными и отсутствием дублей.
- **Первичный источник производителя VIA:** `Welcome` https://elefront.via.inc/docs/eleFront%20Primer/Welcome/ (free download через Rhino PackageManager), `Bake` https://elefront.via.inc/docs/eleFront%20Primer/Bake/ .
- **Точный контракт:** `Bake` задаёт атрибуты объектам; при использовании `BakeName` каждый новый запуск удаляет все ранее созданные этим компонентом Rhino-объекты и создаёт новые; `GUID Output` отдаёт Ghost-представления созданных объектов. `Safest/Moderate/Bulldoze` пресеты регулируют, среди прочего, конфликты block definition/dimension style, **не обещают сохранение прежнего Rhino ID**.
- **Направление:** GH → Rhino WRITE; Rhino → GH Reference (отдельно), **не** Archicad native; no cross-app rollback. Точная версия/совместимость установленного Rhino8 не подтверждены. Free-download не доказывает open-source лицензию.
- **Поручение №2 I02-03:** исключить `BakeName` из identity-sensitive пути BUILD-01; сравнить со штатным Rhino8 Content Cache ID-preserving поведением (исследование №1 01Z); если eleFront нужен для вспомогательных **Rhino-only** деталей, отметить как disposable, без привязки к Archicad GUID.

### C04 — Hops/compute не годится как доказанный stateful read активного Rhino8
- **Операция:** вынести часть вычислений GH в Hops и затем читать тот же объект Rhino по слою/UserText.
- **Первоисточник — зарегистрированный случай и комментарии на официальном форуме McNeel:** https://discourse.mcneel.com/t/rhino-8-query-model-objects-component-not-working-with-hops/203059 ; 14.04.2025 Rhino8 SR15 Windows, обсуждение 17–18.06.2025, ответ Andy Payne (McNeel).
- **Наблюдавшийся контракт/ограничение:** `Query Model Objects` внутри Hops не вернул активные объекты; аналогично `eleFront Reference By Layer`. Участник поясняет, что rhino.compute запускает отдельный контекст документа, и предложил сначала извлекать данные в основном Rhino, затем передавать базовые типы `Brep/Mesh/int/string` в Hops; `Model Object` как I/O на тот момент не поддерживался. McNeel выразил надежду на будущую поддержку в Rhino9 WIP, **это не доказательство исправления в Rhino8 в октябре 2026**.
- **Направление:** GH data → compute → GH result (потенциально), **не** доступ к active Rhino document, **не** AC sync. Ограничение конкретного SR; текущая версия не проверена.
- **Поручение №2 I02-04:** не включать Hops в критическую ветвь `active document identity / UserText / Rhino Object ID`; оставлять `Query Model Objects` в главной GH definition; Hops рассматривать только для stateless расчётов с явным входом, после независимой проверки.

### C05 — Версионный фильтр: исторический Rhino GDL/LCF Observer не является AC29-решением
- **Операция:** попытка обновлять GDL-библиотеки Archicad из Rhino через готовый старый Rhino LCF Observer.
- **Официальный первоисточник:** Graphisoft, *Rhino–Grasshopper–Archicad Toolset*, https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ , разделы `Rhinoceros – GDL Converter`, `Rhino LCF Observer`, `Grasshopper–Archicad 29`.
- **Точный контракт:** исторический `GSM-LCF exporter for Rhino 5`; Observer показан для **Archicad 18/19/20**. Для Archicad25+ 3DM Import/Export встроен, но импортированная геометрия не доказывает native Wall/Roof/Window BIM. AC29 GH Live Connection имеет отдельный пакет 29 build3000 (01.10.2025, Windows Rhino7/8); не подменять его AC30 build3000 (07.10.2026).
- **Направление:** Rhino5 → GSM/LCF → старый Archicad object library; **не** штатная двусторонняя AC29 native BIM sync.
- **Поручение №2 I02-05:** пометить старый Observer `NOT_APPLICABLE_AC29`; не скачивать/не устанавливать его для BUILD-01; в матрице разделить 3DM/GDL import, GH native authoring и APA SceneWriter native writer.

## 2. Двадцать шесть фактически сверенных SOURCE-позиций

В каждой строке сверена конкретная формулировка в указанном первоисточнике. Это 26 **документарных утверждений**, а не 26 запусков, проверок установленного ПО или независимых публикаций.

| № | Проверяемое утверждение | Результат | Первоисточник |
|---:|---|---|---|
| 01 | Rhino8 GH1 содержит `Query Model Objects` | SOURCE_PASS | [McNeel filter](https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/) |
| 02 | `Query Model Objects` читает активный Rhino document | SOURCE_PASS | [McNeel filter](https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/) |
| 03 | Фильтр `Layer` допускает wildcard `Floors*` | SOURCE_PASS | [McNeel filter](https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/) |
| 04 | `Group Content` группирует по Model Object → User Text | SOURCE_PASS | [McNeel filter](https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/) |
| 05 | `Group Content` выдаёт ветви и уникальные `Values` | SOURCE_PASS | [McNeel filter](https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/) |
| 06 | `Match Text Filter` поддерживает `Equals` | SOURCE_PASS | [McNeel filter](https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/) |
| 07 | `Filter Content` выбирает совпавшие объекты | SOURCE_PASS | [McNeel filter](https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/) |
| 08 | `Greater Than Filter` фильтрует числовые значения | SOURCE_PASS | [McNeel filter](https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/) |
| 09 | Rhino8 GH1 содержит нативные типы Layer/Material | SOURCE_PASS | [McNeel attributes](https://www.rhino3d.com/docs/guides/grasshopper/object-attributes/) |
| 10 | `Query Layers` получает атрибуты слоя из документа | SOURCE_PASS | [McNeel attributes](https://www.rhino3d.com/docs/guides/grasshopper/object-attributes/) |
| 11 | Pass-through позволяет переопределить один атрибут | SOURCE_PASS | [McNeel attributes](https://www.rhino3d.com/docs/guides/grasshopper/object-attributes/) |
| 12 | `Model Object` может задавать имя и слой геометрии | SOURCE_PASS | [McNeel attributes](https://www.rhino3d.com/docs/guides/grasshopper/object-attributes/) |
| 13 | Для появления объекта в Rhino нужен Bake | SOURCE_PASS | [McNeel attributes](https://www.rhino3d.com/docs/guides/grasshopper/object-attributes/) |
| 14 | `Import Model` доступен в Params → Input | SOURCE_PASS | [McNeel attributes](https://www.rhino3d.com/docs/guides/grasshopper/object-attributes/) |
| 15 | `Import Model` раскрывает атрибуты внешней 3D-модели | SOURCE_PASS | [McNeel attributes](https://www.rhino3d.com/docs/guides/grasshopper/object-attributes/) |
| 16 | `Import Model` даёт Transform для согласования единиц | SOURCE_PASS | [McNeel attributes](https://www.rhino3d.com/docs/guides/grasshopper/object-attributes/) |
| 17 | `Query Materials` поддерживает Rhino material preview | SOURCE_PASS | [McNeel attributes](https://www.rhino3d.com/docs/guides/grasshopper/object-attributes/) |
| 18 | eleFront распространяется бесплатно через PackageManager | SOURCE_PASS | [VIA welcome](https://elefront.via.inc/docs/eleFront%20Primer/Welcome/) |
| 19 | eleFront BakeName удаляет прежние объекты и создаёт новые | SOURCE_PASS | [VIA Bake](https://elefront.via.inc/docs/eleFront%20Primer/Bake/) |
| 20 | eleFront имеет `Safest/Moderate/Bulldoze` пресеты | SOURCE_PASS | [VIA Bake](https://elefront.via.inc/docs/eleFront%20Primer/Bake/) |
| 21 | eleFront `GUID Output` возвращает Ghost объектов Bake | SOURCE_PASS | [VIA Bake](https://elefront.via.inc/docs/eleFront%20Primer/Bake/) |
| 22 | В Rhino8 SR15 `Query Model Objects` внутри Hops был пуст | SOURCE_CASE_CONFIRMED | [McNeel forum](https://discourse.mcneel.com/t/rhino-8-query-model-objects-component-not-working-with-hops/203059) |
| 23 | В том же кейсе `Reference By Layer` не видел активный Rhino | SOURCE_CASE_CONFIRMED | [McNeel forum](https://discourse.mcneel.com/t/rhino-8-query-model-objects-component-not-working-with-hops/203059) |
| 24 | McNeel не подтвердил Rhino8 Model Object Hops I/O в июне 2025 | SOURCE_CASE_CONFIRMED | [McNeel forum](https://discourse.mcneel.com/t/rhino-8-query-model-objects-component-not-working-with-hops/203059) |
| 25 | Graphisoft AC29 Live Connection = build3000, Rhino7/8 Windows | SOURCE_PASS | [Graphisoft downloads](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/) |
| 26 | Исторический Rhino5 GDL/LCF Observer не заявлен для AC29 | SOURCE_PASS | [Graphisoft downloads](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/) |

## 3. Два контрааудита

### A — не является ли встроенный GH filter уже готовым автоматическим выбором программ?
**Опровергаемое предположение:** `Query Model Objects → Group/Filter` автоматически решает, в какой из трёх программ исполнять операцию, и синхронизирует нативный GUID. **Сверка:** McNeel документирует выбор *объектов и data-tree branches внутри GH*; Graphisoft документирует отдельный Live Connection, а APA PR74 — отдельный SceneWriter. Нет контракта dispatch в Archicad, нет global identity map, нет cross-app atomic commit и обратного подтверждения. **Вердикт:** `P0_DATA_ROUTING_SOURCE_CONFIRMED`, `P0_PROGRAM_ROUTING_AND_THREE_WAY_SYNC_NOT_PROVEN`. Без нового writer допустимо использовать фильтры как подготовительный слой GH, но исполнять APA-owned native только существующим SceneWriter.

### B — не сохраняет ли eleFront BakeName GUID и не исправлен ли Hops в новых версиях?
**Опровергаемое предположение:** Elefront предотвращает дубли, значит сохраняет Rhino ID; Hops умеет stateful read и можно без проверки заменить локальную GH definition. **Сверка:** VIA прямо пишет `removed from document before new objects are created`; `GUID Output` — GUID *нового* Bake, не гарантия старого. Форум McNeel содержит конкретный Rhino8 SR15 failure и лишь надежду на поддержку в Rhino9 WIP. Нет установленной версии Rhino8/Hops/eleFront и свежего воспроизводимого LIVE. **Вердикт:** `BAKENAME_DESTRUCTIVE_TO_RHINO_ID` (документарно); `HOPS_ACTIVE_DOCUMENT_READ_NOT_QUALIFIED`, **не** `ALL_RHINO8_HOPS_BROKEN`. Предпочитать Rhino8 native `Model Object` и штатный Content Cache с известным ID; не запускать Bake в исследовательском проходе.

## 4. Согласование с другими потоками и 61-кандидатной матрицей

Прочитаны: [BUILD-01 #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192), [PR #74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74), `docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md`, pivot `research-1-20261023T11Z-TRIAD-PIVOT.md`, [№1 01Z](research-1-20261024T01Z-TRIAD-DECONSTRUCT-ROOF-ID-GATES.md), [№2 01Z](research-2-integration-2026-10-24T01Z-triad-report.md), [№2 01Z контрааудиты](research-2-integration-2026-10-24T01Z-triad-audits.md), [№3 20.10 18Z A](audit-2026-10-20-18-A.md) и [B](audit-2026-10-20-18-B.md), `priority_matrix_20261018.json` (`count=61`, исходник прочитан, **пересчёт рейтингов не выполнялся**). `PROJECT_PLAN rev182` не изменялся и не использовался как WRITE-разрешение.

**Недублирование:** №1 01Z уже нашёл `Model Object` vs `Brep` и Content Cache ID; №2 01Z уже выявил **SOURCE_STATIC_CONTRACT_MISMATCH**: legacy `building-shell-v1` задаёт Slab level=0 на втором этаже, тогда как authored использует абсолютный уровень. Это **не** новая находка №1 и **не** LIVE-баг. В этом проходе новые: native `Group/Filter Content` по UserText, `Import Model` с единицами, eleFront `BakeName` destructive, Hops stateful limitation, исторический LCF version gate.

**Адресная передача №2:** I02-01 metadata selection; I02-02 units/material gate; I02-03 avoid destructive BakeName; I02-04 no Hops for active-doc reads; I02-05 reject obsolete GDL observer. **Инженеру BUILD-01:** после отдельного разрешения только G0 read-only → G1 authored preflight, с проверкой absolute Slab Z и владельца GUID. Никаких новых writers/routers и прямой GH записи в APA-owned.

## 5. Итог
- `SOURCE`: 26 документарных позиций / 5 карточек / 2 контрааудита; это **не** 26 отдельных документов или испытаний.
- `OFFLINE=0; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0; ACCEPTED=0`.
- `FULL_AUTOMATIC_NATIVE_THREE_WAY_SYNC=NOT_PROVEN`.
- `MODEL_MODE_NOT_VERIFIABLE`.
- Публикация в research branch и проверка commit SHA/readback выполняются **после** составления данного текста; не считать отчёт опубликованным до точного сравнения.
