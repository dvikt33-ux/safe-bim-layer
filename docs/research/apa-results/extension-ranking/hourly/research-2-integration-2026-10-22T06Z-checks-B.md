# APA №2 — 2026-10-22T06Z — SOURCE-проверки 16–30
Все файлы реально прочитаны через GitHub fetch_file. PR162 head f7c37b84b76c040c417ccd58a5543326e50f673a, PR74 head 5a3a9201a715a5528c93bed4a5318e2acb32eea7, PR149 head 4c119428e9b1c24bd00774c91a6f33cbf26f0369, PR126 head f12aeba017ecd34a13989998f0b7700f6a0107d2.

16. **PR162 scripts/archicad_authored_extension.py** — blob edeaf3a875aad63da405ff844a3d5dfb2f2b4e49 — authored readback и host floor binding.
17. **PR162 archicad-addon/Sources/ModelDumpCommands.cpp** — blob c47f12b894dec28d2251b9a18d06678e73603808 — GetModelDumpV1 native implementation; 3D view/filters can constrain geometry evidence.
18. **PR162 schemas/accelerator/functional-modules.json** — blob 84e18ef18e91a8ecdd4a322f9e07aba81eeeb719 — модули и границы геометрических данных, не installed schema.
19. **PR162 schemas/tapir-live-1.5.10/tapir-scene-live.json** — blob e8ad53b6ea7c19dc34cbdcb723a79be995639cd7 — точный pinned provider schema; GetProjectInfo returns isUntitled/isTeamwork/projectLocation/projectPath/projectName, НЕ dirty/readOnly; GetModelDumpV1 и IsAddOnCommandAvailable в каталоге отсутствуют; CreateSlabs без material/structure fields.
20. **PR162 examples/accelerator/model-first-building.json** — blob e192fbb31bc872d751c41aa7132f0a4981755051 — старый fixture, не новая модель BUILD-01.
21. **PR74 scripts/archicad_project_accelerator.py** — blob 8e0ce2fbb5441009925f0d9199e180e8670a5eea — compiler whitelist без beams, есть roof.
22. **PR74 scripts/archicad_scene_run.py** — blob ca91c1cfc41cee763c62d1f3a70337d74fbafd53 — созданный GUID один на шаг, preflight/scratch guard, GetAllElements({}) не универсальный inventory.
23. **PR74 scripts/archicad_authored_native_plan.py** — blob f57812f29c826bc48ce3c6ffd0f9b6a7dc628a7d — typed DAG, GetStories/story bindings, проверка высот.
24. **PR74 scripts/archicad_authored_extension.py** — blob e6d5bbf760c82e934b194205edd0fb133d2212fa — hosted elements/roof verification.
25. **PR74 examples/accelerator/model-first-building.json** — blob e192fbb31bc872d751c41aa7132f0a4981755051 — fixture неизменён в PR162; запрещено выдавать за новый BUILD-01.
26. **PR149 scripts/apa_ac29_existing_create_verifiers.py** — blob fff474a2213cb8adfc9306c1e344e8afe60949ea — scoped verifier не универсальный CREATE; Slab material fields не в pinned create contract.
27. **PR126 scripts/archicad_dynamic_commands.py** — blob a11d91b4205a8a31d56f531982cb89fbe7cc713f — packed create, не тот же single GUID contract.
28. **research-1-20261021T22Z-BUILD01-A.md** — blob 31c0f51821592788164879f6d2a7d8e7e5af579a — проверка SetStories/верхнего этажа; read-only и контроль высот обязательны.
29. **audit-2026-10-20-14-cross1.md** — blob e61195b6eb3ab010a8b2b76fec39c2bc042f2bb0 — независимая проверка CreateSlabs/ModifySlabs и floorId vs ifcId.
30. **research-2-integration-2026-10-20T06Z-sha-manifest.json** — blob 40a6682ffc82fd4b0775f90812d935313a586740 — 7 файлов 06Z; checks-B восстановленный индекс, не исходный оригинал.

**Вне числа 30**: официальный upstream Tapir LICENSE (MIT, copyright 2024 Enzyme APD) прочитан; APA LICENSE и LICENSE.md в корне PR162 не найдены (404), следовательно APA license=NOT_VERIFIED. scripts/archicad_guarded_save.py PR162 не найден (404), не считать это доказательством отсутствия GuardedSave в других файлах.

**Критическая граница:** provider 1.5.10 schema != installed APX binary/schema. Ни один SOURCE readback не доказывает G0/G1/G2 LIVE.