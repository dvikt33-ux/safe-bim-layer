## V2: исправлена проверка активной исходной копии

Первый старт V2 успешно выполнил проверку `GROUP_CLONE_SOURCE_OWNED_NATIVE_BREP_AND_LAYOUT_PASS` и подтвердил прошлую независимую сверку `44 GUID, 0 prior writes`, но остановился с `PROJECT_SWITCH_DETECTED`, поскольку прежний `verify_previous()` требовал активный `group-ac29-assembly-20261018-04.pln`, тогда как после сверки был открыт `group-ac29-scene-writer-20261018-01.pln`.

**Это исключение возникло до `STATE.mkdir()`, до создания V2-файла, до открытия другого PLN и до любой нативной записи**. Исправлен узкий вход: `V2` теперь передаёт исходному обработчику только точно заданную, независимо сверенную копию `...-01.pln`. Проверяются побайтовое совпадение с сохранённым `...-04.pln`, SHA исходного функционального проекта и текущее активное имя PLN. Произвольный путь не допускается; обычный вход V1 неизменен. Адресный тест проверяет действительную допустимую копию, запрещённый путь и несовпадающие байты.

После установки исправления допускается запуск `apa_ac29_group_scenewriter_v2.py --execute` **только если** каталога V2 `...scene-writer-20261018-02` и `...-02.pln` нет: сам V2 блокирует любое повторное использование занятого состояния. Это не повтор уже выполненной нативной операции: первый старт V2 не дошёл даже до создания попытки. Старую попытку #01 не запускать и не очищать журналы.

## Новый однократный запуск V2 после завершённой независимой сверки

**Не запускать старый** `apa_ac29_group_scenewriter_live.py`. Сценарий #01 намеренно остаётся в состоянии STOPPED, сохранённые квитанции и SQLite не изменяются.

Точно подтверждённая квитанция #01: `WRITER_PRE_DISPATCH_STOP_AND_LIVE_NATIVE_BASELINE_PASS`, 44 GUID, 0 команд нативной записи, 0 строк сцен/шагов SQLite, BREP и исходная группа неизменны.

Новый `scripts/apa_ac29_group_scenewriter_v2.py` перед любыми изменениями:
- сравнивает локальную квитанцию #01 с опубликованной квитанцией GitHub;
- проверяет активную старую копию PLN на порту 19724, исходные SHA, полный состав GUID, дочерние сегменты и BREP, повторно проверяет существующую нативную группу;
- запускает **полный нативный геометрический и коллизионный префлайт только на чтение** и выбирает настоящую команду через основной APA с каталогом Tapir **1.5.10**;
- отказывает в исполнении, если новая копия или её рабочий каталог уже существуют.

**Только после префлайта** создаёт другую одноразовую копию `C:\LocalAI\APA_Group_Acceptance\group-ac29-scene-writer-20261018-02.pln`, новый SQLite-журнал `C:\LocalAI\APA_AC29_Group_SceneWriter_State\scene-writer-20261018-02\original-scenewriter.sqlite` и новую сцену `GroupCloneWriter29_20261018_02`. Исходный `SceneWriter` выполняет ровно один `CloneNativeGroupV1`, затем независимый readback. `SaveProject` не выполняется. Повторы запрещены.

