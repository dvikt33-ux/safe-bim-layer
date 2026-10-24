# APA №1 — TRIAD / Hotlink cache, IFC georeferencing, Teamwork locks и Speckle: границы нативной синхронизации
**Дата исследования:** 2026-10-23 22:58 UTC / 2026-10-24 01:58 МСК. **MODEL_MODE_NOT_VERIFIABLE.**
**Режим:** исключительно SOURCE / GitHub READ + публикация этого исследовательского текста. Ни LIVE, ни установки, ни изменения кода, PLN, APX, main или исторического PROJECT_PLAN.

## 0. Влияние на трёхстороннюю сборку BUILD-01 (#192)
**Новый практический результат:** у Tapir появились штатные операции обновления/перепривязки Hotlink-модулей (v1.7.1), полное описание IFC map conversion и survey point (v1.7.0), а также Teamwork-блокировки наборов атрибутов и Hotlink cache (v1.7.1). Это кандидаты для G0/G2/G4: проверка внешних источников, координат и конкурирующих изменений. **Они НЕ доказывают сохранение native GUID дочерних Hotlink-элементов, не создают триадный router и отсутствуют в сохранённой схеме Tapir 1.5.10.** Speckle поддерживает обмен Archicad29/Rhino8/GH, но принимает Rhino/GH геометрию в Archicad как **GDL Objects**, а не нативные Wall/Slab/Roof/Door/Window; потому НЕ замена PR74/SceneWriter. Для BUILD-01 единственный предусмотренный writer — существующий DynamicCommands → BIM Graph → SceneWriter → SQLite.

**Статусы именно ЭТОГО прохода:** SOURCE=30 отдельных документарных утверждений/сверок (не 30 независимых источников); OFFLINE=0 новых; BUILD=0 новых; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0 новых. G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4=NOT_RUN; G5=NOT_RUN. FULL_AUTOMATIC_THREE_WAY_GUID_PRESERVING_SYNC=NOT_PROVEN. Исторический PR74 21-элементный LIVE/Save-Open не относится к новому BUILD-01.

