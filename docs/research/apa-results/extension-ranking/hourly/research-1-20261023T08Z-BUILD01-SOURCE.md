# APA №1 | BUILD-01 | 2026-10-23 08Z | 29 SOURCE-проверок

**Воздействие:** новый upstream риск G4 — PR #1440 (quit crash, проверен на AC29 build5101 Windows); G0 получает независимую цепочку PID→loaded APX→SHA; G2 выявлены ложные готовности merged PR, фактический CREATE→MODIFY требует двух разрешений. **G0 BLOCKED; G1/G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. PASS=0.**

Строгий тип: SOURCE, без локального Windows/APX/PLN, без OFFLINE/LIVE/ACCEPTED. Контекст: [issue192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192), [№2 07Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T07Z-report.md). Не повторяются реализованные PR/Clone. Каждая запись — отдельный проверенный контракт; несколько записей относятся к одному файлу, это не 29 независимых производителей.

### S01 | G1 — Допускает ли authored offline? 
**Первоисточник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py#L728-L754
**Версия/лицензия:** PR162 pinned f7c37b8; APA
**Факт:** run_project для apa-authored-project/1 требует preflight/execute + transport; offline отклоняет.
**Решение/ограничение и задание №2:** Не обходить защиту; №2: read-only preflight либо вызов чистой compile_authored_intent с валидными read fixtures.

### S02 | G1/G2 — Ограничены ли дополнительные nativeComponents этажом/габаритом?
**Первоисточник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py#L535-L628
**Версия/лицензия:** PR162 pinned; APA
**Факт:** Проверка story/envelope явно есть для Walls/Roofs/Columns; для дополнительных Slabs/Beams аналогичного блока нет.
**Решение/ограничение и задание №2:** №2: fail-closed в существующем preflight для Slab/Beam, OFFLINE отрицательные случаи.

### S03 | G2 — Можно ли доверять provider-schema для ширины окна?
**Первоисточник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py#L411-L535
**Версия/лицензия:** PR162 pinned; APA
**Факт:** SceneWriter.verify_readback индексирует обязательные для writer width/height/sillHeight, хотя upstream schema может их опускать.
**Решение/ограничение и задание №2:** №2: проверять writer-required поля до CREATE, не после него.

### S04 | G2 — Есть ли второе изменение Slab?
**Первоисточник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py#L976-L1015
**Версия/лицензия:** PR162 pinned; APA
**Факт:** После CreateSlabs выполняется отдельный ModifySlabs; журнал BASIC_MODIFY_ATTEMPTED есть, но approval_record permission=CreateSlabs.
**Решение/ограничение и задание №2:** №2: отдельно квалифицировать оба write-scopes; до этого Slab материал не PASS.

### S05 | G2 — Есть ли готовый Beam adapter?
**Первоисточник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_connected_components.py#L53-L165
**Версия/лицензия:** PR162 pinned; APA
**Факт:** NativeAdapter(CreateBeams) уже существует, но requires opt-in.
**Решение/ограничение и задание №2:** №2: оценить подключение в том же SceneWriter без нового writer; Beam необязателен первому зданию.

### S06 | G0 — Что означает runtime registration?
**Первоисточник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_dynamic_commands.py#L309-L324
**Версия/лицензия:** PR162 pinned; APA
**Факт:** probe_runtime вызывает API.IsAddOnCommandAvailable с commandNamespace и commandName; version catalog не подтверждает APX.
**Решение/ограничение и задание №2:** №2: read-only per-command registration на установленном порту.

### S07 | G0 — Достаточен ли текущий probe для APX SHA?
**Первоисточник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_runtime_version_probe.py#L36-L94
**Версия/лицензия:** PR162 pinned; APA
**Факт:** Probe читает GetProjectInfo/GetAddOnVersion/GetStories, но не хеширует загруженный модуль.
**Решение/ограничение и задание №2:** №2: дополнить фактическим PID/module path/SHA через готовые Windows tools.

### S08 | G0 — Как увидеть загруженный модуль без модификации APX?
**Первоисточник:** https://learn.microsoft.com/en-us/sysinternals/downloads/listdlls
**Версия/лицензия:** Microsoft ListDLLs v3.2; Microsoft license
**Факт:** listdlls -v PID перечисляет модули и версии; не является доказательством SHA и не запускает Archicad.
**Решение/ограничение и задание №2:** №2: по PID получить фактический путь APX; только read-only.

