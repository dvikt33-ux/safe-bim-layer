# APA №2 — 23.10.2026 11Z — SOURCE-проверки S01–S15

**Метод:** 26 отдельных GitHub fetch_file на immutable PR162 commit `f7c37b84b76c040c417ccd58a5543326e50f673a` и 4 отдельных read-only обращения к документам/issue. Файлы с кодом прочитаны, ключевые ветви дополнительно просмотрены по строкам. SOURCE не равен OFFLINE/LIVE.

**S01** — [`scripts/archicad_scene_run.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py); blob `484c600a205192d5737e124f8d47c8583e07a9f3`. G1: scan_for_existing_geometry вызывает GetModelDumpV1 лишь при инвертированном 3D bbox; при пустом GetAllElements цикл не выполняется. G2: ModifySlabs вызывается после санкции CreateSlabs без отдельной permission.

**S02** — [`scripts/archicad_dynamic_commands.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_dynamic_commands.py); blob `c05017ee3d082feebea96d804dbd6a3bd26680e7`. probe_runtime использует API.IsAddOnCommandAvailable: подтверждает регистрацию, не локальную схему; packed create требует независимого readback.

**S03** — [`scripts/archicad_bim_graph.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_bim_graph.py); blob `87fc7476c9079a189c8b8e31ae3c6beaf6712dd3`. Проверяет $createdGuid, hostWall и fit/overlap для прямых стен, но не библиотечные части и не фактический физический проём.

**S04** — [`scripts/archicad_authored_native_plan.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_authored_native_plan.py); blob `a9d8cb844a862ea92aed955fae999ddcc418eb86`. compile_candidate создаёт Walls/Slabs по реальным storyBindings; дополнительные Roof/Doors/Windows поступают через nativeComponents.

**S05** — [`scripts/archicad_authored_extension.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_authored_extension.py); blob `edeaf3a875aad63da405ff844a3d5dfb2f2b4e49`. verify_model проверяет тип/этаж/host; изменение модели поддерживает лишь ограниченный набор параметров, не универсальное редактирование.

**S06** — [`scripts/archicad_authored_geometry.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_authored_geometry.py); blob `f43fc5b04e90e0e7a85f3f780da8153e73066243`. run требует GetModelDumpV1 и GetCollisions; это отдельная native-геометрическая приёмка, не AABB.

**S07** — [`scripts/archicad_project_accelerator.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py); blob `439f6d26ce097cdfdfc33a2b5a245352073151f2`. run_project подключает typed adapter только при CreateRoofs; nativeGeometryAudit и nativeRoofJunctions могут потребовать GetModelDumpV1.

**S08** — [`scripts/archicad_connected_components.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_connected_components.py); blob `c5a99f59a90369ff622807574677cf11ca0a2225`. Roof verify использует typed details (SinglePlane Basic, material, pivot), Beam verify дополнительно требует GetModelDumpV1 и дочерние BeamSegment.

**S09** — [`scripts/archicad_native_material_selection.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_native_material_selection.py); blob `f66a1b34fe28191cc3ada97e2dc8e2a317eebc40`. Материал/Composite/Surface для Walls разделены по доступным полям; нельзя приписывать CreateWalls неподдержанные поля.

**S10** — [`scripts/archicad_runtime_version_probe.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_runtime_version_probe.py); blob `c76e394b8ea1c9128ad3e34e93f3ebf09d3b543a`. Готовый read-only inventory: GetProjectInfo/GetProductInfo/GetAddOnVersion/GetStories, без локального APX SHA и регистрации команд.

**S11** — [`scripts/archicad_batch_contracts.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_batch_contracts.py); blob `4afbe545360f919209f086f2d3cd13e573d13393`. Батч-контракты включают CreateWalls/Slabs/Beams/Columns; список команд не равен разрешению SceneWriter на запись.

**S12** — [`scripts/apa_ac29_dynamic_write_scopes.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/apa_ac29_dynamic_write_scopes.py); blob `8feec3283e5d3c04d7aaf54b3a43f7495741464a`. build_existing_workflow_scopes требует approved_project_sha, exact before GUID set, retained BREP и source-specific verifier; не обходить.

**S13** — [`scripts/apa_ac29_dynamic_native_verifiers.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/apa_ac29_dynamic_native_verifiers.py); blob `8516ebef2c6804bc83dc79724bfb234591e14aa9`. В части Column verifier присутствует floorIndex==0; не применять как универсальный валидатор двух этажей.

**S14** — [`scripts/archicad_building_shell.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_building_shell.py); blob `59bb8c24d641f550eb63abf0059b811fc10ffd59`. building-shell-v1 и source floorplates дают готовый preview; без обязательной Roof/Doors/Windows сборки это не BUILD-01.

**S15** — [`scripts/archicad_scene_v1.py`](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_v1.py); blob `5fd0292c7a9dd00caebe10408f46f26216f9cba6`. Исторический 12-элементный fixture; не повторять CREATE в пользовательском файле.
