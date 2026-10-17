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

## October 17 — all six vendor families and guarded production sync

### Actual IFC tests

[Windows CI #39055216133](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/39055216133)
passed on Python 3.11 and 3.12 with temporary **IFC4 walls containing geometry**:
- IfcClash 0.8.5 actual geometry CLI succeeds after a source-reviewed required `mode="intersection"`, `tolerance=0.001`, `check_all=False` fix. No claim that every source collision is detected, and clashes alone do not certify engineering errors.
- IfcTester 0.8.5 actual `IDSValidate` CLI succeeded with actual IDS requirement that IFC walls have `Name`.
- `IFCQuantities` invoked the **existing** `archicad_connected_ifc.inspect_quantified_exchange` on a geometrically represented IFC4 wall, returning one `IfcWall`, not a new QTO computation.
These are temporary source files generated in CI, not the user's BDD/PLN.

### Existing laptop installation

The user's installed adapter was an earlier, manifest-hash-protected version lacking the required IfcClash source-set mode. **Do not reinstall packages or overwrite the adapter directly**; the installed `apa_external_catalog.py` verifies the adapter SHA against `installation.json` and correctly fails when they disagree.

New `scripts/upgrade_apa_external_readonly_clash.py` performs explicit opt-in `--apply` upgrade of **only** `apa_external_readonly.py` and its corresponding `installation.json`. Before changing anything it checks:
- every installed adapter/catalog/requirements SHA against manifest;
- that the new source differs by exactly the reviewed IfcClash mode/tolerance hunk (allow Windows CRLF encoding);
- target `venv\Scripts\python.exe` exists;
- `upgrade-ifcclash-intersection-v1` does not yet exist.

It writes untouched backups under `external-tools\apa-readonly-v1\upgrade-ifcclash-intersection-v1`, atomically installs the reviewed source and updated receipt, runs `doctor`, verifies target digest, and attempts recovery on any caught failure. Repeated `--apply` is refused. The native APA core, SDK DLL/APX, original router, Dispatcher and PLN remain unchanged.

After upgrade, `scripts/apa_external_ifc_host_probe.py` creates **temporary IFC4/IDS fixtures**, uses the original installed `DynamicCommands` to register six commands from the installed sidecar and executes three IFC operations via `router.prepare/read`. It reports `REAL_VENDOR_IFC_READ_ONLY_ROUTE_PASS` only after all operations pass. That is a full isolated **host process** test, not an Archicad model mutation or engineering approval.

### Session-scoped auto-attach

`scripts/apa_external_session_factory.py` exports the same
`native_command_router(schema_path, official_commands=None, include_functional_modules=True)`
signature as the original APA core. The wrapper calls **the original factory first**, retaining existing SDK/functional providers, then calls the installed reviewed catalog's `register(router)` on **that same router**. Each router created through this wrapper therefore registers the six external commands in the new session. No second router or writer.

**The wrapper is opt-in.** It is not injected into pre-existing processes, does not hook Windows startup or change the original core `native_command_router` import globally. Production caller(s) must explicitly import the wrapper instead of the core factory; that change remains NOT_DEPLOYED until their startup site can be reviewed and validated against stable APA module hashes. Do not claim global auto-registration based on factory unit tests alone.

### Local acceptance statuses

- User laptop isolated 10/10 packages + doctor READY: CONFIRMED.
- User laptop six DynamicCommands + PDF/DXF real operation: CONFIRMED from user-provided PowerShell JSON.
- Windows CI three new IFC operations: PASS on CI dummy IFC geometry.
- User laptop IFCClash upgraded and 3 IFC operations via installed router: **NOT_RUN** until upgrade/probe receipts.
- Factory startup integration into existing persistent APA processes: **NOT_APPLIED**.
- Native operations and BDD model: untouched by this package; BDD 1.14 unknown outcome still demands read-only reconcile.

## Permanent scoped vendor factory — reviewed deployment (18 October update from user logs)

Actual laptop evidence: the user confirmed `EXTERNAL_READONLY_IFCCLASH_ADAPTER_UPGRADED`, adapter SHA-256 `83421ab9a0315d5813bb5e0ce1ade2f616c0be830f5a87f35a6226c74b85a75a`, `doctor READY`, all 10 version pins matched, `REAL_VENDOR_IFC_READ_ONLY_ROUTE_PASS`, 3 vendor operations and 0 native/model calls, and `APA IFC ROUTER: VERIFIED PASS`. The generated example fixtures returned `clashCount=0`: this is neither a claim about a user's actual model nor full collision/geometry acceptance.

**Existing APA has MULTIPLE call sites** using `APA.native_command_router(...)` directly, including BDD readback, windows, native copying, bulk placement, and save operations. Modifying `scripts/archicad_project_accelerator.py` globally would change a hash-protected stable core module and could invalidate approved controllers. A global auto-loader/monkey patch is intentionally **not** installed.

`scripts/install_apa_external_session_factory.py` provides a **separately opt-in, one-time persistent installation** of the safe wrapper into
`C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1\session-factory-v1\`.
It independently reviews the existing installation receipt, exact upgraded adapter SHA, installed catalog SHA, the existence of the original stable core files and all pristine source snapshot files. It copies ONLY:
- `apa_external_session_factory.py`: a thin wrapper around the existing original `archicad_project_accelerator.native_command_router`, attaching the same six installed READ_ONLY providers to each newly returned router instance.
- `tapir-scene-live.json` and **both** `command_definitions.js` and `common_schema_definitions.js`, because `catalog_with_provenance` checks original Tapir JS SHA-256 and re-parses the command definitions. Copying JSON alone is insufficient.
- `session-factory-install.json`: own exact source and installed adapter/catalog SHA values.

The installer makes a new directory only, refuses an existing directory, does not edit existing core modules or any installed package, and immediately executes a **read-only** smoke through the original factory and the installed provider. `--check` revalidates and re-executes an in-memory router creation without an IFC/PLN write.

**Usage in future new processes ONLY:**
```python
import sys
from pathlib import Path
root = Path(r"C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1\session-factory-v1")
sys.path.insert(0, str(root))
from apa_external_session_factory import native_command_router
router = native_command_router(root / "tapir-scene-live.json",
                               include_functional_modules=False)
# Original DynamicCommands object; six local provider handlers already registered.
```

The default wrapper signature preserves the core API, including `official_commands` and `include_functional_modules=True`; `--include-functional-modules` is an explicit CLI probe option. The routine installation probe avoids optional native modules. This factory **does not migrate or mutate existing running processes**. Callers importing the old `APA.native_command_router` still create old-style routers, so claim only `autoRegisteredWithinFactorySessions=true`, not global registration.

**Pending after installation:** A specific existing APA startup/controller entrypoint must be chosen and its caller switched to the opt-in factory if its functionality needs the six vendors. This is NOT a live Archicad or BDD write test. No automated edits to signed hash-guarded core, Dispatcher, Active SceneWriter or PLN.

## Production read-only analytics entrypoint — opt-in original router (2026-10-17)

The laptop successfully installed and checked `session-factory-v1` (user-visible `APA SESSION FACTORY: VERIFIED PASS`). Subsequent read-only inventory of all stable `scripts/*.py` shows **multiple independent** `APA.native_command_router(...)` call sites: `apa_bdd_existing_router_readback.py`, `apa_bdd_kr12_two_north_windows.py`, `apa_reconcile_source_batch_save.py`, `apa_source_qualified_native_batch.py`, `archicad_authored_extension.py`, and `archicad_strategy_discovery.py` at 1064 and 1145. These include native WRITE workflows and SHA-bound core modules. Rewriting or monkey-patching them globally just to add external file analysis is unsafe.

The new `scripts/apa_external_analytics_entrypoint.py` is a **practical explicit production launcher**, not a simulated registration check:
- loads the **installed** `session-factory-v1/apa_external_session_factory.py`, validating its own receipt, immutable source JS provenance, registered vendor catalog and reviewed adapter hashes;
- creates the **original DynamicCommands** object using the official original factory and `include_functional_modules=False`; adds six READ_ONLY vendor commands automatically via the installed factory, not via a second Python router;
- dispatches the selected `--command` through original `router.prepare` + `router.read(None, ticket, reviewed_read_only=True)`;
- input files are existing IFC/PDF/DXF/IDS, and `--output` must be an **absent JSON file** in an existing directory **outside** `APA_AC29_Stable`. Incomplete or drifting receipts block execution;
- prints only minimal source-backed proof, output path and output SHA-256, so large quantity/vector reports are not injected into chat; native calls and PLN writes always zero.

Supported `--command` values: `IFCDiff` (`--a` and `--b` IFC); `IFCClash` (one or two IFCs); `IDSValidate` (`--a` IFC + `--ids`); `IFCQuantities` (`--a` IFC); `PDFVectors` (`--a` PDF); `DXFVectors` (`--a` DXF). No automatic selection based solely on vague natural language; the source kind and user command must be explicit.

The new `scripts/install_apa_external_analytics_entrypoint.py` is a **one-time opt-in** installer for exactly this read-only launcher and a new `analytics-entrypoint-install.json` receipt under the already verified `session-factory-v1` directory. It does **not** reinstall vendor packages or mutate the existing session factory receipt. On a repeated install the new-file-only guard refuses overwrites; `--check` validates the installed script SHA against the published source and receipt.

Example (after explicit installation and source checkout SHA match):

```powershell
$py = 'C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1\venv\Scripts\python.exe'
$runner = 'C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1\session-factory-v1\apa_external_analytics_entrypoint.py'
& $py $runner --command IFCQuantities --a 'D:\IFC\actual-export.ifc' --output 'D:\IFC\quantities-new.json'
```

**Qualification:** the CI fixture tests exercise the real original router and mock the downstream vendor call for this new CLI; the vendor operations themselves have already passed separately on actual temporary IFC/PDF/DXF structures and on the user's laptop. This CLI is **not yet installed or executed on the user's actual IFC**. The existing BDD export is not touched. `archicad_strategy_discovery.py` and every other original callsite remain unchanged. The installed session factory still automatically registers vendors **only for new sessions created through the factory**, not all running processes.
