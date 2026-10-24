# APA №1 | 23.10.2026 10Z | BUILD-01 | 2 собственных контрааудита

## A01 — Первоисточник, версия, совместимость и фактическая зрелость

**Проверяемый тезис:** новые upstream PR 23.10 можно использовать в AC29 build5101 с локальным Tapir1.5.10 без установки.

**Контрпроверка №1: не верно.** [PR1134](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1134) объединён 10:46:57Z, `AddOnMain.cpp` регистрирует `RegularizePolygons` / `RegularizePolylines` как 1.7.2; непосредственно прочитан diff четырёх файлов, включая `PolygonCommands.cpp`, `Examples/regularize_polygons.py`. В pinned 262-command schema 1.5.10 [R2-10Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T10Z-report.md) эти команды не подтверждены. **SOURCE MERGED ≠ LOCAL INSTALLED.** Отдельного live readback в нашем окружении нет.

**Контрпроверка №2: версия PR не равна версии installed APX.** [PR1277](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1277) объединён 10:45:12Z, регистрирует 1.7.3; автор прямо указывает not built/tested in Archicad. [PR1434](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1434) merged 22.10, `ProjectHealthCheck.py` требует Python>=3.11 и tkinter, но не подтверждён как установленный builtin script в 1.5.10. Никакая новая функция не объявлена RUNTIME_READY.

**Контрпроверка №3: проверка исходников и лицензии.** Прямо прочитаны patch PR1134 (четыре файла), PR1434 (семь файлов), [upstream LICENSE](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/LICENSE), blob `1cdb2cb904b53c3e5d004d801e28b3ccaa00d9dd`: MIT. Права по MIT не доказывают совместимость binary, отсутствие DevKit ошибок или разрешение пользователя на установку.

**Контрпример:** [PR1351](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1351) TriangulatePolygonsOfElements остаётся OPEN и untested, даёт только XY triangles; даже после merge он не является BREP. [PR1395](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1395) сообщает конкретные размеры на AC29 build5101, но OPEN и относится к CreateObjects/Lamps, не доказано для 1.5.10 Windows/Doors.

**Вердикт A01:** SOURCE_CONFIRMED для upstream реализации PR1134/PR1434/PR1277, но `INSTALLED=0, LIVE=0, ACCEPTED=0` в текущем исследовании. Обязательный G0 — PID, загруженный APX path/SHA, порт, active PLN, exact runtime command schema. Официальный SDK29 не заменяется текстом PR. `MODEL_MODE_NOT_VERIFIABLE`.

## A02 — Применимость к P0 BUILD-01, недублирование, полнота G0–G5

**Проверяемый тезис:** найденные новые решения устраняют главный инженерный blocker и позволяют объявить G2/G4 PASS.

**Контрпроверка №1: фактический blocker сильнее новых функций.** [BUILD-01 issue192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) требует новое 2-этажное native здание через existing PR74 compiler/SceneWriter. [№2 10Z audit A](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T10Z-audit-A.md) установил: `SceneWriter` после разрешённого `CreateSlabs` вызывает `ModifySlabs` без второй самостоятельной проверки permission. Следовательно, **G2 = DUAL_WRITE_APPROVAL_NOT_ENFORCED / WRITE_BLOCKED**; регуляризация контура не исправляет право на MODIFY. Исследователь №1 не меняет код.

**Контрпроверка №2: отсутствие BREP.** [№2 10Z report](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T10Z-report.md): pinned `GetModelDumpV1` отсутствует, AABB `Get3DBoundingBoxes` ≠ BREP. PR1434 проверяет дубль по type/story/AABB; PR1351 предлагает 2D triangulation; PR1277 меняет параметры изображения. Ни один не закрывает G4 independent 3D geometry.

**Контрпроверка №3: новое не всегда применимо.** PR1134 — полезен лишь при реальном invalid slab polygon; BUILD-01 пока не предъявил такой вход. PR1394 (library part replacement) OPEN и требует native WRITE; missing libraries ещё не доказаны на scratch. PR1233 редактирует GDL scripts и прямо запрещён пользователем. PR1131 Drawing boxes, PR1430 Layout subset, PR1391 dimension formatting — не P0. IFC/Hotlink/DXF/PDF/MEP/SAF/Publisher не исследованы дополнительно без конкретного blocker.

**Контрпроверка №4: контекст и недублирование.** Прочитаны [NEXT_RESEARCH_PRIORITIES](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md), [матрица 61](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json) (поле count=61, не выполнялся повторный 61/61 расчёт), [№2 10Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-23T10Z-report.md), [последний найденный аудит №3 20.10 07Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-07.md), исторический [PROJECT_PLAN rev182](https://github.com/dvikt33-ux/safe-bim-layer/blob/049576378c961c5d7a9a62611f4091e3da70d309/docs/research/apa-results/control/PROJECT_PLAN.json) (revision=182, 91 tasks). История и main не изменены.

**Вердикт A02:** нет разрешения на G3; G0 BLOCKED, G1 NOT_RUN, G2 WRITE_BLOCKED/SOURCE_ONLY, G4 BREP_BLOCKED/NOT_RUN, G5 NOT_RUN. PR74/SceneWriter остаются единственным writer. Никаких 100× без benchmark. Задание №2: G0 runtime identity; G1 реальный read-only authored preflight; G2 двойное permission Slab, затем только отдельный допуск G3. Это адресные инженерные задачи, не готовая модель.

## Контроль происхождения и ограничения
- **28 отдельных SOURCE-проверок S01–S28** находятся в SOURCE-A/B; каждая имеет прямой GitHub PR/issue URL и конкретное решение/ограничение.
- Opera: две доступные связи проверены; первая вернула `Browser not connected`, вторая потребовала интерактивного подтверждения; вкладки не открывались/закрывались. Использован GitHub connector, не web-копии.
- Источники не равны LIVE. Права на code/PLN/APX/INSTALL/PR merge не запрашивались и не использовались.
