# APA №1 — 2026-10-24 03Z | Rhino8 Duplicate Content, Content Details, Cache Branch Names и контроль идентичности

**Исследователь №1. Режим:** SOURCE_ONLY, MODEL_MODE_NOT_VERIFIABLE. **Ветка публикации:** `research/apa-extension-ranking-hub-20261018`. **Только исследование:** нет установки, OFFLINE/LIVE, изменения main, кода, PLN/APX, Work/Codex/Arena, платных API или merge.

## 0. Реальное влияние на BUILD-01 #192

**Новая проверяемая дельта:** штатный Rhino8/Grasshopper1 содержит не только ранее изученные `Model Object` и `Content Cache`, но и **`Duplicate Content`** (отделение идентичности при создании варианта), **`Content Details`** (чтение cache membership, Rhino Object ID и атрибутов) и **`Branch Names`** (изоляция пространств имён блоков, слоёв и материалов между вариантами). Эти готовые средства уменьшают риск случайной замены Rhino-объектов и конфликтов имён, но **не сохраняют Archicad GUID, не создают нативные BIM-элементы и не синхронизируют автоматически три программы**. Особенно важно: обычная трансформация `Move` в Grasshopper по разъяснению McNeel порождает копию геометрии, а не гарантирует изменение исходного объекта. Значит, «одна форма визуально осталась» не доказывает identity-preserving roundtrip.

**Критическое ограничение BUILD-01:** свежий отчёт №2 02Z установил, что PR #74 authored layout принимает прямоугольные `outline/rooms`, X/Y bearingLines и один четырёхугольный Slab на этаж; `nativeComponents` не содержит свободные Slab/Beam/MultiPlane writer. Поэтому Rhino/GH не может автоматически направить произвольную сложную BREP в существующий PR74. Не расширять контракт без разрешения и не подменять нативную модель Morph/mesh.

**Статусы этого исследования:** SOURCE=26 конкретных документарных сверок (не 26 независимых документов), OFFLINE=0 новых, BUILD=0 новых, INSTALLED=NOT_VERIFIED, LIVE=0 новых, ACCEPTED=0 новых. G0=BLOCKED_RUNTIME, G1=NOT_RUN, G2=SOURCE_PARTIAL, G3=NOT_AUTHORIZED, G4=NOT_RUN, G5=NOT_RUN. FULL_THREE_WAY_NATIVE_GUID_PRESERVING_SYNC=NOT_PROVEN. PR74 21-элементный исторический прототип — не новая приёмка BUILD-01.

**Версии/лицензии:** Rhino 8 + встроенный Grasshopper1 (коммерческая лицензия Rhino; отдельный платный API не нужен); `Duplicate Content` объявлен разработчиком McNeel для Rhino 8.6 RC 20.02.2024, релиз Rhino 8.6.24101 датирован 10.04.2024; **фактическое присутствие в стабильной сборке и локальный Rhino SR не проверены**. Обновлённое руководство `Content Cache` написано для 8.8 RC 17.05.2024; существование стабильной ветки Rhino 8.8 подтверждено июнем 2024, но точный локальный build неизвестен. Исправление `RH-85560` заявлено для Rhino 8 SR16 (28.01.2025). AC29 build 5101/Tapir 1.5.10 — закреплённые ожидания, не текущий runtime receipt. GH–AC29 Live Connection build3000 — SOURCE, установка не проверена.

## 1. Пять карточек новых готовых механизмов и границ

### C01 — `Duplicate Content`: явное клонирование вместо неявной перезаписи Rhino GUID
- **Операция BUILD-01:** получить вариант сложной кровли или фасадного блока из исходного `Model Object` так, чтобы не перезаписать исходную геометрию Rhino при Bake/Push.
- **Первичный версионированный источник:** разработчик McNeel Kike Garcia, 20–23.02.2024, объявление `Duplicate Content` для Rhino 8.6 RC, затем Rhino 8.6 SR 8.6.24101 от 10.04.2024: https://discourse.mcneel.com/t/rhino-8-grasshopper-detach-guid-from-modelcontent/175548/9 ; https://discourse.mcneel.com/t/rhino-8-service-release-available/169739/7 .
- **Контракт:** `Duplicate Content` делает отдельную копию; имя и Parent необязательны. Исходный `Model Object` с ID при обычном Push/Cache может заменить оригинал; копия должна получить отдельный Rhino ID при размещении. `Duplicate Content` **не сохраняет исходный ID**: это специально новый объект.
- **Направление:** Rhino→GH read/duplicate→Rhino optional write. Никакой записи в Archicad.
- **Ограничение:** clone ≠ update, Rhino ID ≠ AC GUID. Не применять для модификации APA-owned AC элементов; не назначать клону старый `APA_ExternalId`. Локальная доступность не проверена.
- **№2 / I03-01:** без LIVE подготовить GH схему «исходный Model Object → Duplicate Content → новый APA_ExternalId → отдельный вариант» и таблицу запрета повторного AC GUID; проверить точный SR в будущем read-only G0.

