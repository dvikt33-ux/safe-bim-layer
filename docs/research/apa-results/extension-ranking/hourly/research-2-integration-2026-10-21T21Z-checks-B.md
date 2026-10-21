# APA №2 — BUILD-01 | SOURCE 16–30 | 2026-10-21T21Z

30 адресных проверок в цикле, только чтение. PR metadata и исходники — SOURCE, не LIVE.

**16 — PR131.** Slab CREATE без материала, host/story/Favorite для проёмов. [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/75ae71dc60176225bb71928fb805e5adcc688b2e/docs/research/apa-results/execution-optimizer/AUTO_DISCOVERY_V2.md).

**17 — PR149.** Scoped floorIndex=0, не второй этаж. [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/4c119428e9b1c24bd00774c91a6f33cbf26f0369/scripts/apa_ac29_dynamic_native_verifiers.py).

**18 — PR150.** Pinned healthcheck/hashes, не запускался. [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/8fbb311fc2f25fb8b2b6ff432e74d4e31b4c93fc/scripts/release_apa_ac29_six_verifiers.py).

**19 — PR151.** Историческая установка ≠ текущий INSTALLED. [Источник](https://github.com/dvikt33-ux/safe-bim-layer/pull/151).

**20 — PR154.** PDFVectors отдельно. [Источник](https://github.com/dvikt33-ux/safe-bim-layer/pull/154).

**21 — PR159.** Группы на другом PLN/порту. [Источник](https://github.com/dvikt33-ux/safe-bim-layer/pull/159).

**22 — PR160.** PDF→OpenBIM не BUILD-01. [Источник](https://github.com/dvikt33-ux/safe-bim-layer/pull/160).

**23 — PR162 core.** inventory_guids по-прежнему GetAllElements({}). [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py).

**24 — PR162 Dynamic.** prewrite current inventory = affected∪retained; область не доказана. [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_dynamic_commands.py).

**25 — PR162 groups.** COPYABLE Column/Beam/Object; CREATE Column/Beam. [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/apa_ac29_group_strategy.py).

**26 — G0 probe.** READ_ONLY_VERSION_CHECK даже при несовпадении build; нет APX SHA/command inventory. [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_runtime_version_probe.py).

**27 — Story contract.** Запрет hardcode floorIndex; nativeIndex/floorId/level. [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/docs/FULL_CYCLE_PROJECT_GOAL_AND_STORY_CONTRACT.md).

**28 — Favorite contract.** Favorite/Transfer Set требуют material/composite readback. [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/docs/archicad-template/FAVORITE_CONTRACT_v0.1.md).

**29 — Pinned schema.** CreateSlabs v1.0.3: 8 полей, без structureType/buildingMaterialId. [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/4c119428e9b1c24bd00774c91a6f33cbf26f0369/schemas/tapir-live-1.5.10/tapir-scene-live.json).

**30 — Upstream Tapir.** Публичные releases 1.5.9→1.6.0 без 1.5.10; MIT; локальный APX не идентифицирован. [Источник](https://github.com/ENZYME-APD/tapir-archicad-automation/releases).

Upstream MIT: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/LICENSE. Отдельного upstream 1.5.10 release в публичном списке не найдено; это не доказывает отсутствие локального бинарника.
