# APA №2 | 10Z | Контрааудит B — G0/G1/G4 и доказательность

**Вопрос:** могут ли source snapshot, OPEN PR или read-only preflight быть приняты за INSTALLED/LIVE/ACCEPTED?

**SOURCE:** 14 прямых GitHub `fetch_pr` (#34/#48/#74/#82/#97/#126/#131/#149/#150/#151/#154/#159/#160/#162) — все OPEN, merged=false. PR162 HEAD `f7c37b84b76c040c417ccd58a5543326e50f673a` — source branch, не доказательство загрузки в Windows.

**G0:** pinned schema имеет 262 команды и metadata `provider_version=1.5.10` с историческим `C:\LocalAI\SafeBIM_Global_Library_Test_Projects\Тест MER .pln`, port19723. Без PID→loaded APX path/SHA256 и локального `API.IsAddOnCommandAvailable` installed contract неизвестен. `DynamicCommands.probe_runtime` проверяет регистрацию, не эквивалентность input/output schema.

**G1:** `run_project` для `apa-authored-project/1` отвергает `mode='offline'`; необходим реальный read-only preflight. `guarded_project` требует точный `projectName/projectPath`, `actStory`, `floorId`, `GetAddOnVersion`. CLI `--scratch-port` привязан только к `C:\LocalAI\APA_Test_House_01.pln`; `--isolated-port` — к `C:\LocalAI\APA_Isolated_Writer_Test_01.pln`. `bind_authorized_saved_copy` существует с SHA256/authorizationRef, но CLI не вызывает его автоматически.

**Ложный LIVE:** `run_project` выставляет `evidenceKind='LIVE'` при `transport is native_transport` даже в read-only `mode='preflight'`. Это маркировка транспорта, **не** квитанция native CREATE. Нужны явные `modelWriteAttempts`, SQLite receipt и независимый readback.

**G4:** `archicad_authored_geometry.run` вызывает `GetModelDumpV1`; в pinned 262 commands команда отсутствует. `Get3DBoundingBoxes` не заменяет BREP. Upstream [Tapir issue #681](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/681) касается AC29 build3000/Win/Tapir1.5.9 и SaveProject из 3D, не доказывает тот же дефект на build5101/1.5.10. Требуется runtime read-only proof и GUI close/reopen.

**Результат:** G0 BLOCKED, G1 SOURCE_ONLY/NOT_RUN, G2 SOURCE_ONLY/DUAL_SCOPE_BLOCKED, G3 NOT_AUTHORIZED, G4/G5 NOT_RUN. Источник/тест/установка/приёмка строго разделены. Никаких изменений main/PLN/APX/кода.