Одноразовая команда на Windows (при отсутствии несохранённых пользовательских изменений во втором Archicad):

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $src = 'C:\LocalAI\APA_AC29_Build_Source'
    git -C $src pull --ff-only
    if ($LASTEXITCODE -ne 0) { throw 'APA не обновился' }
    python "$src\scripts\apa_ac29_group_scenewriter_v2.py" --execute
    if ($LASTEXITCODE -ne 0) {
        throw 'V2 остановлен: запрещено запускать повторно'
    }
}
```

Публикуемый отчёт: `safe-bim-bridge` → `safe-bim-mailbox/apa-ac29-group-acceptance/results/group-scenewriter-native-clone-20261018-02.json`. Результат **пока не подтверждён LIVE**. После выполнения не сохранять и не закрывать Archicad, сначала проверить GitHub-квитанцию.

## Остановка первого запуска и безопасная сверка

Первый запуск остановился с ValueError: DYNAMIC_PROVIDER_VERSION_DRIFT. В коде использовался каталог Tapir 1.5.8, а локально установлен 1.5.10. Ранее выданная квитанция пометила состояние как потенциально изменённое, поскольку флаг намерения выставляется до попытки записи. По порядку выполнения SceneWriter это исключение возникает в проверке before() до вызова нативной операции, но требуется независимая проверка локального следа и модели.

Исправлен источник каталога: исходный код теперь вызывает APA.catalog_with_provenance() для уже проверенного экспорта schemas/tapir-live-1.5.10/tapir-scene-live.json. Это проверка хэшей исходных JS и воспроизводимости схемы; она не является доказательством того, что активный PLN соответствует исходному экспорту документации. Проект защищён отдельным guarded_binding() и SHA.

Исходный сценарий с тем же именем scene-writer-20261018-01 и его SQLite-журнал НИКОГДА НЕ ПОВТОРЯТЬ. Новая подготовка без записи:

```powershell
$src = 'C:\LocalAI\APA_AC29_Build_Source'
git -C $src pull --ff-only
if ($LASTEXITCODE -ne 0) { throw 'Не удалось обновить APA' }
python "$src\scripts\apa_ac29_group_scenewriter_reconcile_readonly.py"
```

Нельзя закрывать или переключать Archicad 29 на 19724: сценарий только читает активную первую копию group-ac29-scene-writer-20261018-01.pln. Он требует точной исходной квитанции остановки, пустого журнала сцен и шагов, полного журнала вызовов без отправки любой команды записи, 44 GUID, совпадения физических BREP/атрибутов/связей с записанным до попытки снапшотом, членства исходной группы и хэшей исходных PLN.

Ожидаемое подтверждение при полной проверке: WRITER_PRE_DISPATCH_STOP_AND_LIVE_NATIVE_BASELINE_PASS; отдельный отчёт публикуется в safe-bim-bridge по пути safe-bim-mailbox/apa-ac29-group-acceptance/results/group-scenewriter-native-clone-20261018-01-readonly-reconciliation.json. Если любой факт не подтверждён, тест остановится и не инициирует восстановление/повтор.

Только после публикации этой квитанции можно планировать ИНОЕ, отдельно одобренное одноразовое испытание на новой копии PLN с новым ID сцены и SQLite-журналом. Само исправление исходного каталога не разрешает повтор записи.

# APA AC29 — сквозной тест нативной группы через SceneWriter

Исполняемая цепочка: source-qualified native group → APA automatic group selector → DynamicCommands → существующий BIM Graph → штатный build_existing_workflow_scopes → SceneWriter SQLite → code-owned native BREP readback.

## Границы

- Порт 19724 и только Archicad 29.
- Исходная сохранённая тестовая копия: C:\LocalAI\APA_Group_Acceptance\group-ac29-assembly-20261018-04.pln (44 GUID).
- Отдельная целевая копия: C:\LocalAI\APA_Group_Acceptance\group-ac29-scene-writer-20261018-01.pln. Существующий файл не перезаписывать.
- Команда: одна AddOn.TapirCommand.CloneNativeGroupV1, смещения dx=25 м и dx=50 м, две группы по две стойки.
- BDD/19723, исходный APA_Functional_Test_House_01.pln, main и Archicad 30 не изменяются.
- SaveProject НЕ вызывается: копия в Archicad после теста остаётся с несохранённой нативной группировкой, чтобы проверить именно маршрутизацию записи. Сохранение — отдельная операция и отдельный допуск.

## Проверяемые факты

- Исходные 44 GUID, два родительских Column и их ColumnSegment, исходное членство в нативной группе, этаж, исходные BREP, атрибуты.
- Два новых размещения не пересекаются с существующей 3D-моделью, все зависимости подтверждены.
- Все 44 исходных GUID и BREP сохранены; новые две группы содержат 4 Column и 4 ColumnSegment с точной геометрией и атрибутами.
- SQL-журнал и долговременное намерение создаются до вызова записи. Запрещён автоматический повтор даже при ошибке после отправки.
- Статус подтверждения: LIVE_SCENEWRITER_NATIVE_GROUP_CLONE_PASS только после WORKFLOW_CALLABLE_VERIFIED и независимого readback.

## Один запуск

Перед запуском убедиться, что во втором Archicad нет несохранённых пользовательских правок: он переключится на новую тестовую копию.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $src = 'C:\LocalAI\APA_AC29_Build_Source'
    $branch = 'feature/apa-ac29-group-scenewriter-live-20261018'
    $changes = git -C $src status --porcelain
    if ($LASTEXITCODE -ne 0 -or $changes) { throw 'В локальном APA есть изменения.' }
    git -C $src fetch origin $branch
    if ($LASTEXITCODE -ne 0) { throw 'Не удалось загрузить ветку.' }
    git -C $src show-ref --verify --quiet "refs/heads/$branch"
    if ($LASTEXITCODE -eq 0) { git -C $src switch $branch }
    else { git -C $src switch --track "origin/$branch" }
    if ($LASTEXITCODE -ne 0) { throw 'Не удалось переключить ветку.' }
    git -C $src pull --ff-only
    if ($LASTEXITCODE -ne 0) { throw 'Не удалось обновить код.' }
    python "$src\scripts\apa_ac29_group_scenewriter_live.py" --execute
}
```

Если скрипт остановился или возвратил ошибку, не повторять. Публикация результата идёт в dvikt33-ux/safe-bim-bridge, ветка feature/apa-ac29-apx-build-mailbox-20261018, путь safe-bim-mailbox/apa-ac29-group-acceptance/results/group-scenewriter-native-clone-20261018-01.json.

Это исходный код и готовая инструкция, НЕ подтверждённый LIVE результат до отдельной квитанции.
