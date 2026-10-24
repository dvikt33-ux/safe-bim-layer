# APA №2 — BUILD-01 · 18Z · SOURCE 16–22

16. [PR74 story binding](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py#L24-L88): authored heights 2.4–4.5 м, уровни tolerance 1e-5 и точное nativeStoryBindings. Только SOURCE.
17. [PR74 Slab](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py#L840-L925): ATTEMPTED→CreateSlabs→typed readback→BASIC_MODIFY_ATTEMPTED→ModifySlabs→readback. Не повторять CREATE после UNKNOWN.
18. [Pinned CreateSlabs](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/schemas/tapir-live-1.5.10/tapir-scene-live.json#L2873-L2959) v1.0.3: favoriteName/level/thickness/polygon/floorIndex, без structureType/buildingMaterialId.
19. [Pinned ModifySlabs](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/schemas/tapir-live-1.5.10/tapir-scene-live.json#L5379-L5455) v1.4.0: slabsWithDetails, material/structure/thickness; требуется installed schema.
20. [PR149 verifier](https://github.com/dvikt33-ux/safe-bim-layer/blob/4c119428e9b1c24bd00774c91a6f33cbf26f0369/scripts/apa_ac29_existing_modify_verifiers.py#L20-L70): только elementId/structureType/buildingMaterialId, floorIndex=0; несовместим с PR74 Slab pipeline как есть.
21. [Tapir tag1.5.9 CreateSlabs](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp#L348-L413): Favorite, без прямого материала. Не доказательство APX1.5.10.
22. [Tapir GetBuildingMaterials](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AttributeCommands.cpp#L2403-L2478): GUID/index/name и поэлементные ошибки; read-only квалификация материалов.

OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0.