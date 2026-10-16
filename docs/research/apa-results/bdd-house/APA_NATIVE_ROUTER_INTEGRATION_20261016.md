# BDD дом — подключение к существующему APA, без второго исполнителя

**Дата:** 2026-10-16. **Состояние:** `SOURCE_BINDING_PREPARED / NOT_LOCAL_RUNTIME_EXECUTED`. Этот проход не меняет PLN и не утверждает создание окон, дверей или кровли.

## Почему прямые скрипты предыдущих проходов не являются APA-интеграцией

Нативная сборка (125 физических BIM-элементов) и исправления пола/ростверка действительно состоялись в Archicad 29 и опубликованы в приватном `safe-bim-bridge/results`. Но использовались автономные Python/Tapir-вызовы, минуя `DynamicCommands`, `BIM Graph`, единый `SceneWriter` и SQLite-журнал ускорителя. Успешная запись в Archicad ≠ прохождение маршрута APA.

Ветка APA, содержащая действующий SceneWriter/маршрутизатор: `feature/apa-native-owner-recovery-20261015` (PR #111), а не устаревший `feature/working-archicad-mvp` с минимальным `archicad_executor.py` и захардкоженным 19723.

Повторно запускать `apa_bdd_house_native_builder.py`, `apa_bdd_house_safe_resume.py`, `apa_bdd_native_kr6_floor_repair.py` или `apa_bdd_native_kr6_grillage_contact_fix.py` **запрещено**: они не являются идемпотентными для этой уже построенной модели.

## Уже существующий маршрут исполнения APA

1. `scripts/archicad_project_accelerator.py`: `native_command_router()`, `prepare_native_task()`, `run_native_task()`.
2. `scripts/archicad_dynamic_commands.py`: текущий динамический каталог Tapir/SDK, `DynamicCommands.prepare_workflow()`, `run_workflow()`, `scope()` и `execute()`.
3. `scripts/archicad_bim_graph.py`: `compile_graph()` и проверка зависимостей/hosted-wall.
4. `scripts/archicad_scene_run.py`: **единственный** существующий SceneWriter, GUID retention, точное соответствие проекта, схема и SQLite `intent-before-write`.
5. `scripts/apa_native_dependency_flow.py`: привязка нативных отношений/материалов к существующему BIM Graph/DependencyImpact.

Никакого нового writer/router, своей очереди, отдельной SQLite-базы или собственных CLI-команд не добавлено.

## Подготовленные входные данные

- `examples/accelerator/bdd-house-20261016-readonly-native-task.json` — **формат `apa-native-task/1`**, единый граф из 13 операций: `GetProjectInfo`, `GetStories`, `GetAllElements` и **по пять** пакетных чтений `GetDetailsOfElements` и `Get3DBoundingBoxes` всех 125 физических GUID. Это исходный граф для `prepare_native_task()`, а не самостоятельно исполняющий Python.
- `docs/research/apa-results/bdd-house/APA_EXISTING_SCENE_WRITER_BASELINE_20261016.json` — реальные исходные 21 GUID, новые 125 физических, 115 авто-сегментов, исходный путь и контрольная сумма оригинала, рабочий путь и окончательная квитанция ростверка.
- Реальный послеисправительный узел: 49 свай Z=-3.000…-0.600, ростверк Z=-0.600…-0.300, лаги Z=-0.300…-0.100. Эта цепь подтверждена индивидуальными native readback и сохранённым PLN.

## Условия реального запуска через APA

**Блокировка среды:** через подключение GitHub невозможно вызвать Windows `archicad_scene_run.py` на реальном локальном адресе `127.0.0.1:19727`, считать текущий saved SHA рабочего PLN либо подтвердить, какой бинарник APA фактически загружен. Старый `sync_bridge` умеет только чтение выделения через mailbox. Нельзя подменять такую связь правом выполнения операций.

- Перед любым `run_native_task()` локально получить живой `GetProjectInfo`, `GetAddOnVersion`, runtime command catalog и свежий хеш сохранённого **рабочего** PLN, отдельно от оригинала.
- `SceneWriter` по умолчанию закреплён за `Тест MER` на 19723 и двумя явными тестовыми копиями; не изменять глобальные константы напрямую ради BDD. В нём уже есть `bind_authorized_saved_copy(port,path,name,saved_sha256,authorization_ref)`; использовать **только** после точной авторизации текущей сохранённой рабочей копии и прохождения всех штатных preflight и native retention checks.
- `DynamicCommands` должен источником своих команд считать реально экспортированный из активного Archicad 29 каталог с source hashes и утверждёнными эффектами; обнаружение каталога/совпадение схем не предоставляют прав записи.
- Перед чтением указанных 125 GUID сверить полный набор 261 GUID, 125 физических, 115 внутренних и 21 исходных. Не считать `ColumnSegment` и `BeamSegment` физическими сваями/балками. При несовпадении остановить без записи.
- Только после read-only `run_native_task()`/graph facts и установления host-wall геометрии превратить подтверждённые по PDF окна/двери в typed шаги `CreateWindows`/`CreateDoors` **существующего** APA. Для каждого необходимы `ownerWallId`, фактический `centerOffset`, `sillHeight`, размеры, ориентация, clearance, source-sheet ID и exact target PLN.
- Отсутствующие lateral offsets и хозяева 23 кандидатов из PDF **не восполнять догадками**. Не писать на основании одного числа проёмов.
- Кровля сейчас `КР - 001` GUID `F0D643A1-B236-4DFC-844A-98424A12B9B7`, фактический zMax +6.128 м; проект +6.295 м. Переход к точной крыше требует определения XY линий ендов/коньков; не менять её поворотом/подъёмом вместо проверки геометрии.

## Правила подтверждения

`SCHEMA_VALID`/`PLAN_VALIDATED_OFFLINE` — не `LIVE_PASS`; `GetAllElements` 261 — не доказательство отсутствия коллизий; `CREATE` без GUID и independent native body readback — не доказательство геометрии. Сохранять `SceneWriter` journal, source/target SHA, affected/retained GUID signatures, result BREP, dependency impact и receipts в существующем `docs/research/apa-results`/private mailbox. Запрещено менять `main` и уже используемые ветки.

**Следующий реальный проход:** только локальный APA runner с read-only graph и точным bound PLN; после успешного выполнения объединить host/block source mapping (КР-10—КР-15) с нативными стенами и подготовить адресные typed CREATE intents через тот же SceneWriter.