### S09 | G0 — Чем вычислить точный SHA APX?
**Первоисточник:** https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash?view=powershell-5.1
**Версия/лицензия:** Windows PowerShell 5.1; Microsoft
**Факт:** Get-FileHash -LiteralPath <loaded APX path> -Algorithm SHA256 вычисляет хеш байтов файла.
**Решение/ограничение и задание №2:** №2: сопоставить путь с загруженным модулем; не считать хеш другого APX доказательством INSTALLED.

### S10 | G0 — Что гарантирует официальный AC29 JSON API?
**Первоисточник:** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
**Версия/лицензия:** Graphisoft AC29 b3000; proprietary
**Факт:** IsAlive, GetProductInfo (версия/build/локаль), IsAddOnCommandAvailable (регистрация) — три разных утверждения.
**Решение/ограничение и задание №2:** №2: проверить каждое отдельно; не смешивать Tapir GetProjectInfo с official API.

### S11 | G2 — Чем штатно проверить доступность свойства по классификации?
**Первоисточник:** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html#archicad.releases.ac29.b3000commands.Commands.GetPropertyDefinitionAvailability
**Версия/лицензия:** Graphisoft AC29; proprietary
**Факт:** GetPropertyDefinitionAvailability(propertyIds) возвращает допустимые classification items; не сообщает редактируемость текущего экземпляра.
**Решение/ограничение и задание №2:** №2: перед structuralFunctions сопоставить классификацию + определение свойства.

### S12 | G4 — Является ли bounding box полной геометрией?
**Первоисточник:** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
**Версия/лицензия:** Graphisoft AC29; proprietary
**Факт:** Get3DBoundingBoxes возвращает только AABB; GetComponentsOfElements возвращает компоненты; GetAllElements — GUID в current plan.
**Решение/ограничение и задание №2:** №2: AABB использовать как coarse filter, BREP/host/readback отдельно, проверить все databases.

### S13 | G2 — Как определить происхождение library part?
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/150_UserInterfaceToolSettings/150_UserInterfaceToolSettings-10.htm
**Версия/лицензия:** Graphisoft Archicad29; proprietary
**Факт:** Folder View with sources показывает библиотечный пакет, а Favorites — отдельный слой настроек.
**Решение/ограничение и задание №2:** №2: фиксировать пакет/имя Favorite и реальные GUID в scratch; не смешивать с именем GDL.

### S14 | G2 — Почему свойство может отсутствовать у объекта?
**Первоисточник:** https://help.graphisoft.com/AC/29/RUS/_AC29_Help/045_PropertiesClassifications/045_PropertiesClassifications-6.htm
**Версия/лицензия:** Graphisoft AC29 RUS; proprietary
**Факт:** Доступность свойства ограничивается классами; опция Нет скрывает свойство.
**Решение/ограничение и задание №2:** №2: проверить structural function классификацию до изменения; без расширения свойств в исходном PLN.

### S15 | G4 — Безопасно ли закрывать Archicad с запущенным Tapir Palette script?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1440
**Версия/лицензия:** Tapir upstream PR1440, OPEN 23.10.2026; MIT
**Факт:** Репорт: воспроизводимый crash при quit; исправление испытано автором на AC29.0 JPN build5101 Windows; PR не объединён.
**Решение/ограничение и задание №2:** №2: G4 close gate — отсутствие активных palette scripts/relay; не устанавливать patch без разрешения.

### S16 | G4 — Останавливает ли Stop дочерний Python?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/775
**Версия/лицензия:** Tapir upstream PR775 OPEN; MIT
**Факт:** Старый Stop убивает uv, Python-child может жить; proposed process-tree kill unbuilt/untested.
**Решение/ограничение и задание №2:** №2: до G4 исключить висящие процессы, не применять unverified PR.

### S17 | G2 — Есть ли готовая read-only проверка значений property?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1147
**Версия/лицензия:** Tapir upstream PR1147 OPEN; target 1.7.x; MIT
**Факт:** CheckPropertyValues(propertyValues [{propertyId,propertyValue:{value}}]) возвращает isValid/error; не протестирован в AC29.
**Решение/ограничение и задание №2:** №2: DEFER как неустановленный; штатный AC29 GetDetailsOfProperties/enum + fail-closed input.

### S18 | G2 — Можно ли заранее проверить editable/visible property?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1238
**Версия/лицензия:** Tapir upstream PR1238 OPEN, 1.7.3; MIT
**Факт:** GetPropertyEditability различает editable и visible per element/default; не в локальной 1.5.10.
**Решение/ограничение и задание №2:** №2: не включать в required runtime; проверять доступность существующим API29 и readback.

