# ArchiCAD Project Accelerator R03.1

## Запуск в Windows

Откройте PowerShell в распакованном каталоге APA или в корне интеграционной ветки. Для локальных функций достаточно 64-разрядного Python 3.11. Сборка испытана на 3.11.9.

```powershell
py -3.11 -m venv .venv-apa
$Apa = ".\.venv-apa\Scripts\python.exe"
& $Apa -m pip install -r requirements-apa.lock
& $Apa -m pip check
& $Apa -X utf8 -m apa doctor
& $Apa -X utf8 -m apa --help
```

Если `py -3.11` не находит интерпретатор, укажите полный путь к установленному `python.exe` в первой команде. `doctor` сверяет версии с `requirements-apa.lock` и показывает состояние окружения для локальных операций.

## Основные команды

```powershell
& $Apa -X utf8 -m apa catalog IFCGeometry --contracts
& $Apa -X utf8 -m apa template-check
& $Apa -X utf8 -m apa plan --intent examples/accelerator/building-shell.intent.json --output shell-plan.json
& $Apa -X utf8 -m apa exchange "C:\Models\example.ifc" --output ifc-report
& $Apa -X utf8 -m apa exchange "C:\Models\example.dxf" --output dxf-report
& $Apa -X utf8 -m apa exchange "C:\Models\example.pdf" --page 1 --output pdf-report
```

`plan` принимает существующие типизированные задания APA. Для оболочки выводит BIM Graph и маршруты `SceneWriter`. Для массового тиражирования выводит кандидатный граф, пока реальная регистрация команды не подтверждена. `exchange` сохраняет инвентаризацию и количества для IFC, предконтроль и инвентаризацию для DXF, векторную геометрию и PNG для страницы PDF. Используйте новые пути для выходных файлов и каталогов.

Для отдельного инструмента используйте `apa run-local ИМЯ_КОМАНДЫ --params параметры.json`. Контракт параметров показывает `catalog`. Для последовательности инструментов используйте `apa run-read-workflow --graph граф.json --output результат.json`. Граф принимает `after` и ссылки `$result` по JSON Pointer. Например, второй шаг может прочитать `/artifactPath` результата `AddOn.APAIFCArtifactsB2.IFCExtractElements` и экспортировать этот IFC-поднабор через `AddOn.APAIFCGeometryB3.IFCGeometryGLB`. Команды нативного API не допускаются в локальном графе.

```powershell
$Dump = 'examples/model_dump_v1.sample.json'
@((Get-Content $Dump -Raw | ConvertFrom-Json).elements[0].guid) |
    ConvertTo-Json -AsArray | Set-Content -Encoding utf8 guids.json
& $Apa -X utf8 -m apa documentation --native-dump $Dump --guids guids.json --story 0 --output documents
```

Документация принимает исходный или нормализованный Model Dump V1 и явно перечисленные GUID. В `documentation.json` и CSV используется одна версия модели. Планы и разрезы, требующие чтения нативной графики, отмечают наличие соответствующих данных в исходнике.

## Архитектура исполнения

Точка входа `apa.py` собирает существующие схемы и политики `DynamicCommands`. Локальные IFC, DXF и PDF-провайдеры регистрируются как `READ_ONLY`. `BIM Graph` проверяет зависимости и контракты. Нативные операции продолжают идти через `SceneWriter` с существующим журналом SQLite, привязкой к проекту, проверками модели и сверкой результата.

`apa project-runtime --help` показывает сохранённый интерфейс предконтроля и выполнения на тестовом проекте. `apa group-runtime --help` показывает протокол работы с выделенной копией PLN, сверку прерванного запуска и проверку повторного открытия. При наличии `saved.json` выбирайте сверку сохранённого результата. Для записи используют только область, прошедшую действующий предконтроль и привязку к проекту.

Опциональные `OpenBIMSegments` и `RasterFloorplan` подключаются через `apa --semantic-profile models.json catalog APASemantic`. Используется существующий локальный профиль `APA_SEMANTIC_ML_VENDOR_CONFIG_V1` с доверенными интерпретаторами, каталогами вендоров и контрольными суммами моделей. Пакет включает исходники и контракты Archicad 29. Для нативных операций нужен совместимый загруженный APX и активная рабочая копия PLN. Исторические установщики и мост GitHub остаются доступны отдельно для совместимости с установленным профилем.

## Повтор проверки

```powershell
$env:PYTHONPATH = 'scripts;tests'
$env:PYTHONUTF8 = '1'
& $Apa -m unittest -v test_apa_unified
```

Windows CI повторяет сквозные сценарии и регрессии на зафиксированных зависимостях, затем собирает ZIP тестируемого коммита и SHA-256. Сценарии CLI проверяют артефакты и содержимое исходных файлов. Для результата в Archicad действуют самостоятельные нативные испытания.
