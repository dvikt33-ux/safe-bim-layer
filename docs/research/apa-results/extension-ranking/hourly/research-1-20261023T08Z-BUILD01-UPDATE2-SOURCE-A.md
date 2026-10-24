# APA №1 — BUILD-01 | 2026-10-23 08Z | Дополнение UPDATE2 | SOURCE-A (S01–S15)

Уже существует исходный hourly INDEX 08Z; это отдельное дополнение по источникам, обновившимся позднее. Ни один SOURCE не означает INSTALLED/LIVE/ACCEPTED. Статус G0 BLOCKED, G3 NOT_AUTHORIZED. Каждый пункт — конкретная проверка отдельного PR/issue. Важность в карточках экспертная, не benchmark.

### S01 — G2: Можно ли прочитать параметры Favorite окна без CREATE?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1274
**Версия/лицензия/статус:** Tapir upstream 1.7.3; MIT; MERGED 2026-10-23 08:06Z
**Факт/поля:** GetFavoriteSettings({favorites:[name]}) возвращает GDL параметры, marker, libPart, folder и subelements; не возвращает все non-GDL API_Element settings.
**Решение/ограничение → №2:** SOURCE_ONLY, нет в подтверждённом локальном 1.5.10; не менять APX. №2: использовать уже имеющийся ExportFavorites/локальный каталог и fail-closed для обязательных полей; новую команду не предполагать установленной.

### S02 — G2/G4: Можно ли перевести глубину откоса из core в side для составной стены?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1270
**Версия/лицензия/статус:** Tapir upstream 1.7.3; MIT; MERGED 2026-10-23 08:13Z
**Факт/поля:** ConvertRevealOffsets(openings:[{elementId,coreOffset}|{elementId,sideOffset}]) возвращает оба смещения/ошибку для окон и дверей; ровно одно входное смещение.
**Решение/ограничение → №2:** Не доказано для 1.5.10 и не определяет фактический край GDL рамы. №2: на текущем маршруте проверять revealDepthOffset/host, неизвестный frame plane = NOT_VERIFIED.

### S03 — G2/G4: Есть ли готовое чтение трансформации Opening-tool проёма?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1271
**Версия/лицензия/статус:** Tapir upstream 1.7.3; MIT; MERGED 2026-10-23 08:09Z
**Факт/поля:** GetOpeningTransformations({elements}) возвращает globalToLocal, localToGlobal, origin, axes, determinant, isMirrored; отдельный тип Opening, НЕ Window/Door.
**Решение/ограничение → №2:** Не локальный 1.5.10; не делать Opening обязательным для первого здания. №2: сохранить hostWall окон/дверей и отдельно маркировать unsupported Opening-tool.

### S04 — G4: Может ли отображение CoreOnly скрыть отделку при геометрической приёмке?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1102
**Версия/лицензия/статус:** Tapir upstream, регистрация 1.7.2; MIT; MERGED 2026-10-23 08:30Z
**Факт/поля:** GetStructureDisplay() читает EntireStructure/CoreOnly/WithoutFinishes/StructureOnly и is3D; SetStructureDisplay меняет текущий вид без undo.
**Решение/ограничение → №2:** Установленная 1.5.10 не подтверждена; SET запрещён исследователю. №2: фиксировать фактический view/partial display до BREP сравнения; если неизвестен — NOT_VERIFIED.

### S05 — G2: Можно ли через ElementSet доказать семантическую группу фасадных элементов?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1260
**Версия/лицензия/статус:** Tapir upstream 1.7.3; MIT; MERGED 2026-10-23 08:26Z
**Факт/поля:** GetElementSetsOfElements возвращает только наборы, созданные этим же add-on; CreateElementSets PR #1188 не merged, так что в типичном случае пусто.
**Решение/ограничение → №2:** Не замена BIM Graph/SQLite и не доказательство native group. №2: оставить существующие GUID-связи, не включать новую команду в G2.

### S06 — G2: Можно ли менять GDL скрипты библиотечных деталей как безопасный способ устранить missing parts?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1233
**Версия/лицензия/статус:** Tapir upstream 1.7.3; MIT; MERGED 2026-10-23 08:16Z
**Факт/поля:** SetLibraryPartScripts пишет master/2d/3d/parameter/properties только если GSMObject IsEditable; частичные изменения до ошибки возможны.
**Решение/ограничение → №2:** WRITE и изменение GDL запрещены; это НЕ read-only диагностика и не решение G0. №2: только перечислить исходные библиотеки/Favorites, без скриптовых правок.

