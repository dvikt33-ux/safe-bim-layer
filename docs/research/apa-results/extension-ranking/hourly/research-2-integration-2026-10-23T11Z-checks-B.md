# APA №2 — 23.10.2026 11Z — SOURCE-проверки S16–S30

**Метод:** 26 отдельных GitHub fetch_file на immutable PR162 commit `f7c37b84b76c040c417ccd58a5543326e50f673a` и 4 отдельных read-only обращения к документам/issue. Файлы с кодом прочитаны, ключевые ветви дополнительно просмотрены по строкам. SOURCE не равен OFFLINE/LIVE.

**S16** — [`scripts/archicad_semantic_spatial.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_semantic_spatial.py); blob `5cfcfa1ee016703b1d2bf672a2af288901c0229d`. compile_spatial формирует геометрию/ограничения из brief; не подтверждает несущую пригодность.

**S17** — [`scripts/archicad_semantic_brief.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_semantic_brief.py); blob `e431016f796bb8052487478dde3b2ed2752e7c00`. resolve_stories использует реальный GetStories; нельзя угадывать nativeIndex из порядка этажей.

**S18** — [`scripts/archicad_project_library_pack.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_library_pack.py); blob `b6053b93d9956bcbfd22a528f4f5750e07e9f5a7`. compile_pack разрешает конкретный BuildingMaterial по имени/GUID; источник CSE и инженерная применимость остаются предварительными.

**S19** — [`scripts/archicad_native_roof_editing.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_native_roof_editing.py); blob `91daaf8af881df5ba0cbddc09721bc92a54879c9`. CreateRoofs typed fields: level/floorIndex/thickness/structureType/buildingMaterialId/pivotLine; нативный Roof не универсален.

**S20** — [`scripts/apa_ac29_group_strategy.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/apa_ac29_group_strategy.py); blob `153bc1e353f3a0dd363a7bbcc23cb6d692b5ff3e`. Групповые операции сохраняют локальные SceneWriter permissions; не дублировать CloneNativeGroupV1.

**S21** — [`scripts/apa_ac29_scoped_native_executor.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/apa_ac29_scoped_native_executor.py); blob `0b4ae56febc909f53e19340e25b8bf20c5f6fd87`. Нативные операции требуют approved saved SHA, sceneId, authorizationRef и typed/BREP readback; не второй writer.

**S22** — [`scripts/apa_ac29_scene_reconciliation.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/apa_ac29_scene_reconciliation.py); blob `aa8b7fc92eb5a49fab7f48007c19cdbd20f6f6fd`. При UNKNOWN использовать read_only_reconciliation и native signatures, без автоматического повторного CREATE.

**S23** — [`scripts/archicad_execution_optimizer.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_execution_optimizer.py); blob `1219edcab8dddb511a5de7159084ec5df11ba09b`. Оптимизатор допускает эффекты READ_ONLY/CREATE/MODIFY, но не создаёт самостоятельного права на LIVE.

**S24** — [`examples/accelerator/model-first-building.json`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/examples/accelerator/model-first-building.json); blob `e192fbb31bc872d751c41aa7132f0a4981755051`. Готовый двухэтажный source intent содержит nativeComponents Door/Window/Roof; пример фиксирует material GUID и nativeGeometryAudit=true, nativeRoofJunctions=true.

**S25** — [`examples/accelerator/isolated-authored-project.json`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/examples/accelerator/isolated-authored-project.json); blob `cbc7822d505d92a8b19ef09745ac580782098a01`. Изолированный authored fixture; target PLN/исторические данные нельзя автоматически переносить на новый scratch.

**S26** — [`schemas/tapir-live-1.5.10/tapir-scene-live.json`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json); blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`. 262 команды; CreateSlabs не имеет structureType/buildingMaterialId, ModifySlabs имеет; GetModelDumpV1 отсутствует; CreateWindows/Doors имеют favoriteName/libraryPartName.

**S27** — [Issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192). P0 G0–G5, новая scratch PLN, отдельная санкция G3; read-only.

**S28** — [NEXT priorities](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md). blob 6f074693360231c5cb42ada815984a6b0dd504c0; приоритет BUILD-01, NEXT только чтение.

**S29** — [Матрица 61](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json). blob 9cb5e6f2a59f80762cc77073eeb10404829af75a; count=61, не новые приёмочные испытания.

**S30** — [Исторический PROJECT_PLAN](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/control/PROJECT_PLAN.json). blob c2ab2f9d606db1412c4031076103c267fc463f83; revision=182, read-only.