### C02 — `Content Details`: штатная проверка скрытой принадлежности к Cache и реального Object ID
- **Операция:** перед передачей исходной геометрии в PR74 отличить оригинал, отслеживаемый кэш и отвязанный Bake; проверить, что выбран нужный объект и версия.
- **Первичный источник:** McNeel Scott Davidson, `Content Cache Updated Guide` для Rhino 8.8 RC, 17.05.2024, раздел Content Details: https://discourse.mcneel.com/t/content-cache-updated-guide/181883/1 .
- **Контракт:** `Content Details` выдаёт `Cache Name`, `Cached` bool, `Referenced`, полный `ID`, `Path` и `Attributes`. `Push` сохраняет членство в кэше, `Bake` снимает cache membership; наличие ID само по себе не означает membership.
- **Направление:** Rhino document→GH READ; при одном лишь Content Details записи нет.
- **Ограничение:** кэш-имя не гарантирует соответствия BIM-сущности; нельзя автоматически считать `Cache Name` обычным `User Text`. Нет AC GUID crosswalk.
- **№2 / I03-02:** подготовить таблицу read-only `Rhino ID / Cache Name / Cached / Referenced / Path / APA_ExternalId / owner`; запретить экспорт в PR74 при пустом, конфликтном или неоднозначном identity mapping.

### C03 — `Branch Names`: изоляция блоков, слоёв и материалов между вариантами
- **Операция:** иметь в одном Rhino-документе альтернативные фасады/кровли, где блоки `Column`, материалы и слои могут иметь одинаковые локальные имена.
- **Первичные источники:** McNeel Kike Garcia, 04.11.2023, и Scott Davidson, 17.05.2024: https://discourse.mcneel.com/t/grasshopper-rhino-bake-content-cache/168299/5 ; https://discourse.mcneel.com/t/content-cache-updated-guide/181883/1 .
- **Контракт:** опция `Branch Names` в `Content Cache` создаёт родительский слой по Cache Name, вложенные слои/имена; по разъяснению McNeel префиксы разделяют также блоки, материалы, типы линий, штриховки. Без изоляции одноимённый блок может переопределиться для двух вариантов.
- **Направление:** GH→Rhino write при Push/Bake, read через Query/Content Details; не GH→Archicad native.
- **Ограничение:** пространственная изоляция имён **не транзакция** и не защита от конфликта двух writers; Cache Name должен быть уникален для варианта. `Branch Names` может менять имена, поэтому сопоставление по имени в APA ненадёжно.
- **№2 / I03-03:** подготовить no-code правило имен `BUILD01/<sourceSha>/<variant>/<discipline>` для cache namespace (это предложение, не существующий контракт), сопоставлять по внешнему ID, а не по имени слоя; проверить блоки/материалы без LIVE.

### C04 — GH `Move`/Boolean/Trim: копия вместо гарантированного in-place изменения
- **Операция:** модифицировать Rhino-кровлю и ожидать, что идентичность останется неизменной после GH-прохода.
- **Первичный источник:** McNeel Scott Davidson, 27.05.2024, разъяснение по Content Cache, циклам и функциональной природе GH: https://discourse.mcneel.com/t/rhino-8-grasshopper-detach-guid-from-modelcontent/175548/22 .
- **Контракт:** трансформации/булевы операции/Trim могут выдавать новые геометрические значения, а не изменять тот же Rhino Object. McNeel отдельно предупреждает о циклической логике и отсутствии гарантии сходимости при многоуровневом Push/Pull.
- **Направление:** Rhino→GH geometry→GH geometry, identity continuity **не следует** из геометрического сходства; для Rhino→Rhino обновления нужен явный целевой ID/cache и независимый readback.
- **Ограничение:** конкретный эффект каждой комбинации компонентов и Rhino SR не испытан. Нельзя выдавать это за универсальную потерю ID при любом Move.
- **№2 / I03-04:** составить матрицу `reference Model Object → transform → Content Details → target ID` и сценарий STOP, если старый ID не доказан; без изменения AC-owned элементов.