### S07 — G2: Почему CreateWindows/Doors может дать -2130313110 при корректном hostWall?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/559
**Версия/лицензия/статус:** Tapir upstream, MERGED 2026-08-16; MIT; код не является локальным runtime proof
**Факт/поля:** PR переключает current database на FloorPlan вокруг ACAPI_Element_CreateExt и восстанавливает его; исправляет APIERR_BADDATABASE при 3D view.
**Решение/ограничение → №2:** Ранее известный маршрут; в 1.5.10 наличие нужно проверять по установленному APX. №2: read-only current database и обязательная host/story preflight, не создавать пробное окно.

### S08 — G4: Безопасно ли массово вызывать GetDetailsOfElements на всех типах?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/586
**Версия/лицензия/статус:** Tapir upstream, MERGED 2026-10-02; MIT; заявлено без DevKit/live проверки
**Факт/поля:** Ограничивает AddFloorPlanPolygonsIfAvailable набором допустимых типов; исходный дефект приводил к crash на конкретном элементе AC29 Hillside House.
**Решение/ограничение → №2:** Нельзя считать исправление установленным в 1.5.10. №2: не использовать безусловный full GetDetailsOfElements sweep; сначала типизированная инвентаризация и read-only квалификация.

### S09 — G4: Почему SaveProject зависит от активного окна?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/683
**Версия/лицензия/статус:** Tapir upstream, MERGED 2026-09-28; MIT; автор отмечал отсутствие локального теста
**Факт/поля:** Сохраняет текущую database, временно переключает на FloorPlan, вызывает ACAPI_ProjectOperation_Save, восстанавливает и возвращает исходный error code.
**Решение/ограничение → №2:** Не подменяет GuardedSave и не доказывает работу локальной 1.5.10. №2: только проектировать safe G4 с явным active database и SHA после сохранения.

### S10 — G2: Можно ли заменить missing library part у уже созданного окна без смены GUID?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1394
**Версия/лицензия/статус:** Tapir upstream 1.7.3; MIT; OPEN на 2026-10-23
**Факт/поля:** ChangeLibraryPartOfElements предлагает name/index/guid, keepParameters/keepSize; поддерживает Window/Door/Object и др.
**Решение/ограничение → №2:** Открытый PR, не локальная функция; это WRITE. №2: до CREATE проверять libPart и Favorite, не полагаться на постфактум замену.

### S11 — G4: Можно ли получить GUID в ошибке GetDetailsOfElements?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1406
**Версия/лицензия/статус:** Tapir upstream 1.7.3; MIT; OPEN
**Факт/поля:** Предлагает добавлять GUID в error.message, документировать output alignment 1:1; без нового обязательного elementId поля.
**Решение/ограничение → №2:** Пока не использовать как установленную гарантию. №2: связывать ошибки с GUID по порядку запроса и сверять количество ответов.

### S12 — G4: Есть ли готовая триангуляция Slab/Roof outline для проверки площади?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1351
**Версия/лицензия/статус:** Tapir upstream 1.7.3; MIT; OPEN
**Факт/поля:** TriangulatePolygonsOfElements использует ACAPI_Polygon_TriangulatePoly для Slab/Zone/Hatch/Mesh/Roof; отдаёт 2D triangles, не 3D BREP.
**Решение/ограничение → №2:** Не принимать за проверку отверстий/объёма; не локальный 1.5.10. №2: существующий readback contour/holes, BREP отдельным доказательством.

### S13 — G2: Готов ли ModifyOpenings для AC29?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1011
**Версия/лицензия/статус:** Tapir upstream; MIT; OPEN, stacked on #918
**Факт/поля:** Предлагает поддержку AC29/30 для ModifyOpenings; зависит от отдельной ветки #918, не standalone merged.
**Решение/ограничение → №2:** Не включать Opening-tool в обязательный BUILD-01. №2: Window/Door hostWall по существующему маршруту; Opening-tool — NOT_SUPPORTED.

### S14 — G2: Это ошибка параметров окна или активной database?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/issues/532
**Версия/лицензия/статус:** Tapir 1.5.8/AC29 build3000; issue CLOSED; upstream MIT
**Факт/поля:** Ошибка -2130313110 идентифицирована как APIERR_BADDATABASE; комментарии подтверждают работу из FloorPlan и отказ из 3D.
**Решение/ограничение → №2:** Не доказывает ошибку build5101; не выдумывать проблему Favorite. №2: зафиксировать active database в G2 и исключить Create из исследовательского прохода.

### S15 — G4: Может ли один элемент привести к crash даже в маленьком запросе?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/issues/583
**Версия/лицензия/статус:** Tapir 1.5.8, AC29 build3000 USA, Win11; CLOSED; MIT
**Факт/поля:** Hillside House element 8AA90DC1-8FFE-9542-92CD-4662EAFC5C20: GetDetailsOfElements 1 элемент завершал Archicad, а батч 3362 без него проходил.
**Решение/ограничение → №2:** Нельзя объявлять ошибкой build5101/1.5.10; batch-size не является защитой. №2: не делать всепроектный sweep без отдельной квалификации read-only маршрута.
