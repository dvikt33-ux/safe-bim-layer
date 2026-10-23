# APA №1 | 2026-10-23 09Z | BUILD-01 | 7 карточек готовых маршрутов

**Шкала 0–100 — экспертная важность, не benchmark.** Все карточки SOURCE_ONLY. Tapir исходники MIT (tag 1.5.9), штатные возможности Graphisoft относятся к установленному Archicad только после локальной проверки; сторонние платные API не используются. Никаких INSTALL/LIVE/ACCEPTED.

## C01 — G0 — идентификация фактически загруженного APX — 100/100

**Конкретный блокер.** G0 — идентификация фактически загруженного APX.

**Первоисточники.** [BUILD-01 #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192), [Microsoft ListDLLs](https://learn.microsoft.com/en-us/sysinternals/downloads/listdlls), [Get-FileHash](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash).

**Версия и доказательство.** Windows11 + AC29 build5101 + заявленная Tapir1.5.10; installed не проверен.

**Готовый контракт.** Read-only PID Archicad → загруженный путь .apx (не просто файл в Add-Ons) → SHA-256 этого пути → JSON server port + active PLN → GetAddOnVersion → фактическая регистрация и JSON schema каждой обязательной команды.

**Ограничения.** Внешняя утилита ListDLLs — опциональна и не устанавливалась; PowerShell Get-Process -Module может требовать доступ. SHA файла не доказывает, что команда реально работает. Команды записи запрещены.

**Подключение без дублирования PR74/SceneWriter — задание №2.** №2 использует существующий read-only preflight; единственный выход RUNTIME_READY либо BLOCKED с конкретным отсутствующим атрибутом. Не менять APX и не выдавать SOURCE за INSTALLED.

**Критерий готовности.** PID, port, PLN path, loaded APX path, SHA-256, GetAddOnVersion, required-command availability, schema snapshots — единая непротиворечивая квитанция.

## C02 — G1 — безопасная привязка двух этажей — 98/100

**Конкретный блокер.** G1 — безопасная привязка двух этажей.

**Первоисточники.** [Issue #573](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/573), [PR #571](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/571), [PR #423](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/423).

**Версия и доказательство.** #573 AC28 GER Win; PR423 AC28 live; PR571 merged untested; локальная 1.5.10 не проверена.

**Готовый контракт.** Готовые GetStories + существующий storyBindings/typed DAG из PR74. Сравнить index, elevation, высоты и ожидаемую структуру здания без SetStories. Исторический SetStories мог сдвигать уровни даже при success.

**Ограничения.** Двухпроходный workaround SetStories описан в issue, но WRITE этажей в этой роли запрещён; риск удаления существующих элементов. Не переносить баг AC28 автоматически на AC29.

**Подключение без дублирования PR74/SceneWriter — задание №2.** №2: только чтение GetStories, затем офлайн typed DAG на двух уже существующих этажах. Если нужных этажей нет — BLOCKED, отдельный исполнитель готовит scratch PLN после санкции.

**Критерий готовности.** Два корректных floorIndex, отметки и высоты в спецификации; никакой story mutation; план hash; G1 PASS только после реального offline/preflight исполнения.

## C03 — G2 — Hosted Window/Door: защита от призрачного GUID — 99/100

**Конкретный блокер.** G2 — Hosted Window/Door: защита от призрачного GUID.

**Первоисточники.** [Issue #481](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/481), [#399](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/399), [#453](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/453), [#371](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/371).

**Версия и доказательство.** AC29 5003 CHE Mac Tapir1.5.5; AC29 4006 JPN Win Tapir1.4.0; AC29 5003 GER Mac Tapir1.5.3. Не доказано для Win build5101..

**Готовый контракт.** Существующие CreateWindows/CreateDoors + GetElementsByType(Window/Door) + GetDetailsOfElements(host wall) + GetConnectedElements по каждому типу отдельно. Сверить returned GUID, существование элемента, hostWall GUID, width/height/sillHeight, фактический opening.

**Ограничения.** Issue #481 сообщает успешный GUID при нулевом фактическом создании; #399 — BADPARS даже с Favorite. Не заменять hosted Window/Door generic Opening; не считать polygon wall поддержанным.

**Подключение без дублирования PR74/SceneWriter — задание №2.** №2: preflight строго прямых стен-хостов и библиотечных Favorites; после отдельного G3 допуска выполнить независимый readback, при несоответствии STOP без повторного CREATE.

**Критерий готовности.** GUID exists + elementType Window/Door + hostWall + геометрия и инвентаризация совпадают; только тогда LIVE_CREATED_UNSAVED, не ACCEPTED.

## C04 — G2 — Slab: материал, отверстия, размерность батча — 99/100

**Конкретный блокер.** G2 — Slab: материал, отверстия, размерность батча.

**Первоисточники.** [Issue #604](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/604), [#439](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/439), [PR #785](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785), [№2 09Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T09Z-report.md).

**Версия и доказательство.** #604 AC28 Win Tapir1.5.8; #439 AC28 Mac Tapir1.5.3; PR785 2026-10-11 upstream untested; pinned catalog 1.5.10 = без CreateSlabs.structureType/material/composite..

**Готовый контракт.** Существующий SceneWriter CreateSlabs → GUID → независимый readback → отдельная санкционированная ModifySlabs → readback. holes только [{polygonCoordinates:[...]}]; polygonOutline без holes может удалить отверстия; Composite useWith=Slab проверять.

**Ограничения.** Готовый direct CREATE из PR785 не является локальным контрактом. Отчёт №2 09Z: verified PR149 Slab floorIndex==0 нельзя использовать для второго этажа. Mixed complex slab batches имели crash на AC28.

**Подключение без дублирования PR74/SceneWriter — задание №2.** №2: сверить installed schema, отдельные WRITE scopes для обеих мутаций; при сложных контурах — одиночные будущие CREATE, no retry on UNKNOWN. Строгий preflight polygon.

**Критерий готовности.** Slab на обоих floorIndex; native structure/material/composite и толщина подтверждены независимым readback, отверстия и контур сохранены.

## C05 — G2/G4 — Roof: проверка фактической геометрии — 96/100

**Конкретный блокер.** G2/G4 — Roof: проверка фактической геометрии.

**Первоисточники.** [Issue #604](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/604), [#569](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/569), [Graphisoft SDK29 Opening](https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_element_1_1_opening.html).

**Версия и доказательство.** #604 AC28 Win; #569 AC27; SDK29 Opening-tool — другой элемент; локальная Roof schema Tapir1.5.10 неизвестна.

**Готовый контракт.** Готовые CreateRoofs и read-only геометрические команды проверяются на точной локальной схеме; сравнить pivotLine, slope, levels, толщину и границы, а также сопряжение Wall/Roof. AABB не равно BREP.

**Ограничения.** #604 сообщает игнорирование Roof thickness в одной версии; #569 отсутствие RoofDetails. Generic Opening не замещает hosted Window/Door. Нельзя считать ROI/SEO соединение доказанным без нативного readback.

**Подключение без дублирования PR74/SceneWriter — задание №2.** №2: выбрать поддерживаемый roof subtype для первого здания, сформировать ожидаемые геометрические инварианты; не подключать новый Roof writer.

**Критерий готовности.** После будущего разрешённого CREATE реальные roof elements, slopes, roof-wall connections и geometry/brep readback согласуются со спецификацией.

## C06 — G2 — библиотечные источники и Favorites без пробной записи — 97/100

**Конкретный блокер.** G2 — библиотечные источники и Favorites без пробной записи.

**Первоисточники.** [Graphisoft AC29 Library Manager](https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-43.htm), [#1217](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1217), [#1218](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1218), [#1223](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1223), [#812](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/812).

**Версия и доказательство.** AC29 штатный Library Manager; #1217/#1218/#1223 OPEN requests; #812 AC29 AUT Win Tapir1.7.0.

**Готовый контракт.** Штатный Library Manager показывает missing/duplicate parts; существующие GetAvailableLibraryParts и GetFavoritesByType — read-only каталог. Зафиксировать libraryPartName, GUID/происхождение, missing warnings, конкретный Favorite.

**Ограничения.** Новые GetLibrariesOfLibParts/GetMissingLibPartNames/GetLibPartParameters пока предложения, не команды 1.5.10. GDL 2D arrays нельзя писать как flat list. Upstream GetFavoriteSettings 1.7.3 уже найден в 08Z, здесь не считается новым решением.

**Подключение без дублирования PR74/SceneWriter — задание №2.** №2: до CREATE проверить нужные Window/Door library parts и Favorites в активном scratch, не менять библиотеки и GDL scripts.

**Критерий готовности.** Нет неопределённых библиотечных зависимостей для обязательных дверей/окон; источники и имена зафиксированы, статус только READ_ONLY_READY.

## C07 — G4 — защищённый Save/Open и независимая инвентаризация — 100/100

**Конкретный блокер.** G4 — защищённый Save/Open и независимая инвентаризация.

**Первоисточники.** [Issue #681](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/681), [PR #683](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/683), [#686](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/686), [PR #694](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/694), [#665](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/665).

**Версия и доказательство.** SaveProject issue AC29 build3000 CZE Win Tapir1.5.9; Slab bbox issue AC28 mac; PR683/694 merged но untested; локальная 1.5.10 неизвестна..

**Готовый контракт.** Существующий GuardedSave только после санкции на scratch, проверить active FloorPlan; SHA защищённых исходников, файл на диске, GUI close, reopen, all-database inventory с per-database errors, GUID/type/floor/host/material/segment и BREP.

**Ограничения.** API Save success и AABB не достаточны. ColumnSegment property values могут отсутствовать; BeamSegment final GUID diff условный blocker из №2 08Z/09Z. Не делать массовый unsafe GetDetails до проверки.

**Подключение без дублирования PR74/SceneWriter — задание №2.** №2: добавить критерии к существующей приёмке без нового writer/router; любые UNKNOWN => STOP+read-only reconciliation, не повтор CREATE.

**Критерий готовности.** Сохранённая новая копия PLN, фактическое закрытие и повторное открытие, независимые native receipts + геометрия + все дочерние GUID; только затем G4 PASS.
