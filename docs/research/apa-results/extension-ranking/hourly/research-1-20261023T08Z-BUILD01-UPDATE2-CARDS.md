# APA №1 — BUILD-01 | 2026-10-23 08Z UPDATE2 | 7 карточек готовых механизмов и ограничений

Оценка 0–100 — только экспертная значимость для BUILD-01, не ускорение. `MERGED upstream` ≠ `INSTALLED` ≠ `LIVE`. Новые команды 1.7.3 не предлагать устанавливать на локальную 1.5.10. Без WRITE/LIVE.

## C01 — GetFavoriteSettings — чтение GDL параметров и маркеров
**Gate / экспертная важность:** G2; 99/100.
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1274
**Версия/лицензия:** upstream Tapir 1.7.3, MERGED 2026-10-23 08:06Z; MIT
**Точный контракт:** `GetFavoriteSettings({favorites:["Window - Casement"]}) → favoriteSettings[]` с `elementType`, `folder`, `libPart`, GDL parameters, marker и subelements; non-GDL API_Element defaults не экспортируются.
**Неохваченный BUILD-01 вопрос:** BUILD-01 зависит от точной библиотеки, Favorites и GDL параметров окон/дверей. Один `favoriteName` не гарантирует идентичность параметров.
**Совместимость/ограничение:** В локальном 1.5.10 команда не доказана. Использовать уже существующие ExportFavorites/прочтение атрибутов, не обновлять APX.
**Адресное задание №2 / критерий закрытия:** №2: проверить по установленному catalog/registration наличие read-only альтернативы, фиксировать Favorite+libPart+marker+library provenance до CREATE. PASS только после независимого readback фактических параметров.
**Недублирование:** Дополняет PR74/SceneWriter; не создаёт библиотеку, не дублирует writer.

## C02 — ConvertRevealOffsets — нативное смещение рамы относительно core
**Gate / экспертная важность:** G2/G4; 93/100.
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1270
**Версия/лицензия:** upstream Tapir 1.7.3, MERGED 2026-10-23 08:13Z; MIT
**Точный контракт:** `ConvertRevealOffsets({openings:[{elementId,coreOffset}|{elementId,sideOffset}]}) → revealOffsets[{coreOffset,sideOffset}|error]`; на basic wall равны.
**Неохваченный BUILD-01 вопрос:** На composite wall геометрия оконного откоса относительно core и side не совпадает; расчёт на глаз может дать ошибку глубины.
**Совместимость/ограничение:** Не подтверждено в 1.5.10; команда не определяет внутреннюю геометрию конкретной GDL рамы.
**Адресное задание №2 / критерий закрытия:** №2: в G2 записать систему отсчёта revealDepthOffset; не делать неустановленный ConvertRevealOffsets обязательным; если невозможно проверить, depth = NOT_VERIFIED.
**Недублирование:** Не заменяет CreateWindows/Doors и существующий hostWall GUID.

## C03 — GetOpeningTransformations — глобальная матрица Opening-tool
**Gate / экспертная важность:** G2/G4; 80/100.
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1271
**Версия/лицензия:** upstream Tapir 1.7.3, MERGED 2026-10-23 08:09Z; MIT
**Точный контракт:** `GetOpeningTransformations({elements}) → openingTransformations[]` с `globalToLocal`, `localToGlobal`, `origin`, `xAxis/yAxis/zAxis`, `determinant`, `isMirrored`, error.
**Неохваченный BUILD-01 вопрос:** Для инженерных шахт/проходок нужна точная трансформация Opening, особенно mirrored. Но BUILD-01 первую модель может принять без сложных Opening-tool.
**Совместимость/ограничение:** Отдельный тип Opening, не Window/Door; не установлен в 1.5.10, не BREP.
**Адресное задание №2 / критерий закрытия:** №2: не повышать сложные Opening до P0; для Window/Door продолжить native hostWall. В G4 маркировать Opening-tool как conditional/not-verified.
**Недублирование:** Не дублирует PR82/97 и существующий Window/Door path.