### C05 — RH-85560 / 8.16: отдельная ошибка замены Model Object и пределы Action=False
- **Операция:** заменить геометрию существующего Rhino объекта из GH, не создавая дубликат, и остановить вычисление между стадиями.
- **Первичные источники:** McNeel Kike Garcia/Brian Gillespie, 22–28.01.2025, bug `RH-85560`, fixed Rhino 8 SR16: https://discourse.mcneel.com/t/q-why-is-replacing-geometry-not-working/197819/5 ; McNeel `Content Cache Updated Guide` 8.8 RC, 17.05.2024: https://discourse.mcneel.com/t/content-cache-updated-guide/181883/1 .
- **Контракт:** в Rhino 8 SR14/SR15 был воспроизводимый у пользователя случай отказа групповой замены Model Object; разработчик рекомендовал `Content Cache`, fix RH-85560 отмечен для SR16. У `Content Cache` Action=False подавляет выбранное действие, **но Result, если видим, продолжает Pull**. `Push` обновляет отслеживаемый объект; `Purge` может удалять объекты и определения, включая материалы и слои, когда они не используются.
- **Направление:** GH→Rhino WRITE, Rhino→GH READ; нет AC native WRITE. Это два направления **внутри пары Rhino/GH**, а не три программы.
- **Ограничение:** не утверждать, что любая сборка SR14/15 неисправна или что исправление RH-85560 автоматически решает все ошибки Content Cache. Action=False не означает остановку всех read/feedback loops.
- **№2 / I03-05:** при G0 read-only записать Rhino `SystemInfo` SR; для старых SR запретить заявлять update PASS без теста; в проектной GH-схеме разделить `Action` и `Result`, исключить цикл Pull→transform→Push, запретить `Purge` без отдельного допуска.

## 2. Журнал 26 выполненных SOURCE-сверок (проверены тексты, не запущены приложения)

| № | Проверенное утверждение | Первичный источник / результат |
|---|---|---|
| 01 | Исследовательская ветка `research/apa-extension-ranking-hub-20261018` существует | GitHub search_branches: PASS |
| 02 | P0 TRIAD-PIVOT требует без нового writer | `research-1-20261023T11Z-TRIAD-PIVOT.md`: PASS |
| 03 | BUILD-01 G0→G5 и запрет повторного CREATE | issue #192: PASS |
| 04 | PR74 содержит 21 native element, не универсальный BUILD-01 | PR #74: PASS |
| 05 | PR74 параметрические правки не покрывают Roof contour/slope | PR #74 описание: PASS |
| 06 | №2 02Z фиксирует rectangular `layout.outline/rooms` | `research-2-integration-2026-10-24T02Z-report.md`: PASS |
| 07 | №2 02Z фиксирует один rectangular Slab/story | тот же файл: PASS |
| 08 | №2 02Z фиксирует отсутствие Beam/GenericOpening в nativeComponents allowlist | тот же файл: PASS |
| 09 | Матрица содержит `count=61` | `priority_matrix_20261018.json`: PASS |
| 10 | Последние доступные файлы №3 в hourly датированы 20.10.2026 | listing hourly + `audit-2026-10-20-18-A/B.md`: PASS, не выдавать за свежий аудит |
| 11 | `Duplicate Content` объявлен разработчиком для Rhino 8.6 RC | https://discourse.mcneel.com/t/rhino-8-grasshopper-detach-guid-from-modelcontent/175548/9 : PASS |
| 12 | `Duplicate Content` всегда создаёт копию; Name/Parent optional | https://discourse.mcneel.com/t/rhino-8-grasshopper-detach-guid-from-modelcontent/175548/14 : PASS |
| 13 | Rhino 8 SR6 8.6.24101 выпущен 10.04.2024 | https://discourse.mcneel.com/t/rhino-8-service-release-available/169739/7 : PASS |
| 14 | У `Model Object` с ID есть риск замены оригинала при Bake/Push | https://discourse.mcneel.com/t/content-cache-updated-guide/181883/1 : PASS |
| 15 | `Content Cache` имеет Push/Pull/Bake/Purge | тот же источник: PASS |
| 16 | `Pull` возвращает Rhino Object ID | тот же источник: PASS |
| 17 | `Push` отслеживает объект и обновляет вместо создания дубля | тот же источник: PASS |
| 18 | `Bake` отвязывает cache membership, но при входном ID возможна замена | тот же источник: PASS |
| 19 | `Purge` может удалить объекты/определения, если не используются | тот же источник: PASS |
| 20 | `Action=False` не отключает `Result` Pull | тот же источник: PASS |
| 21 | `Content Details` выводит Cache Name/Cached/Referenced/ID/Path/Attributes | тот же источник: PASS |
| 22 | `Branch Names` создаёт parent layer для варианта | тот же источник: PASS |
| 23 | Разработчик описал конфликт одноимённых блоков без Branch Names | https://discourse.mcneel.com/t/grasshopper-rhino-bake-content-cache/168299/5 : PASS |
| 24 | McNeel предупреждает о копировании при GH Move/Boolean/Trim и циклах | https://discourse.mcneel.com/t/rhino-8-grasshopper-detach-guid-from-modelcontent/175548/22 : PASS |
| 25 | RH-85560 Model Object replacement bug, fixed SR16 | https://discourse.mcneel.com/t/q-why-is-replacing-geometry-not-working/197819/5 : PASS |
| 26 | Последняя исследовательская №1 02Z не содержала Duplicate Content/Content Details/Branch Names как отдельных карточек | `research-1-20261024T02Z-TRIAD-NATIVE-RHINO8-ROUTING-HOPS-ELEFRONT.md` и этот отчёт: PASS |

