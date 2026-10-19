# Постоянный APA: принятый массовый selector подключён и проверен

19.10.2026, задача APA-P70.A11.S13, продолжение native-приёмки #179.

**INSTALLED_MASS_SELECTOR_READBACK_VERIFIED**. Обновление реально применено к
`C:\LocalAI\APA_AC29_Stable`, после отдельного stage и проверки на настоящем AC29.
Исполненный исходный commit: `650b076963c4660fa903362588037c14aad1418e`.

## Что работает

Один существующий DynamicCommands Router получает установленную цепочку
V1(6) → V2(12) → B1(3) → B2(3) → C1(3) → B3(3), существующие четыре semantic
команды и два source-контракта чтения/клонирования групп. Новый Router, transport,
dispatcher, SceneWriter или фоновый процесс не создавался.

Фактический каталог: B3-цепочка **292**, с semantic **296**, с двумя групповыми
контрактами **298**. Сохранены **все 296 исходных contract hashes**, в том числе
30/30 файловых и 4/4 semantic. Это количество контрактов; оно не означает
регистрацию всех этих команд в текущем Archicad.

Существующий `prepare_auto_optimized_native_task` распознаёт типизированный
`apa-native-mass-request/1` и направляет его в принятый group-first selector.
Прежнее поведение V1/V2 discovery сохранено как fallback. Native-выполнение
проходит через прежние `run_auto_optimized_native_task`, Router, scope,
SceneWriter и SQLite; новый групповой verifier добавлен в прежний registry.

## Фактическая проверка установленного кода

- Точный проект-копия #179, 172 GUID, saved SHA256
  `b6b44dc1a811ec4e77864177f3cef57e701e1f63126c16bc64b6a5d82a89c478`.
- Исходная группа `40d5303f-18ca-4117-9de0-e06bfd8e64b9`, оба её native member GUID
  и типизированные/геометрические факты повторно прочитаны.
- Свежая SDK identity равна принятой сборке AC29; выбранная Clone-команда
  проверена через native `IsAddOnCommandAvailable` именно этого экземпляра.
- **LINEAR**, **GRID**, **AXIS_INTERSECTIONS**: текущие факты → selector → один
  существующий native Clone в исходном BIM Graph; проверка размещений по BREP
  всех 172 элементов прошла. Координаты явно заданы в тестовом контракте.
- 33 native read-вызова, **0 native model writes**, **0 Save**, новый SQLite
  не создан, сохранённая копия и исходный PLN неизменны.
- Native-запись 32 групп и её реальный save/reopen приняты отдельно в #179.
  Здесь эта операция не повторялась. Read-only план LINEAR/AXIS не объявляется
  LIVE-приёмкой записи этих вариантов.

## Сохранность установки

Изменены только тела `prepare_auto_optimized_native_task` и `installed_verifiers`.
Добавлены guarded runtime wrapper и один code-owned READS reader состава групп.
Прочие байты обоих прежних файлов сохранены. Остальные **152 существующих
кодовых/конфигурационных файла** совпадают с предварительными SHA.

Восемь небольших Python-модулей и один точный JSON-контракт добавлены отдельно.
DynamicCommands, исходный SceneWriter, sidecar adapters, их квитанции и три
существующих vendor-окружения сохранены. Проверены прежние pyvenv.cfg/python.exe.
IfcOpenShell, PyMuPDF, ezdxf и прочие зависимости не устанавливались повторно.
APX, рабочие пользовательские PLN и main не менялись; merge не выполнялся.

До замены созданы локальные побайтовые резервные копии и SHA-квитанция в
`runtime-code-backups/mass-selector-*`. Installer проверяет ожидаемые старые
байты, проводит smoke/readback и при неуспехе восстанавливает только свои
изменения с проверкой SHA. Исходники пользовательского checkout не затронуты.

SHA256 установленного core после обновления:
`30793c9538feacd11e86c6e6d688869f0506afb6e0ec19f74d50cdc143a26e03`.

## Проверки

- Windows Python 3.11: 130/130 целевых офлайн тестов PASS, включая 9 тестов
  установки, rollback, сохранности контракта и точной runtime identity.
- GitHub Actions на точном `650b0769...`: все 8 опубликованных checks SUCCESS,
  включая Windows Python 3.11/3.12 mass request, Windows/Linux scope integration
  и полный существующий Windows schema-contract suite. Ссылки в ci-checks.json.
- Родительский #179: все 13 checks SUCCESS на `f5f1ad15...`. Закрыты Windows
  short-path comparison и устаревшее фиксированное число команд в старом тесте;
  теперь сравнивается весь объявленный набор команд.

## Использование

Для общего каталога новых сессий используется существующая factory-цепочка через
`scripts/apa_ac29_installed_factory.py`. Запуск без аргументов выводит inventory;
`--task-json` принимает явный массовый запрос и готовит план без native-записи.
Программный вход: `apa_ac29_installed_factory.native_command_router()`;
планирование/исполнение остаются в существующем `archicad_project_accelerator`.

Запросу нужны проверенные native source GUID/семейство/этаж, состав группы и
явные размещения в метрах. Свободный текст не задаёт размеры, материалы,
разрешение на запись или runtime availability.

## Остаток приоритета 1

Принят clone существующей группы из двух полных Column на этаже 0. Другие
составы групп, отдельная новая группировка, булево объединение и создание
самих native осей/сеток требуют своих native контрактов и верификаторов.
Ungrouped MoveElements(copy=true) подготовляется прежним selector, но его
пакетное подключение к общему registry требует отдельного завершения;
подготовленный preview не выдаётся за LIVE-выполнение.

## Квитанции

deployment.json — точные before/after SHA и сохранность окружений;
original-296-contracts.json — весь прежний каталог;
stage-smoke.json — проверенный stage;
native-readonly-qualification.json — фактические три маршрута на текущем AC29;
native-readonly-call-audit.json — раздельный счётчик 33 native reads/0 writes;
local-tests.json и ci-checks.json — отдельные офлайн/CI результаты.
