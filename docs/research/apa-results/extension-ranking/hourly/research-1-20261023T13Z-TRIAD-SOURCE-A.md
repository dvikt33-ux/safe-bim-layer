# APA №1 | 2026-10-23 13Z | TRIAD | 30 новых SOURCE-вопросов

Новые относительно отчёта 12Z вопросы: мультиплоскостная кровля, hosted Door/Window, GDL-параметры, Teamwork/GUID/SEO, Speckle Next-Gen, Tapir GH plugin, Rhino solver/Player. Это **30 конкретных проверок контрактов**, а не 30 независимых сайтов. Исторические Teamwork-утверждения 2017/2021 не переносятся автоматически на AC29. SOURCE не равно INSTALLED/LIVE/ACCEPTED. Лицензии: AC29/Rhino8 — базовые лицензии; Tapir upstream MIT; Speckle Free ограничен условиями текущего тарифа; никаких установок/платных API.

## S01 — AC29 Deconstruct Roof: можно ли читать многоскатную крышу?
**Факт / поля / направление:** Graphisoft AC29 GH Live Connection guide, Deconstruct Roof: только Single-Plane Roof; Multi-Plane не обрабатывается.
**Первоисточник, версия, лицензия, статус:** https://help.graphisoft.com/AC/29/INT/GC.pdf; лицензия AC/Rhino отдельно; ограничение SOURCE_AC29, не runtime.
**Ограничение и адресное задание №2:** №2: исключить Multi-Plane Roof из гарантированного AC→GH Deconstruct; предложить отдельный независимый readback через существующий APA.

## S02 — AC29 Roof: можно ли обратно прочитать односкатную крышу?
**Факт / поля / направление:** Тот же guide разрешает Deconstruct Roof для Single-Plane Roof; геометрия+Settings, но не запись в тот же GUID.
**Первоисточник, версия, лицензия, статус:** https://help.graphisoft.com/AC/29/INT/GC.pdf; SOURCE_AC29, INSTALLED_UNKNOWN.
**Ограничение и адресное задание №2:** №2: добавить read-only single-plane roof reference/Settings/ID сценарий и сопоставить с native roof.

## S03 — После ручного редактирования AC изменение само отправится в GH?
**Факт / поля / направление:** AC29 guide прямо требует нажать Send Changes на палитре Archicad, чтобы обновить GH definition.
**Первоисточник, версия, лицензия, статус:** https://help.graphisoft.com/AC/29/INT/GC.pdf; SOURCE_AC29, auto-event NOT_PROVEN.
**Ограничение и адресное задание №2:** №2: описать явный Send Changes checkpoint; не обещать бесконтактную обратную синхронизацию.

## S04 — Можно ли подключить вручную созданную стену к GH?
**Факт / поля / направление:** Deconstruct применим и к вручную размещённым AC-элементам; Set one Element/Set Multiple Elements в контекстном меню.
**Первоисточник, версия, лицензия, статус:** https://help.graphisoft.com/AC/29/INT/GC.pdf; SOURCE_AC29, read/reference, не write-back.
**Ограничение и адресное задание №2:** №2: план read-only reference Wall→Deconstruct, сравнить исходный GUID с выходом GH.

## S05 — У Deconstruct есть независимый Synchronize gate?
**Факт / поля / направление:** В AC29 guide параметр Synchronize отсутствует у Deconstruct, хотя есть у Design/Document generators.
**Первоисточник, версия, лицензия, статус:** https://help.graphisoft.com/AC/29/INT/GC.pdf; SOURCE_AC29, нельзя считать обратный read транзакционной записью.
**Ограничение и адресное задание №2:** №2: разграничить GH reference refresh и разрешение на генераторный write.

## S06 — Можно ли переиспользовать настройки AC элемента?
**Факт / поля / направление:** Settings output Deconstruct подключается к Extract Settings; это извлечение настроек, не мутация исходного элемента.
**Первоисточник, версия, лицензия, статус:** https://help.graphisoft.com/AC/29/INT/GC.pdf; SOURCE_AC29, без гарантий сохранения GUID.
**Ограничение и адресное задание №2:** №2: читать Settings, сравнить материал/структуру и фиксировать GUID при последующем отдельном создании.

