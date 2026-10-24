# APA №1 — BUILD-01 | 2026-10-23 09Z | два самостоятельных контрааудита

## A01 — первоисточник, совместимость и отрицательные контрпримеры

**Вопрос:** являются ли 30 прочитанных первоисточников доказательством дефектов или новых команд локального Tapir 1.5.10 на Windows11/Archicad29 build5101?

**Проверка:** прямые GitHub fetch_issue/fetch_pr для 27 отдельных issue/PR, официальный Graphisoft AC29 Library Manager и SDK29 Opening, а также tag 1.5.9 LICENSE (30 SOURCE-записей в A/B). Проверены status/version/build и текст доказательств. Положительные контракты разнесены по типам:
- [#573](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/573) AC28 Win после [PR571](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/571) показывает, что MERGED pinned-index implementation может оставить неверные elevations и вернуть success. Нельзя выдавать PR571 за проверенную AC29 реализацию.
- [PR423](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/423) исправляет отрицательный story index и сообщает AC28 live; это уже готовый upstream fix, но его присутствие в загруженном 1.5.10 не проверено. Повторная реализация запрещена.
- [#481](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/481) AC29 CHE Mac 5003 и [#399](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/399) AC29 JPN Win 4006 — разные исходы Window/Door (призрачный GUID против явного BADPARS), не подтверждение одинаковой ошибки в Win build5101.
- [#439](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/439), [#686](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/686) — аварии AC28 Mac; не переносить автоматически на локальный AC29. [PR694](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/694) MERGED, автор отмечает unbuilt/untested.
- [#681](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/681) AC29 CZE Win 3000 описывает SaveProject/3D; [PR683](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/683) MERGED, unbuilt/untested. Не считать fixed in installed.
- [PR785](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785) merged 2026-10-11, direct Composite Slab — более поздний upstream. Закреплённый APA 1.5.10 catalog по [№2 09Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T09Z-report.md) не содержит этих CREATE полей.
- [#1217](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1217), [#1218](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1218), [#1223](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1223) — OPEN feature requests, не новые готовые команды. Готовый штатный [AC29 Library Manager](https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-43.htm) проверяется отдельно.
- [SDK29 Opening](https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_element_1_1_opening.html) относится к Opening-tool, а не автоматически к hosted CreateWindows/CreateDoors.

**Итог A01:** подтверждены SOURCE-факты и существующие штатные диагностические маршруты; LOCAL_INSTALLED_NOT_VERIFIED, LIVE_NOT_RUN, ACCEPTED=0. Два ложных вывода исключены: MERGED→INSTALLED и external bug→local bug. Лицензия Tapir tag1.5.9 MIT, это не свидетельство runtime.

## A02 — применимость к BUILD-01, недублирование и контроль актуального №2

**Вопрос:** устраняют ли семь карточек реальные blockers issue #192, не заменяя существующие PR74/SceneWriter вторым исполнителем?

**Прямая сверка:** [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) требует G0→G5; [очередь P0](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md) прямо запрещает новый writer. Прочитан свежий [инженерный отчёт №2 09Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T09Z-report.md): 
1. G2 Slab — уже существует SceneWriter CreateSlabs→GUID→readback→ModifySlabs→readback, но нужны **две отдельные санкции на WRITE**; PR149 floorIndex==0 нельзя применять ко второму этажу. Наш C04 только уточняет holes/сложность batch, не создаёт adapter.
2. G2 Beam — NativeAdapter('CreateBeams') существует, но в run_project подключается лишь roof adapter; без явного opt-in Beam может попасть в UNSUPPORTED_WRITE_RECIPE. Это статический блокер №2, не воспроизведённый OFFLINE; №1 не дублирует его кодом.
3. G4 BeamSegment — возможен финальный GUID diff mismatch, если child GUID возвращаются GetAllElements. Требуется installed read-only enumeration, а не автоматическое предположение.
4. G4 GetModelDumpV1 отсутствует в pinned 262-командном каталоге; AABB не BREP. Нельзя объявлять полную геометрическую приёмку.
5. G1 authored-project offline CLI может быть отвергнут; фактический read-only preflight PR74 пока не запускался.

**Негативная проверка применимости:** IFC, Hotlink, DXF/PDF, MEP, SAF, Publisher в текущем issue #192 не названы доказанными блокерами первой двухэтажной модели; исследования по ним не замещают P0. Не предлагать замену PR34/48/74/126/131/149/162, CloneNativeGroupV1 и SceneWriter.

**Реестр матрицы:** прямо прочитаны priority_matrix_20261018.json (Git blob 9cb5e6f2a59f80762cc77073eeb10404829af75a) и candidates.json (blob 87ee1c0b66233bf713e273b8b7cd00eff3a422f9); у обоих count/total=61, массивы длиной 61. Важность карточек 0–100 — экспертная, не benchmark.

**Итог A02:** G0 BLOCKED; G1 NOT_RUN/SOURCE_ONLY; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4 NOT_RUN; G5 NOT_RUN. Следующее адресное действие №2 — runtime identity и schema, затем read-only PR74 preflight и строгая проверка двух WRITE scopes Slab. **Ни одно ворото не PASS.**

## Контроль неизменности

Исторический PROJECT_PLAN.json rev182 прочитан по commit 049576378c961c5d7a9a62611f4091e3da70d309, 91 задача, без изменений. Opera Connector проверен: Browser not connected; пользовательские вкладки не затронуты. Исходный код, main, PLN/APX, установки, LIVE, Work/Codex/Arena, PR merge не изменялись/не запускались.

MODEL_MODE_NOT_VERIFIABLE.