**Границы подсчёта:** это 26 конкретных проверок утверждений по источникам и репозиторию, а не 26 независимых сайтов, не 26 экспериментов и не доказательство локальной совместимости. Источники McNeel — официальные разъяснения сотрудников в профильном форуме, но отдельные старые версии могут отличаться от текущего Rhino SR.

## 3. Контрааудит A — подмена identity-preserving UPDATE клонированием

**Проверка:** `Duplicate Content` может безопасно отделить вариант Rhino от оригинала, но новый Rhino Object ID **прямо противоречит** требованию сохранить прежний GUID при редактировании того же BIM-элемента. Если применить его к APA-owned объекту и затем создать новый AC элемент, получится дублирование, а не правка. `Content Cache` может заменять по входному ID; это иной маршрут. **Вердикт:** C01 допустим только для новых вариантов/не-APA-owned копий; AC-native UPDATE остаётся через существующий SceneWriter/Modify и независимый GUID readback. Доказанной трёхсторонней синхронизации нет.

## 4. Контрааудит B — cache namespace не равен distributed lock/transaction

**Проверка:** `Branch Names` уменьшает коллизии имён блоков/материалов/слоёв, но не блокирует конкурирующую запись и не делает AC+Rhino+GH атомарной транзакцией. `Content Details` показывает membership/ID только в Rhino, а `Action=False` может продолжать Pull. Повторный Push после ручного изменения может перезаписать геометрию; при неизвестном результате необходим STOP/read-only reconciliation. **Вердикт:** нельзя считать эту связку автоматическим three-way sync, rollback или нормативной BIM-приёмкой.

## 5. Адресное поручение №2 / следующий безопасный шаг

**I03-01..05:** (1) сравнить штатный `Duplicate Content` с уже известными `Model Object`/`Content Cache` на уровне SOURCE и версии; (2) добавить в предлагаемую GH-схему **read-only** `Content Details` и identity crosswalk, не менять код; (3) разделить имена вариантов через `Branch Names`, но не использовать имена как GUID; (4) зафиксировать STOP для геометрических трансформаций, потерявших Rhino ID; (5) подготовить read-only `SystemInfo` Rhino SR и защиту от RH-85560/Action=False Pull. Все проверки на существующем BUILD-01 только после отдельного допуска, без установки и без LIVE.

**Единый поддержанный маршрут пока остаётся ограниченным:** Rhino8/GH READ+parametric подготовка → только поддержанный authored JSON PR74 → SceneWriter/SQLite → Tapir1.5.10 → AC29 native readback. Автоматическая смена исполняемой программы, полноценный обратный AC→GH/Rhino sync и сохранение всех GUID/материалов/проёмов/сложной кровли в одном цикле: **NOT_PROVEN**.

## 6. Ссылки на проектные источники
- BUILD-01: https://github.com/dvikt33-ux/safe-bim-layer/issues/192
- PR74: https://github.com/dvikt33-ux/safe-bim-layer/pull/74
- Pivot: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md
- Priorities: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md
- №2 02Z: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-24T02Z-report.md
- №3 last found: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md
- Matrix61: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json
- PROJECT_PLAN rev182: только чтение, не изменялся.

**Заключение:** 5 новых SOURCE-карточек, 26 проверок, 2 контрааудита; ни одного нового инженерного PASS, установки или LIVE. MODEL_MODE_NOT_VERIFIABLE.