## S07 — GH Door/Window без Wall host?
**Факт / поля / направление:** AC29 guide: Door/Window могут находиться только в существующей Wall; GH компоненты требуют Wall-type input.
**Первоисточник, версия, лицензия, статус:** https://help.graphisoft.com/AC/29/INT/GC.pdf; SOURCE_AC29; host является обязательной зависимостью.
**Ограничение и адресное задание №2:** №2: построить DAG Wall→Window/Door, проверить Wall ID/host readback до разрешения генерации.

## S08 — Где располагается окно по горизонтали?
**Факт / поля / направление:** Horizontal Distance задаёт расстояние точки вставки от конца reference line стены вдоль линии.
**Первоисточник, версия, лицензия, статус:** https://help.graphisoft.com/AC/29/INT/GC.pdf; SOURCE_AC29, знак/ориентация требуют геометрической проверки.
**Ограничение и адресное задание №2:** №2: для каждого проёма сохранять reference wall endpoint и проверить centerOffset после readback.

## S09 — Есть ли готовая альтернативная привязка окна по точке?
**Факт / поля / направление:** Door/Window Point проецирует точку перпендикулярно на reference line Wall.
**Первоисточник, версия, лицензия, статус:** https://help.graphisoft.com/AC/29/INT/GC.pdf; SOURCE_AC29, projection может отличаться от произвольной Rhino точки.
**Ограничение и адресное задание №2:** №2: сравнить Point и Distance placement на одной проверенной Wall; вне LIVE — только схема.

## S10 — Можно ли произвольно управлять внутренними параметрами GDL библиотечной детали без кода?
**Факт / поля / направление:** AC29 guide: чтобы GH получил доступ к internal parameters Library Part, нужно изменить её program code.
**Первоисточник, версия, лицензия, статус:** https://help.graphisoft.com/AC/29/INT/GC.pdf; SOURCE_AC29; пользователь запретил писать код, значит путь не годится как универсальное no-code решение.
**Ограничение и адресное задание №2:** №2: ограничить библиотечные параметры штатными exposed settings/Favorites; отметить NOT_SUPPORTED без правки GDL.

## S11 — Есть ли выбор существующей библиотечной детали?
**Факт / поля / направление:** Object Settings допускает Use existing Library Part / Select Archicad Library Part; Window/Door Settings выбирают Library Part.
**Первоисточник, версия, лицензия, статус:** https://help.graphisoft.com/AC/29/INT/GC.pdf; SOURCE_AC29, имя детали ≠ GUID/Favorite.
**Ограничение и адресное задание №2:** №2: сверить actual GDL library part identity, а не только width/height.

## S12 — Кто владеет созданным GH элементом в Teamwork?
**Факт / поля / направление:** Graphisoft Teamwork note: GH-created элементы locked и reserved создавшим пользователем.
**Первоисточник, версия, лицензия, статус:** https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680; историческая статья 2017/ред.2021, НЕ подтверждена AC29 build5101.
**Ограничение и адресное задание №2:** №2: если Teamwork используется, сначала read-only reservation inventory; scratch solo предпочтительнее.

## S13 — Нужна ли reservation даже создателю GH элемента?
**Факт / поля / направление:** Graphisoft Teamwork note: изменение требует reservation даже при lock тем же создателем.
**Первоисточник, версия, лицензия, статус:** https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680; историческая SOURCE, runtime AC29 не проверен.
**Ограничение и адресное задание №2:** №2: добавить owner/reservation в preflight для Teamwork, иначе STOP.

## S14 — Что если GH элемент reserved другим пользователем?
**Факт / поля / направление:** Graphisoft Teamwork note: регенерация/модификация может создать дубликат.
**Первоисточник, версия, лицензия, статус:** https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680; историческая SOURCE, не гарантированная современная ошибка.
**Ограничение и адресное задание №2:** №2: при чужом reservation запретить повтор генерации; read-only duplicate check по source definition/геометрии.

## S15 — Что если элемент доступен, но не зарезервирован исполнителем?
**Факт / поля / направление:** Graphisoft Teamwork note: GH update может не изменить элемент и не создать дубликат.
**Первоисточник, версия, лицензия, статус:** https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680; историческая SOURCE, не подтверждение AC29.
**Ограничение и адресное задание №2:** №2: запретить трактовать успешный GH расчет как native write; обязательный GUID/property readback.
