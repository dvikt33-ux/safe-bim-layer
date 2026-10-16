# BDD дом — запуск существующего APA Dynamic Router на рабочем PLN

Дата: 2026-10-16. Статус: `IMPLEMENTED + OFFLINE_PASS / LIVE_NOT_EXECUTED`.

## Входы
- Рабочий Archicad 29.2.1 build 5101, порт `19727`.
- Активная рабочая копия `C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln`.
- Исходный `C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln` — не изменять.
- Исходный сохранённый модельный состав: **261 GUID** = 21 исходный + 125 физических + 115 автоматических сегментов.
- Последний сохранённый ремонт: 18 ростверковых балок, Z −0.600…−0.300 м.

## Только существующий APA
`scripts/apa_bdd_existing_router_readback.py` — **тонкая точка входа**, не нативный исполнитель:
- `archicad_project_accelerator.native_command_router(... include_functional_modules=False)`;
- `prepare_native_task` и `run_native_task`;
- `archicad_bim_graph.compile_graph` внутри существующего `DynamicCommands.prepare_workflow`;
- `archicad_project_accelerator.EvidenceAPI(execute=False)`, журнал фактических API-ответов;
- `archicad_scene_run.bind_authorized_saved_copy` и `guarded_project`, существующая привязка активного PLN;
- существующая схема с source-hash и runtime availability `schemas/tapir-live-1.5.10`.

Никаких вызовов `SceneWriter.execute*`, `Create*`, `Modify*`, `SaveProject`, `OpenProject` в этом режиме нет. SQLite-журнал SceneWriter должен применяться только для последующей санкционированной **записи**, а не для имитации read-only прохода. Исполнитель содержит только reviewed-read GET-команды.

## Одна локальная команда PowerShell

```powershell
$ErrorActionPreference = "Stop"
$dest = Join-Path $env:TEMP ("APA_BDD_ExistingAPA_" + [DateTime]::UtcNow.ToString("yyyyMMdd_HHmmss"))
gh repo clone dvikt33-ux/safe-bim-layer $dest -- --depth 1 --branch feature/apa-bdd-live-router-readback-20261016
if ($LASTEXITCODE -ne 0) { throw "Clone APA failed" }
$py = "$env:APPDATA\uv\tools\archicad-mcp-server\Scripts\python.exe"
& $py (Join-Path $dest "scripts\apa_bdd_existing_router_readback.py") --publish
Write-Host "APA_ROUTER_EXIT_CODE=$LASTEXITCODE"
```

**Без `--apply`**: никакого режима записи в скрипте вообще нет. До запуска не переключать текущий PLN и не закрывать Archicad.

В случае успеха появится `PRIVATE GITHUB APA ROUTER REPORT:`. При блокировке в связи с версией, схемой, проектом, пакетом Python или родительскими GUID скрипт опубликует `PRIVATE GITHUB APA ROUTER FAILURE:`. Эти файлы находятся в приватном `dvikt33-ux/safe-bim-bridge/safe-bim-mailbox/gpt-live/results`.

## После реальной нативной проверки
1. Связать полученную геометрию и host GUID шести нынешних стен с реестром КР-10—КР-15 (23 стеновых блока, проёмы требуют позиционной сверки).
2. Не пытаться размещать окна/двери без измеренного `centerOffset` и правильного `ownerWallId`.
3. Собрать нативный пакет в **этом же** `prepare_native_task/run_native_task` с явными `scopes`, штатным SceneWriter, UUID-журналом до команды и независимым нативным BREP/readback. Для writer потребуется отдельно сверить текущий сохранённый SHA; видимость каталога не есть разрешение на запись.
4. Запрет повторного запуска старых BDD builder/repair скриптов сохраняется.

Офлайн PASS не является live PASS. В этом проходе файл PLN ещё не изменён и новый дом не строился.