### S19 | G2 — Можно ли проверить property availability в tool defaults?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1279
**Версия/лицензия:** Tapir upstream PR1279 OPEN, 1.7.3; MIT
**Факт:** GetPropertyAvailabilityOfDefaults(elementType,properties) возвращает available/visible, Favorite действует только после применения.
**Решение/ограничение и задание №2:** №2: не полагаться на неподтверждённую команду; проверить применённые defaults на scratch.

### S20 | G2 — Можно ли читать values текущих defaults?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1336
**Версия/лицензия:** Tapir upstream PR1336 OPEN, 1.7.3; MIT
**Факт:** GetPropertyValuesOfElementDefaults требует elementType + properties; автор указал отсутствие DevKit/build/live проверки.
**Решение/ограничение и задание №2:** №2: DEFER; не блокировать базовую модель новой командой.

### S21 | G2 — Объединённый PR означает поддержку AC29?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1149
**Версия/лицензия:** Tapir PR1149 MERGED 23.10.2026 05:35Z; MIT
**Факт:** MakePropertyAvailable/UnavailableForElements имеет #if AC27 && !AC28, в AC29 возвращает отказ.
**Решение/ограничение и задание №2:** №2: EXCLUDE для AC29; не считать merged=compatible.

### S22 | G2 — Работают ли GH components для defaults после merge?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1141
**Версия/лицензия:** Tapir PR1141 MERGED 23.10.2026 05:41Z; MIT
**Факт:** Grasshopper UI-компоненты ссылаются на backend PR968 и PR1140; без них unknown command.
**Решение/ограничение и задание №2:** №2: не ставить как готовое решение для G2, проверить dependencies прежде чем рекомендовать.

### S23 | G2 — Есть ли backend для GH defaults property?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/968
**Версия/лицензия:** Tapir PR968 OPEN 23.10.2026; MIT
**Факт:** Get/SetPropertyValuesOfElementDefaults не объединены; UI PR1141 не доказывает регистрацию.
**Решение/ограничение и задание №2:** №2: DEFER до merge+build+installed; не заменять существующий API.

### S24 | G2 — Есть ли backend для GH classifications defaults?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1140
**Версия/лицензия:** Tapir PR1140 OPEN 23.10.2026; MIT
**Факт:** Get/SetClassificationsOfElementDefaults не объединены; PR1141 зависит от них.
**Решение/ограничение и задание №2:** №2: DEFER; не блокировать BUILD-01 GH-связкой.

### S25 | G1 — Можно ли считать Dimensions preferences готовым механизмом units?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1025
**Версия/лицензия:** Tapir PR1025 MERGED 23.10.2026 01:16Z; MIT
**Факт:** Get/SetProjectPreferences Dimensions расширение ссылается на базовый PR964, который пока OPEN; автор не сверял DevKit.
**Решение/ограничение и задание №2:** №2: не полагаться на это для meters/radians; исходный intent уже фиксирует units.

### S26 | G1 — Доступен ли базовый GetProjectPreferences?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/964
**Версия/лицензия:** Tapir PR964 OPEN 23.10.2026; MIT
**Факт:** WorkingUnits/CalculationUnits/ReferenceLevels proposed; не установлен и не проверен.
**Решение/ограничение и задание №2:** №2: использовать явные единицы задания и штатный GetCalculationUnits, не новый mutation.

### S27 | G4 — Доступен ли read-only GetExportTolerance?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1359
**Версия/лицензия:** Tapir PR1359 OPEN, 1.7.3; MIT
**Факт:** GetExportTolerance proposed; SetLast3DDefaultLevels — write, отдельный риск; не подтверждено в 1.5.10.
**Решение/ограничение и задание №2:** №2: DEFER export tolerance, не менять defaults ради G4.

### S28 | G2 — Есть ли атомарная bulk property запись?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1148
**Версия/лицензия:** Tapir PR1148 OPEN, AC27+; MIT
**Факт:** ModifyPropertyValueOfElements предлагает all-or-nothing, но не проверен в установленной версии.
**Решение/ограничение и задание №2:** №2: не использовать для structuralFunctions G2; оставить existing guarded write+readback.

### S29 | G2 — Есть ли проверка синтаксиса property expressions?
**Первоисточник:** https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1146
**Версия/лицензия:** Tapir PR1146 OPEN, AC25–30 target; MIT
**Факт:** CheckPropertyExpressions и GetPropertyExpressionReferences read-only; автор не испытал в Archicad.
**Решение/ограничение и задание №2:** №2: DEFER — BUILD-01 не требует новых expressions.

**Контроль счёта:** 29 отдельных SOURCE-контрактов, ни одного INSTALLED/LIVE. Экспертные баллы не являются benchmark. MODEL_MODE_NOT_VERIFIABLE.
