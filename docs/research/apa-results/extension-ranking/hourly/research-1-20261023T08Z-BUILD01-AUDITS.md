# APA №1 | BUILD-01 | 2026-10-23 08Z | Два собственных контрааудита

## A01 — первоисточник, версия, лицензия, несовпадение MERGED/INSTALLED

**Вопрос:** действительно ли найденные upstream возможности применимы к Archicad 29 build 5101 + локальному Tapir 1.5.10?

1. [PR1440](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1440) OPEN на момент проверки 23.10.2026. Автор сообщил о фактическом тесте на **Archicad 29.0 JPN (5101) Windows**: воспроизводимый crash on quit при работающем palette script и отсутствие crash после патча. Это более сильное SOURCE-доказательство, чем синтетический тест, но **не** тест на установленном у владельца APX 1.5.10 и не доказательство наличия того же дефекта в конкретной сборке. Решение: безопасный pre-close gate, не замена бинарника.
2. [PR775](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/775) OPEN, автор прямо указал **unbuilt/untested**. Риск оставшихся Python-child при Stop uv — условный; без Windows process inventory нельзя утверждать наличие orphan процессов. Не включать патч в сборку без допуска.
3. [PR1149](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1149) MERGED 23.10.2026 05:35Z, но исходник guard **ServerMainVers_2700 && !ServerMainVers_2800**: только AC27. **Для AC29 исключить**. MERGED не означает COMPATIBLE.
4. [PR1141](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1141) MERGED 05:41Z, но backend [#968](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/968) и [#1140](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1140) остаются OPEN: GH-компонент может выдавать unknown command. Не предлагать как установленный рабочий мост.
5. [PR1025](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1025) MERGED 01:16Z, базовый [#964](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/964) OPEN; автор не проверил DevKit. Не принимать unit-preferences как подтверждённый локальный контракт.
6. [Официальный API29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html) содержит GetProductInfo, IsAlive, IsAddOnCommandAvailable, GetPropertyDefinitionAvailability; **GetProjectInfo** из существующего APA относится к Tapir, а не к официальному списку Python wrapper AC29. Нельзя объединять два пространства имён.
7. [Лицензия Tapir 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/LICENSE): MIT; Graphisoft SDK/Archicad — proprietary. Лицензия safe-bim-layer в этом проходе отдельно не подтверждена.

**Результат A01:** новый P0-кандидат PR1440 применим как сигнал риска G4, не как установленное исправление; три merged-пакета отсеяны по версии/зависимостям. Никаких SOURCE→INSTALLED, CI→LIVE, MERGED→ACCEPTED.

## A02 — применимость к BUILD-01, отсутствие дублирования, защита нативных записей

**Вопрос:** продвигает ли исследование создание нового полного здания, не заменяя его каталогом и не создавая второго исполнителя?

1. [Issue192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) требует G0 exact PID/port/PLN/APX/schema, затем G1 typed DAG, G2 safe contracts; G3/G4/G5 только при отдельном разрешении. В данном проходе нет доступа к Windows, scratch PLN или зарегистрированному APX. Следовательно G0 BLOCKED, G1/G2 SOURCE_ONLY.
2. [Existing compiler PR162](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py#L535-L628) уже компилирует authored DAG и проверяет часть добавленных компонентов. Никакой новый compiler/writer не нужен. Для additional Slab/Beam отсутствует эквивалент story/envelope check; это адресная задача №2, а не повод заменить SceneWriter.
3. [SceneWriter](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py#L976-L1015) делает CreateSlabs→ModifySlabs; durable BASIC_MODIFY_ATTEMPTED существует, но approval_record.permission фиксирует CreateSlabs. Отдельное подтверждение права ModifySlabs и независимый material readback обязательны. Это **статическая находка**, не доказательство незаконной LIVE записи.
4. [№2 за 07Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T07Z-report.md) уже установил optional-field vs writer-readback gap и Beam adapter opt-in. Наш отчёт не заявляет это собственным новым открытием; он указывает на конкретные штатные средства и свежий G4-риск.
5. [ListDLLs](https://learn.microsoft.com/en-us/sysinternals/downloads/listdlls) + [Get-FileHash](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash?view=powershell-5.1) — только read-only инвентаризация. Не меняют APX и не требуют платного API. Но Windows запуск/установка №1 не выполнялись.
6. При G4 требуются GuardedSave, отсутствие работающего palette script, GUI Close, повторное Open и независимые GUID/BREP/host/material checks. Нельзя считать Get3DBoundingBoxes полноценным BREP, исторический PR74 LIVE — новым BUILD-01, а SOURCE-проверки — PASS.
7. IFC/Hotlink/DXF/PDF/MEP/SAF/Publisher не исследовались в этой итерации: в прочитанном issue192 нет нового доказанного блокера этих направлений, способного опередить G0–G2. CloneNativeGroupV1 и перечисленные уже реализованные PR не повторялись.

**Результат A02:** немедленное действие №2 — PID→loaded APX→SHA→registration/schema; затем fail-closed preflight existing compiler, включая Slab/Beam/hosted opening и права на MODIFY. Только после реального OFFLINE_PASS и отдельного допуска возможна G3. Отчёт не содержит нового здания.

## Проверка реестра/истории

- [Матрица 61](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json): 61 записей, 61 уникальный ID, 61/61 формул priority = 12*need + 7*(5-effort) + confidence совпали, blob SHA `9cb5e6f2a59f80762cc77073eeb10404829af75a`.
- [Исторический PROJECT_PLAN rev182](https://github.com/dvikt33-ux/safe-bim-layer/blob/049576378c961c5d7a9a62611f4091e3da70d309/docs/research/apa-results/control/PROJECT_PLAN.json): `revision=182`, blob `c2ab2f9d606db1412c4031076103c267fc463f83`, **только чтение**.
- [NEXT_RESEARCH_PRIORITIES](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md), [№2 07Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T07Z-index.md), последний доступный аудит №3 от 20.10.2026 07Z прочитаны; нового №3 за 23.10 08Z в каталоге не обнаружено.
- Opera: Primary сообщает Browser not connected; второй link требует интерактивного ввода. Пользовательские вкладки не закрывались и не менялись.
- Исходный код APA, main, PLN/APX, установка, LIVE, Work/Codex/Arena, платные API и PR merge не выполнялись.

**SOURCE=29; OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.**