## 1. Сверенная база и границы новизны
- BUILD-01 issue: https://github.com/dvikt33-ux/safe-bim-layer/issues/192 ; PR74: https://github.com/dvikt33-ux/safe-bim-layer/pull/74 .
- TRIAD-PIVOT: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md ; NEXT: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md .
- **Сохранённый Tapir 1.5.10**, immutable commit `f7c37b84b76c040c417ccd58a5543326e50f673a`, Git blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json . JSON разобран: **262 команды**; `GetGeoLocation` v1.1.6, `SetGeoLocation` v1.2.9 присутствуют; **нет** `xAxisAbscissa`, `xAxisOrdinate`, `positionInProject`, `UpdateHotlinks`, `ChangeHotlinkNodes`, `ReserveLockableObjectSet`, `ReserveHotlinkCacheManagement`. Наличие отдельного `scale` в других местах JSON не считается наличием `surveyPoint.geoReferencingParameters.scale`: этого поля там нет.
- Матрица 61, Git blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`: JSON реально `count=61`, 61 item, 61 уникальный ID; GH имеет исторический priority 40/100, `ИССЛЕДОВАТЬ_ТОЧКУ_ПОДКЛЮЧЕНИЯ`; рейтинг не отменяет TRIAD P0.
- Прочитан **свежий №2 22Z**, blob `1281808f42b882f44fbdef7aca7eab8ebfb1792c`: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T22Z-triad-report.md . Уже известные ему риски GH Embedded Library deletion, Publisher Auto Hotlink Update (вне PLN) и условный автоматический `Sync Changes to GH` **НЕ объявляются новыми**. В отличие от него, здесь проверены именно API-контракты Tapir UpdateHotlinks/ChangeHotlinkNodes, IFC coordinate fields и Teamwork locks.
- Последний прямо прочитанный №3: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md и -B.md. Более поздний №3 не подтверждён; проверка последних 80 commit сообщений ветки не является полным обходом всех файлов. PROJECT_PLAN rev182 в данном проходе не извлечён, **не подменять** rev197, ничего не менять.

## 2. Пять карточек: операция → первоисточник/версия/лицензия → точный контракт/направление → ограничение → №2

### C1 / P0 — Обновление и перепривязка Hotlink cache, без собственного writer
**Операция BUILD-01:** после изменения внешнего .mod/.pln модуля определить, как штатно обновить кэш либо сменить источник; в G4 сравнить нативные GUID/типы/этажи/связи до/после. 
**Источник:** Tapir PR #790, merged 12.10.2026, команды v1.7.1, включены в upstream release 1.7.1/1.7.2: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/790 ; release: https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.2 . Лицензия Tapir MIT (репозиторий https://github.com/ENZYME-APD/tapir-archicad-automation).
**Контракт:** `UpdateHotlinks` WRITE, вход `hotlinkNodes:[{hotlinkNodeId}]`, вызов `ACAPI_Hotlink_UpdateHotlinkCache`; `ChangeHotlinkNodes` WRITE, `hotlinkNodes:[{hotlinkNodeId,sourceLocation}]`, вызов `ACAPI_Hotlink_ModifyHotlinkNode`; ответы `executionResults` по каждому node. Направление: внешний модуль → кэш Hotlink внутри Archicad, не GH/Rhino двусторонняя синхронизация.
**Предел:** НЕ undoable по реализации PR; автор исходно предупреждал об отсутствии seat test, хотя merge и CI состоялись. Стабильность GUID дочерних элементов после обновления НЕ доказана; исходник может быть недоступен. В pinned 1.5.10 обе команды отсутствуют. Режим Auto Hotlink Update в пользовательских Preferences может сработать при Publisher независимо от этих команд (уже обнаружено №2).
**№2:** подготовить только SOURCE-карту `nodeId → sourceLocation → source SHA → instances → expected child GUID` и read-only G4 check; запретить update/relink до отдельного разрешения и runtime G0.

### C2 / P0 — Полная ориентация IFC MapConversion, исключение скрытого поворота/масштаба
**Операция:** сопоставление геометрии Rhino/GH (м, project axes) с Archicad и IFC при G1/G4; отличать `north` от IFC оси X.
**Источник:** Tapir PR #732, merged 02.10.2026, upstream 1.7.0, MIT: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/732 ; релизы: https://github.com/ENZYME-APD/tapir-archicad-automation/releases .
**Контракт:** `GetGeoLocation` READ / `SetGeoLocation` WRITE, три поля `surveyPoint.geoReferencingParameters.{xAxisAbscissa,xAxisOrdinate,scale}` (на GET обязательны, на SET необязательны). IFC `XAxisAbscissa=cos(theta)`, `XAxisOrdinate=sin(theta)`, `Scale` — отдельно от `projectLocation.north`. GH `ProjectLocation` и `SetProjectLocation` получили соответствующие выходы/входы. Направление: AC↔API параметров геопривязки, НЕ AC↔Rhino sync.
**Предел:** pinned 1.5.10 эти поля не имеет. Точность на AC29 build5101 не измерена; исходный PR требует live подтверждения expected readback. Изменение SetGeoLocation — запрещённая WRITE-операция.
**№2:** для будущей G0 таблицы сравнения составить `units, origin, north, XAxisAbscissa, XAxisOrdinate, Scale, IFC CRS` и fail-closed правило при неполной информации; не устанавливать новый Tapir.

### C3 / P0 — Позиция Survey Point в системе проекта
**Операция:** отличить `surveyPoint.position` (easting/northing/elevation карты) от положения Survey Point в локальной системе Archicad, прежде чем переводить координаты GH/Rhino.
**Источник:** Tapir PR #745, merged 03.10.2026, upstream 1.7.0, MIT: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/745 .
**Контракт:** `GetGeoLocation` READ добавляет `surveyPoint.positionInProject:{x,y,z}` (всегда в ответе); `SetGeoLocation` WRITE принимает опционально весь объект `{x,y,z}`. GH `ProjectLocation/SetProjectLocation` получают три порта; SET передаёт объект только при наличии всех трёх чисел. Направление: Archicad ↔ JSON/GH параметров, НЕ универсальная обратная запись геометрии.
**Предел:** не включает lock/visibility Survey Point; pinned 1.5.10 `positionInProject` не имеет; GUID сохранение элементов никак не связано с этим чтением.
**№2:** документировать формулу/происхождение локального origin для G1, добавить обязательный контроль до переноса Rhino 3DM координат; никакого SetGeoLocation.

### C4 / P1 — Готовые Teamwork-блокировки наборов атрибутов и Hotlink cache
**Операция:** при потенциальной совместной работе отличать право менять элементы от права менять Composites/ProjectInfo/Hotlink cache; избегать параллельной смены источников.
**Источник:** Tapir PR #795, merged 09.10.2026, upstream 1.7.1, MIT: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/795 .
**Контракт:** `GetLockableObjectSetStatus({objectSetName})` READ → `status: Free|Editable|Locked|NotAvailable|NotExist` и optional `conflicts`; `ReserveLockableObjectSet` / `ReleaseLockableObjectSet` WRITE; `ReserveHotlinkCacheManagement` / `ReleaseHotlinkCacheManagement` WRITE. Для резервации конфликт `{userId,userName}`. Направление только Archicad Teamwork/BIMcloud, НЕ распределённая блокировка Rhino/GH/APA.
**Предел:** upstream maintainer подтвердил AC27 Mac BIMcloud LIVE, но **не** AC29 Win11 build5101 и не локальный APA; в одиночном PLN `NotExist`/нет Teamwork, блокировка не действует. Команды отсутствуют в pinned 1.5.10. Нет автоматической интеграции с UpdateHotlinks.
**№2:** read-only таблица «тип PLN: solo/teamwork → object set → ожидаемое право → блокирующий actor», не резервировать/освобождать и не менять Teamwork.

### C5 / P2 — Speckle: реальный обмен трёх программ, но НЕ нативный BIM-writer
**Операция:** получить для QA геометрию/материалы Archicad в Rhino/GH, либо контекстную геометрию Rhino/GH в Archicad без собственного моста; не включать в G3 native ownership.
**Официальные источники:** https://speckle.systems/integrations/archicad/ (поддержка AC27/28/29); https://speckle.systems/integrations/rhino/ (Rhino7/8); https://speckle.systems/integrations/grasshopper/ ; код коннектора https://github.com/specklesystems/speckle-archicad (Apache-2.0). **Точный binary build коннектора для AC29/Rhino8 в данном проходе НЕ зафиксирован**, лицензия исходного кода ≠ гарантия условий SaaS; есть Start for free, конкретные ограничения бесплатного аккаунта не установлены.
**Контракт и направление:** AC → Rhino: **meshes + materials**, слои по этажу/типу, properties как Rhino User Text; AC → GH: meshes/materials/properties для анализа. Rhino → AC: **GDL objects + materials**; GH → AC: **GDL objects + materials**. Передача через publish/load Speckle, не редактирование исходного native Wall/Slab/Roof GUID. Направления двухстороннего обмена данных существуют, но это **НЕ доказанная двусторонняя синхронизация идентичных native BIM-элементов**.
**Предел:** облачный/внешний путь, новые библиотечные GDL-детали, не гарантирует стабильность GUID/hostWall/окна/двери/SEO/связей. Не подключать как второй writer, не считать Speckle «универсальным BIM конвертером».
**№2:** оставить как READ-ONLY/контекстный альтернативный маршрут для G4 и лишь документировать лицензионные/облачные ограничения; без установки, публикации пользовательских моделей или передачи данных в SaaS.

## 3. SOURCE-реестр: ровно 30 конкретных проверок утверждений
Коды: B=BUILD-01 issue192; P=PR74; S=сохранённая схема 1.5.10; M=матрица61; U732/U745/U790/U795=соответствующие upstream PR; R=Tapir release 1.7.2; SP-A/SP-R/SP-G=официальные страницы Speckle Archicad/Rhino/GH; G=Graphisoft AC29 GC.pdf; R2=№2 22Z. **Каждая строка — одно проверенное документарное утверждение, не независимый тест ПО.**

| № | Проверенное утверждение | Основание |
|---:|---|---|
| 01 | BUILD-01 требует нового 2-этажного нативного здания, не повтор PR74 | B |
| 02 | PR74 описывает исторический прототип 21 элемент + Save/Open | P |
| 03 | Для BUILD-01 предусмотрен один существующий SceneWriter/SQLite | B |
| 04 | Pinned Tapir JSON содержит ровно 262 команды | S |
| 05 | Pinned GetGeoLocation имеет версию 1.1.6 | S |
| 06 | Pinned SetGeoLocation имеет версию 1.2.9 | S |
| 07 | В pinned geoReferencingParameters отсутствует xAxisAbscissa | S |
| 08 | В pinned geoReferencingParameters отсутствует xAxisOrdinate | S |
| 09 | В pinned geoReferencingParameters отсутствует scale | S |
| 10 | В pinned surveyPoint отсутствует positionInProject | S |
| 11 | В pinned отсутствуют UpdateHotlinks/ChangeHotlinkNodes | S |
| 12 | В pinned отсутствуют Teamwork lockable/hotlink cache команды из PR795 | S |
| 13 | PR732 merged 02.10.2026; добавляет XAxisAbscissa/XAxisOrdinate/Scale | U732 |
| 14 | XAxisAbscissa и XAxisOrdinate описывают IFC ось X отдельно от north | U732 |
| 15 | GH ProjectLocation/SetProjectLocation расширены портами IFC оси/масштаба | U732 |
| 16 | PR745 merged 03.10.2026; добавляет positionInProject | U745 |
| 17 | positionInProject имеет полный объект x/y/z, SET только при всех трёх | U745 |
| 18 | PR790 merged 12.10.2026; UpdateHotlinks работает по hotlinkNodeId | U790 |
| 19 | ChangeHotlinkNodes принимает hotlinkNodeId и sourceLocation | U790 |
| 20 | UpdateHotlinks/ChangeHotlinkNodes возвращают executionResults по узлам | U790 |
| 21 | Реализация PR790 не обёрнута в undoable command | U790 |
| 22 | PR795 merged 09.10.2026; предоставляет пять Teamwork-команд | U795 |
| 23 | GetLockableObjectSetStatus имеет Free/Editable/Locked/NotAvailable/NotExist | U795 |
| 24 | PR795 upstream live проверен на AC27 Mac BIMcloud, не на нашем AC29 | U795 |
| 25 | Release Tapir 1.7.2 опубликован 19.10.2026, AC29 Win APX существует | R |
| 26 | Speckle официально заявляет поддержку Archicad 29 | SP-A |
| 27 | Speckle официально заявляет поддержку Rhino 8 | SP-R |
| 28 | Speckle AC→Rhino/GH даёт meshes, materials и данные для анализа | SP-A |
| 29 | Speckle Rhino/GH→AC принимает геометрию как GDL objects с материалами | SP-R, SP-G |
| 30 | №2 22Z выявил Auto Hotlink Update при Publisher и условный Sync Changes to GH; здесь не дублируется как новое | R2, G |

## 4. Контрааудит A — «двусторонний обмен» ≠ GUID-preserving triad
1. Speckle может отправлять данные в обе стороны, но native Archicad Wall/Slab/Roof превращаются в meshes, а Rhino/GH принимаются в AC как GDL Objects. Это **геометрическая координация**, не сохранение BIM-класса/hostWall/SEO/исходного GUID.
2. `GetGeoLocation`/GH `ProjectLocation` — обмен параметрами координат, а не событие изменения здания. Даже при совпадении origin, осей и масштаба не гарантированы этаж/материал/проём.
3. Graphisoft AC29 Live Connection допускает условный автоматический `Sync Changes to GH` для Parameter Components (№2 22Z), но GH→AC при Synchronize=TRUE — самостоятельный writer вне SQLite APA; нет доказанной атомарности с SceneWriter. 
4. `UpdateHotlinks` обновляет кэш AC из внешнего файла, не возвращает изменённые в AC элементы в Rhino/GH. Сохранение GUID детей, материалов и отверстий после refresh не подтверждено.
**Вердикт:** P0 auto program/tool choice + end-of-operation 3-way sync + GUID retention = NOT_FOUND/NOT_PROVEN. Никаких новых PASS.

## 5. Контрааудит B — безопасность, версии, внешние изменения
1. Установленное состояние Win11/AC29 build5101/Tapir1.5.10/Rhino8/GH build неизвестно. Pinned schema не доказывает actual APX; Tapir1.7.x нельзя использовать до отдельного разрешения.
2. PR790 Hotlink node modifications **не undoable**; кэш зависит от внешнего файла и его SHA. №2 22Z показал Auto Hotlink Update в Preferences вне PLN: даже «только Publisher» может менять результат; до/после snapshot обязателен.
3. PR795 резервирует объекты BIMcloud Teamwork, **не** делает cross-app lock, не подходит solo PLN как глобальная транзакция. Upstream AC27 Mac LIVE не наш AC29 Win LIVE.
4. Новые geo fields в Tapir1.7.0 отсутствуют в pinned 1.5.10. `SetGeoLocation` — WRITE и запрещён. Сравнение без XAxis/Scale/positionInProject должно быть `INSUFFICIENT_COORDINATE_EVIDENCE`, не выдуманный нулевой сдвиг.
5. Speckle cloud-публикация и создание GDL в Archicad без разрешения запрещены; Apache-2.0 для кода коннектора не доказывает локальную бесплатность сервиса и binary compatibility.
6. G0/G1/G2/G3/G4/G5 нового BUILD-01 не изменились; исходный PROJECT_PLAN rev182 не извлечён; свежий №3 позже 20.10 не подтверждён.
**Вердикт:** SOURCE-only, runtime/identity/concurrency/QA остаются BLOCKED/NOT_RUN.

## 6. Адресное поручение исследователю №2 (не выполнять LIVE)
**№2 / I-2258-01, P0:** подготовить **один** read-only preflight-manifest для BUILD-01 с `projectPath/port/APX_SHA/TapirVersion/ArchicadBuild/RhinoBuild/GHBuild`, `floorId/index`, `units`, `projectOrigin`, `north`, `IfcMapConversion.XAxisAbscissa/XAxisOrdinate/Scale`, `surveyPoint.positionInProject`, `Hotlink nodeId/sourceLocation/source SHA/children GUID`, `Teamwork status`, `GH Sync Changes to GH policy` и `Publisher Hotlink Update Preferences`. Все недоступные поля отметить UNKNOWN, а не подставлять значения. На pinned 1.5.10 поля 1.7.x НЕ запрашивать как установленные.
**№2 / I-2258-02, P0:** составить статическую таблицу маршрутизации «стандартный Wall/Slab/Roof/Window/Door → existing SceneWriter; сложная геометрия → Rhino/GH prepare only; Hotlink refresh → upstream-only/not-installed; Speckle → non-native context/QA only». Для каждой строки: owner, разрешённое направление, тип нативного readback, способ обнаружения конфликта, rollback/STOP. Никакого нового writer/router.
**№2 / I-2258-03, P0:** разработать только документ будущей G4-проверки `pre/post GUID, IFC ID, floor, hostWall, library part, material, BREP, hotlink source fingerprint, preferences` после **отдельно разрешённого** изменения/Save/Reopen; не выполнять.
**Критерий ГОТОВО для №2:** проверяемая таблица полей/источников и список UNKNOWN/неустановленных команд, без false ACCEPTED. Текущий статус поручения: ISSUED_IN_REPORT, NOT_EXECUTED.

## 7. Источники и контроль публикации
- Graphisoft AC29 GH guide: https://help.graphisoft.com/AC/29/INT/GC.pdf ; official AC29 GH download: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ .
- Upstream Tapir MIT / releases / PR #732/#745/#790/#795: ссылки в карточках.
- Speckle official AC/Rhino/GH и Apache-2.0 source repo: ссылки в C5.
- Доказательность: 30 SOURCE assertions; 5 карточек (четыре upstream API + один альтернативный bridge); 2 документарных контрааудита. **Не 30 независимых сайтов, не тесты на Windows, не 30 установок.**
- GitHub-публикация: этот файл создаётся **только** в ветке `research/apa-extension-ranking-hub-20261018`; подтверждение create_file → fetch_file exact equality и commit SHA выдаётся отдельно после фактической проверки. Если запись/чтение не удались: WRITE_BLOCKED.