## C04 — GetStructureDisplay — исключить ложные пропажи finish-слоёв
**Gate / экспертная важность:** G4; 96/100.
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1102
**Версия/лицензия:** upstream registered 1.7.2, MERGED 2026-10-23 08:30Z; MIT; AC27+
**Точный контракт:** `GetStructureDisplay() → {structureDisplay,is3D}`; `SetStructureDisplay({structureDisplay})` изменяет view, non-undoable. Официальный AC29: https://help.graphisoft.com/AC/29/INT/_AC29_Help/050_ViewsVB/050_ViewsVB-94.htm
**Неохваченный BUILD-01 вопрос:** В CoreOnly/WithoutFinishes модель на экране может не показывать отделку; нельзя считать скрытые skins отсутствующими в нативной модели.
**Совместимость/ограничение:** Локальный 1.5.10 не подтверждён; исследователю нельзя SetStructureDisplay.
**Адресное задание №2 / критерий закрытия:** №2: до геометрического/визуального readback фиксировать active view и Partial Structure Display; в неизвестном режиме не утверждать геометрический PASS.
**Недублирование:** Это наблюдатель/контроль, не второй geometry engine.

## C05 — Безопасная инвентаризация: GetDetailsOfElements не по всем GUID вслепую
**Gate / экспертная важность:** G4; 98/100.
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/issues/583 ; https://github.com/ENZYME-APD/tapir-archicad-automation/pull/586
**Версия/лицензия:** issue AC29 build3000 Windows/Tapir1.5.8; fix merged 2026-10-02, но untested; MIT
**Точный контракт:** Issue фиксирует crash на 1 GUID Hillside House даже при размере запроса 1; PR586 фильтрует типы для AddFloorPlanPolygonsIfAvailable. Уменьшение batch size не защищает.
**Неохваченный BUILD-01 вопрос:** G4 требует независимый полный readback, но не ценой падения Archicad и потери unsaved проекта.
**Совместимость/ограничение:** Не доказано воспроизведение в AC29 build5101/1.5.10. Closed issue и merged fix не являются installed/live PASS.
**Адресное задание №2 / критерий закрытия:** №2: сначала GetTypesOfElements/типизированная инвентаризация и журнал ошибок per GUID, отдельно квалифицировать GetDetailsOfElements; при подозрительном типе не запускать безусловную декомпозицию.
**Недублирование:** Использует штатные команды, не добавляет renderer/BREP exporter.

## C06 — CreateWindows/Doors: защита floor-plan database и library defaults
**Gate / экспертная важность:** G2; 99/100.
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/issues/532 ; https://github.com/ENZYME-APD/tapir-archicad-automation/pull/559
**Версия/лицензия:** issue AC29 build3000, Tapir1.5.8; fix merged 2026-08-16, MIT
**Точный контракт:** Ошибка `-2130313110` = `APIERR_BADDATABASE`; `ACAPI_Element_CreateExt` требует floor plan database для Main Marker. PR559 переключает current database на FloorPlan и восстанавливает.
**Неохваченный BUILD-01 вопрос:** Правильный `ownerWallId` и размеры не обеспечивают CREATE, если активна 3D database; ошибку нельзя трактовать как неправильный JSON.
**Совместимость/ограничение:** Нельзя переносить исторический crash на локальный build5101; наличие fix в loaded 1.5.10 требует G0.
**Адресное задание №2 / критерий закрытия:** №2: G2 preflight active database, hostWall GUID, library part и story. Не проводить пробное CREATE; требовать подтверждение командной схемы и fail-closed.
**Недублирование:** Сохраняет PR74/SceneWriter, не предлагает новый door/window writer.

## C07 — Save/Open: GuardedSave + dirty-state fail-closed
**Gate / экспертная важность:** G4; 100/100.
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1381 ; https://github.com/ENZYME-APD/tapir-archicad-automation/pull/683
**Версия/лицензия:** issue AC28 build7006 Win/Tapir1.7.2 OPEN; PR683 merged 2026-09-28; MIT
**Точный контракт:** `GetProjectInfo` не выдаёт `hasUnsavedChanges`; `OpenProject` может сбросить unsaved work (наблюдение AC28). PR683 меняет SaveProject database context, но это не гарантия целостности файла.
**Неохваченный BUILD-01 вопрос:** Нельзя выполнить G4 при неизвестном dirty-state или без подтверждённого SHA защищённого исходника.
**Совместимость/ограничение:** Для AC29 build5101 поведение не проверено. Никаких Open/Save исследователем.
**Адресное задание №2 / критерий закрытия:** №2: подготовить GuardedSave: проверка scratch identity/owner approval, закрытие GUI только после разрешения, отсутствие palette scripts, SHA после Save, независимый reopen/readback; unknown dirty-state → STOP.
**Недублирование:** Переиспользовать существующий GuardedSave/SQLite; не писать новую систему сохранения.
