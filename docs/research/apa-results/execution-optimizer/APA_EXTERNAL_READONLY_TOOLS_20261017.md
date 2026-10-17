# APA AC29 — изолированные аналитические инструменты V1

**Ветка:** `feature/apa-readonly-tools-isolated-20261017`; draft PR #142 поверх ветки PR #139. `main` не изменяется.

## Цель и существующий функционал

В APA уже есть `archicad_connected_ifc.inspect_quantified_exchange` и `ifcopenshell==0.8.5` в `scripts/requirements-connected.txt`. Второй IFC-движок, SceneWriter, транспорт или механизмы записи в PLN не создаются.

Пакет включает:
- IfcClash 0.8.5 — проверки коллизий IFC;
- IfcDiff 0.8.5 — сравнение экспортов IFC;
- IfcTester 0.8.5 — проверки IFC по явно указанному IDS;
- Ifc5D 0.8.5 — доступная библиотека для будущего использования, без второго расчётного QTO-движка;
- pdfplumber 0.11.10 — текст и примитивы в координатах PDF;
- ezdxf 1.4.5 — примитивы DXF в исходных единицах;
- IfcOpenShell 0.8.5, networkx 3.6.1, shapely 2.2.0 и необходимые зависимости.

## Python и изоляция

Поддерживаются **Python 3.11.x и 3.12.x, Windows x64**. Системный Python 3.14 пока не поддерживается. Существующий Python APA не обновляется и не заменяется; создаётся только:

`C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1\`

Установщик требует существующий `C:\LocalAI\APA_AC29_Stable` с `apa-selector-install-receipt.json`; проверяет отсутствие папки назначения (повторная установка не выполняется без аудита). Установщик:
1. создаёт отдельный venv выбранной версии;
2. загружает `odfpy==1.4.1` (единственный исходный пакет) и проверяет PyPI SHA-256 `db766a6e59c5103212f3cc92ec8dd50a0f3a02790233ed0b52148b70d3c438ec`;
3. устанавливает только зафиксированные wheel-пакеты, проверяет `pip check`, `doctor` и доступность CLI;
4. сохраняет `installation.json` с SHA-256 установленных адаптеров.

Никаких изменений PLN, APX, глобального pip, локального Dispatcher, SQLite-журнала или рабочего SceneWriter не предусмотрено.

## Установка на уже настроенном компьютере пользователя

На машине установлены `C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe` версии 3.11.9 x64 и Python 3.14.6. Использовать **3.11.9** напрямую.

Исходная ветка **уже склонирована** в `%TEMP%\APA_ExternalReadonly_20261017`. Не удаляйте её и не скачивайте повторно. Выполните PowerShell-блок **только после получения и сверки нового коммита PR #142**:

```powershell
$ErrorActionPreference = 'Stop'
$checkout = Join-Path $env:TEMP 'APA_ExternalReadonly_20261017'
$python = 'C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe'
$branch = 'feature/apa-readonly-tools-isolated-20261017'

if (!(Test-Path $checkout) -or !(Test-Path $python)) { throw 'GitHub clone or Python 3.11 not found' }
if ((git -C $checkout status --porcelain)) { throw 'Local source checkout changed; stop instead of overwrite' }
git -C $checkout fetch --no-tags origin $branch
if ($LASTEXITCODE -ne 0) { throw 'GitHub fetch failed' }

