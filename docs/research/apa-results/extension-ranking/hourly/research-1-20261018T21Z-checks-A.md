# APA №1 21Z — доказательства A: проверки 01–10
Статус: SOURCE; никакие OFFLINE/BUILD/INSTALLED/LIVE не запускались.

01. **План:** канон `docs/research/apa-results/control/PROJECT_PLAN.json`, ветка `research/apa-verified-results-hub-20261010`, blob c2ab2f9d, revision182, 91 задача; A11.S03 PARTIAL, A11.S08/S10 BLOCKED, A07.S03 READY. Проверка: READY не DONE.
02. **Реестр:** priority_matrix_20261018.json, blob 9cb5e6f2, 61 кандидат; IFCOPENSHELL 100 EXISTING, EZDXF 68, PYMUPDF 73, AC29-MEP 59, Publisher 73. Не benchmark.
03. **Аудитор:** audit-2026-10-18-20-tasks-1A/B.md: 8 адресных заданий; источники не заменяются поручениями.
04. **№2:** research-2-integration-2026-10-18T20Z.md blob 570b1a29: уже исследованы IFC 4D/5D, MEP, PDF provenance, mapped, Hotlink. №1 проверяет исходники и лицензии, не проектирует интеграцию.
05. **PDFVectors:** PR154 уже содержит lossless paths/Bézier, исходный 24-page PDF; Win installed-router NOT_VERIFIED. Не писать второй PDF extractor.
06. **IFC:** PR165 file-sidecar 12 routes и PR170 OBJ/GLB/world bounds. Installed sidecar ≠ native LIVE; не писать второй IFC parser.
07. **Hotlink:** PR171 single scratch LIVE saved/reopened 44→69 GUID; PR173 batch SOURCE/OFFLINE/BUILD, LIVE NOT_RUN. Gap ~316 м связан с local/world coordinate, не новый тест.
08. **Tapir upstream:** tag 1.5.9 `ProjectCommands.cpp` L1315–1383 SaveAsModuleFile, L2179–2330 CreateHotlinkNodes, L2334–2520 CreateHotlinkInstances, L2522+ ChangeHotlinkInstances. Installed 1.5.10 отдельно NOT_VERIFIED.
09. **IfcOpenShell pin:** `ifcopenshell-python-0.8.5` → commit 16723d11cab9bc8a13b4e025a00d39445ccc462e. `v0.8.5` tag отсутствует. Pinned source ≠ reproducible wheel.
10. **Windows wheel:** PyPI 0.8.5 13.04.2026 cp311 win_amd64 SHA256 a994cb398aa822b0153ace11fc19deea108706d3a10339de9ac9dc13da21076d; cp312 SHA256 7927921dbfd18024f44780880c37e48460bbca7476da3b0c2607e044b31521d5. Локальная установка и wheel→tag identity NOT_VERIFIED.

Источники:
https://github.com/dvikt33-ux/safe-bim-layer/pull/154
https://github.com/dvikt33-ux/safe-bim-layer/pull/165
https://github.com/dvikt33-ux/safe-bim-layer/pull/170
https://github.com/dvikt33-ux/safe-bim-layer/pull/171
https://github.com/dvikt33-ux/safe-bim-layer/pull/173
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp
https://github.com/IfcOpenShell/IfcOpenShell/tree/16723d11cab9bc8a13b4e025a00d39445ccc462e
https://pypi.org/project/ifcopenshell/0.8.5/

№2: source-tag/wheel/installed SHA, no duplicate writer, PR173 not LIVE.
