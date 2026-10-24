# APA №2 · SOURCE 01–15 · BUILD-01 · 21.10.2026 02Z

Фактически прочитанные issue/файлы/immutable Git blobs в этом цикле. Только SOURCE; ни одного запуска Archicad. Каждый пункт — отдельная проверка, не тест установленного APX.

**01 · P0 #192.** Шесть ворот G0–G5; G3 требует отдельного допуска, G5 — второе задание; исторический прототип не принимается за универсальный BUILD-01.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/issues/192

**02 · NEXT priorities.** Новые OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0; №2 отвечает за способы подключения, №3 за независимый аудит.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md

**03 · Матрица 61.** Фактический blob 9cb5e6f2; 61 кандидатов, формула 12*need+7*(5-effort)+confidence; это экспертная полезность, не benchmark.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json

**04 · Отчёт №1.** Blob 3614b672: SOURCE 28, DevKit 29.3000 Graphisoft EULA; новые готовые Hotlink-интерфейсы не снимают G0.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261019T18Z.md

**05 · Аудит №3.** Blob 40742adb: 30 SOURCE, два контрааудита, нулевые новые строительные стадии.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-07.md

**06 · Контрааудит №3.** Blob 75b635cf: PR160 только PDF candidate, PR191 Slab ограничен, binary SHA локального Tapir не доказан.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-07-cross.md

**07 · PR34 building-shell.** BUILD.step() создаёт по одному элементу; opening(ownerWallId) использует $createdGuid, 1–3 этажа.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/34/head/scripts/archicad_building_shell.py

**08 · PR48 reconciliation.** Историческая попытка верхнего Slab имела z/level mismatch; восстановление требует exact GUID, SQLite, инвентаризации.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/48/head/scripts/reconcile_apa_isolated_authored.py

**09 · PR74 authored plan.** compile_candidate формирует Slab каждого этажа и Walls по bearingLines, проверяет реальный GetStories и материал.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/74/head/scripts/archicad_authored_native_plan.py

**10 · PR74 accelerator.** compile_authored_intent разрешает только CreateColumns/Doors/Windows/Walls/Roofs в nativeComponents; обязательной coverage-проверки полного здания нет.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/74/head/scripts/archicad_project_accelerator.py

**11 · PR74 SceneWriter.** guarded_project без required_story требует active story 0/floorId 1/level 0; run_project вызывает его до компиляции.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/74/head/scripts/archicad_scene_run.py

**12 · PR74 BIM Graph.** $createdGuid разрешается только в .guid, производитель должен создать ровно один элемент; host ownerWallId обязан ссылаться на Wall.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/74/head/scripts/archicad_bim_graph.py

**13 · PR74 authored extension.** verify_model использует readback существующих GUID и запрещает неразрешённое пересоздание элементов.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/74/head/scripts/archicad_authored_extension.py

**14 · PR74 пример.** model-first-building.json закреплён под APA_Isolated_Writer_Test_01.pln, содержит два этажа; не готовое новое задание BUILD-01.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/74/head/examples/accelerator/model-first-building.json

**15 · PR82 Roof.** rectangle_recipe квалифицирует GABLE/HIP, требует native source Roof и ограничения угла; не универсальный Roof.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/82/head/scripts/archicad_native_roof_editing.py

Контроль: SOURCE=15 записей; OFFLINE=BUILD=INSTALLED=LIVE=ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.
