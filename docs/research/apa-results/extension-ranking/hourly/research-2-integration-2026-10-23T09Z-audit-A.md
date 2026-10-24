# Контрааудит A — G2 cross-story Slab: «готово» против фактического кода | 09Z

**Независимый предмет:** создаваемый Slab, native material и floor1. Проверены три разных слоя: pinned Tapir schema (blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`), SceneWriter (blob `484c600a205192d5737e124f8d47c8583e07a9f3`), PR149 material-only verifier (blob `6499cac9bb2f1a9ee942a4578a21798d5cca788c`).

1. `CreateSlabs` v1.0.3: `slabsData[].level/polygonCoordinates` обязательны; `floorIndex/thickness/favoriteName` допустимы; `structureType/buildingMaterialId/compositeId` **отсутствуют**. Нельзя послать материал напрямую.
2. `ModifySlabs` v1.4.0: `slabsWithDetails[].elementId` обязателен, `structureType/thickness/buildingMaterialId` допустимы. Это **отдельная нативная запись**.
3. SceneWriter строки 976–1014 **уже реализует** `CreateSlabs → GUID → GetDetails → BASIC_MODIFY_ATTEMPTED в SQLite → ModifySlabs → GetDetails`. Источник `floor=params['slabsData'][0]['floorIndex']`, **нет ограничения story0** в этом пути. Значит для двух этажей не нужен новый slab writer.
4. Однако `apa_ac29_existing_modify_verifiers.details_for` строка 45 имеет **`floorIndex == 0`**, а `VerifiedBasicSlabMaterial` требует один существующий самостоятельный Basic Slab, не зависимый. Этот verifier **не годится** для изменения story1. **НЕ** маршрутизировать весь BUILD-01 через него.
5. Серьёзная граница допуска: SceneWriter фиксирует `BASIC_MODIFY_ATTEMPTED` до `ModifySlabs`, но в `approval_record` разрешение связано с `CreateSlabs`. Журналирование второй операции не заменяет отдельное разрешение владельца на Create+Modify. До LIVE подтвердить политику двойного scope и отрицательный OFFLINE-кейс.
6. `GetDetailsOfElements` доказывает материал/толщину, но не closed BREP; pinned 262-command catalog не содержит `GetModelDumpV1`. Поэтому **G2/G4 не PASS**.

**Контргипотеза:** если project Favorite уже создаёт нужный Basic Slab, ModifySlabs может быть избыточен. Но существующий путь PR74 всё равно делает MODIFY при наличии `slabBasicMaterialGuid`; менять поведение без отдельной ревизии не разрешено.

**Результат:** NEW PRACTICAL ROUTE CLARIFICATION, SOURCE_CONFIRMED; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED = 0. **Приоритет 99/100**. Следующий шаг: read-only installed schema и отдельный fail-closed preflight для обоих write scopes. Источник: [SceneWriter](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py), [PR149](https://github.com/dvikt33-ux/safe-bim-layer/blob/4c119428e9b1c24bd00774c91a6f33cbf26f0369/scripts/apa_ac29_existing_modify_verifiers.py).
