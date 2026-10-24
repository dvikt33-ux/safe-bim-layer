# APA №2 · SOURCE 16–30 · BUILD-01 · 21.10.2026 02Z

Фактически прочитанные исходники 12 PR и pinned Tapir schema; статусы SOURCE_ONLY. Лицензии: Tapir upstream MIT (версия 1.5.9 по аудиту №3); DevKit29 Graphisoft EULA; внутренняя лицензия APA NOT_VERIFIED. Поставщик != установленный APX.

**16 · PR97 runtime.** GetAPARuntimeInfoV1 возвращает buildIdentity/sourceRevision/sdkMajor=29, но не SHA256 установленного APX.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/97/head/archicad-addon/Sources/NativeGridCommands.cpp

**17 · PR97 ModelDump.** GetModelDumpV1 объявляет ARCHICAD_RESULTANT_POLYGON_MODEL; ShowAllIn3D/Rebuild сохраняет layer/design-option/3D filters.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/97/head/archicad-addon/Sources/ModelDumpCommands.cpp

**18 · PR97 dependency.** apa_native_dependency_flow.py преобразует захваченные связи в существующий DependencyImpact, не новый graph engine.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/97/head/scripts/apa_native_dependency_flow.py

**19 · PR126 packed.** execute_batch: 1–200 Walls/Slabs/Beams/Columns/Windows/Doors; Roof отсутствует, SQLite before-write, один provider call.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/126/head/scripts/archicad_dynamic_commands.py

**20 · PR131 hosted.** _v2_create_row проверяет ownerWallId, nativeReadbackVerified, library qualification, story и коллизии; PDF→Wall GUID остаётся NOT_FOUND.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/131/head/scripts/archicad_strategy_discovery.py

**21 · PR149 Create.** existing_create_verifiers.py ограничен Basic story0; Beam поля точные, Roof source проверяется.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/149/head/scripts/apa_ac29_existing_create_verifiers.py

**22 · PR149 ModifySlabs.** material_request принимает только elementId/structureType/buildingMaterialId, не thickness; только Basic Slab на story0.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/149/head/scripts/apa_ac29_existing_modify_verifiers.py

**23 · PR150 bridge.** Автономный bridge закреплён под BDD WORKING/ORIGINAL и exact SHA; не универсальный BUILD-01 receiver.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/150/head/scripts/apa_ac29_autonomous_job_bridge.py

**24 · PR151 registry.** Bootstrap требует Windows, base revision/PLN SHA/298 GUID и exact local receipt; не установка нового scratch.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/151/head/scripts/apa_ac29_pinned_registry_upgrade.py

**25 · PR154 IFC/DXF.** apa_external_readonly.py переиспользует upstream IFC/ezdxf, проверяет версии, без PLN writer; отдельное направление, не G0 blocker.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/154/head/scripts/apa_external_readonly.py

**26 · PR159 group forensic.** Read-only reconciliation group-ac29-assembly-20261018-04 требует exact source/clone receipts; повтор Clone запрещён.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/159/head/scripts/apa_ac29_group_reconcile_readonly.py

**27 · PR160 AP2.** PDF-текстовые marks не геометрические anchors и не hosted Create; нужен отдельный Wall GUID/offset/story.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/160/head/scripts/apa_ap2_massops_preflight.py

**28 · PR162 groups.** workflow_for_selected собирает group-first через CreateNativeGroupV1/CloneNativeGroupV1, $result и существующий DynamicCommands.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/162/head/scripts/apa_ac29_group_strategy.py

**29 · PR175 save.** ScratchWriteLease кооперативен только между APA, preserve_guarded_save требует точный SHA; reopen Hotlink-specific.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/175/head/scripts/apa_ac29_save_isolation.py

**30 · Pinned Tapir schema.** Blob e8ad53b6: 262 documented commands, provider_version=1.5.10; НЕ доказательство установленного binary/schema.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/74/head/schemas/tapir-live-1.5.10/tapir-scene-live.json

Контроль: SOURCE=15 записей; OFFLINE=BUILD=INSTALLED=LIVE=ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.