# Следующая версия документа фиксирует конкретный проверенный SHA.
# Обязательна независимая сверка SHA после обновления checkout.
```

После установки:
```powershell
$root = 'C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1'
& "$root\venv\Scripts\python.exe" "$root\apa_external_readonly.py" doctor
```

## Подключение к существующему Dynamic Router

`apa_external_catalog.py` регистрирует шесть локальных команд через штатный `DynamicCommands.add_local_provider`: `IFCDiff`, `IFCClash`, `IDSValidate`, `IFCQuantities`, `PDFVectors`, `DXFVectors`. Для регистрационного вызова используется установленный адаптер в `external-tools`; основной Python импортирует только лёгкий stdlib-адаптер, а все внешние библиотеки запускаются из venv через выделенный процесс.

```python
import importlib.util
from pathlib import Path
module = Path(r"C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1\apa_external_catalog.py")
spec = importlib.util.spec_from_file_location("apa_external_catalog", module)
plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin)
receipt = plugin.register(router)  # original DynamicCommands instance
ticket = router.prepare("AddOn.APAExternalReadOnly.IFCDiff", {
    "a": r"D:\IFC\before.ifc",
    "b": r"D:\IFC\after.ifc",
    "output": r"D:\IFC\diff-evidence-new.json"
})
result = router.read(None, ticket, reviewed_read_only=True)
```

Автоматическая регистрация на каждом запуске APA **не внедрена**; регистрация в конкретном экземпляре Router происходит только по явному вызову.

## Приёмка и ограничения

- Windows CI: обязательно отдельно проверить 3.11 и 3.12, включая фактическую установку всех пакетов, `pip check`, `doctor`, импорты vendor CLI и 7 целевых тестов.
- Ноутбук: `NOT_INSTALLED` до получения `installation.json` и успешного `doctor`.
- IFC/PDF/DXF реального здания: `NOT_VERIFIED` до реальных аналитических запусков.
- Векторный PDF не задаёт BIM-масштаб автоматически; DXF не гарантирует верные координаты; столкновения IFC могут быть намеренными; IDS не заменяет строительные нормы РФ.
- Отдельный незакрытый `BDD 1.14 UNKNOWN_OUTCOME` нельзя повторять или пересохранять до независимой read-only сверки.

Исходники: https://github.com/IfcOpenShell/IfcOpenShell · https://github.com/jsvine/pdfplumber · https://ezdxf.readthedocs.io/

## Explicit Dynamic Router activation on already-installed laptop (2026-10-17)

The user confirmed an installed isolated sidecar at
`C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1`
with `doctor: READY` and Python 3.11.9. **Never rerun the installer**.
This extension is activated in a NEW read-only process by
`scripts/apa_external_router_activation.py` in this branch. It imports the
ORIGINAL installed `archicad_dynamic_commands.DynamicCommands`, reads the
pinned Tapir 1.5.10 schema (prefer stable installed, then repository checkout),
calls `apa_external_catalog.register(router)` and validates six reviewed
`READ_ONLY` handlers. Then two ephemeral documents (PDF/DXF) are generated
under Python's temporary directory, dispatched using
`router.prepare(...)` and `router.read(None, ..., reviewed_read_only=True)`
and checked for actual extracted line primitives.

The original router needs JSON Schema validation. Install only
`jsonschema==4.25.1` **in the already isolated external-tools venv**;
do not modify any globally installed Python or core APA packages.
CI uses this exact version on both Windows Python 3.11 and 3.12.

```powershell
$ErrorActionPreference = "Stop"
$checkout = Join-Path $env:TEMP "APA_ExternalReadonly_20261017"
$root = "C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1"
$py = Join-Path $root "venv\Scripts\python.exe"
$branch = "feature/apa-readonly-tools-isolated-20261017"
if (!(Test-Path $checkout) -or !(Test-Path $py)) { throw "Existing source or isolated venv not found" }
if (git -C $checkout status --porcelain) { throw "Source checkout locally modified" }
git -C $checkout fetch --depth 1 --no-tags origin "refs/heads/$branch"
if ($LASTEXITCODE -ne 0) { throw "Fetch failed" }
# Check against the SHA pinned in the accompanying user instruction.
git -C $checkout checkout --detach FETCH_HEAD
if ($LASTEXITCODE -ne 0) { throw "Checkout failed" }
& $py -m pip install --no-input --only-binary=:all: jsonschema==4.25.1
if ($LASTEXITCODE -ne 0) { throw "Local schema validator install failed" }
& $py -m pip check
if ($LASTEXITCODE -ne 0) { throw "Dependency check failed" }
& $py "$checkout\scripts\apa_external_router_activation.py"
if ($LASTEXITCODE -ne 0) { throw "Real Dynamic Router activation check failed" }
```

**Acceptance:**
- [Windows CI #39052634257](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/39052634257): Python 3.11 and Python 3.12 **PASS**, 8 focused tests per version.
- Original unmodified `DynamicCommands.prepare/read` plus six registered read-only policies is exercised in CI (vendor execution mocked only at this unit-test boundary).
- Actual upstream execution on disposable IFC/PDF/DXF: `IFCDiff`, `PDFVectors`, `DXFVectors` **PASS** in both Windows environments, no Archicad process.
- Local user's installed APA integration probe: **NOT_RUN** until user executes and returns output; it will test real router plus PDF/DXF.
- `IFCClash`, `IDSValidate`, `IFCQuantities` registered but live-file semantics are **NOT_VERIFIED**.
- Registration is **not automatic across unrelated existing APA processes**; this is an opt-in activation entry point, not a core startup hook or a second writer.
- No PLN/model change, APX change, Dispatcher/Arena change, no retries to the unresolved BDD 1.14 task.
