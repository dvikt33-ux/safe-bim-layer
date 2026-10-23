# APA №2 | 11Z | Контрааудит B — полна ли проверка native Doors/Windows?

**Гипотеза:** успешные `CreateDoors/CreateWindows` + `SceneWriter.verify_readback` уже доказывают конкретный библиотечный тип и материал.

**Проверка:** pinned `CreateDoors/CreateWindows` поддерживают `favoriteName/libraryPartName`; `model-first-building.json` для окон/дверей не фиксирует их. `SceneWriter.verify_readback` проверяет `ownerElementId`, `ownerElementType` и четыре размерно-позиционных поля, **не** `libPart/ownUnID.guid`, `favoriteName` или материал. `archicad_selected_library_part.resolve` имеет проверку `documentName/guid`, но ограничена `filterByTypeId='Object'`; нельзя объявить её готовым Door/Window verifier.

**Контрапример:** два разных библиотечных окна одинакового размера и host удовлетворят текущему readback, но не требованию точной GDL-идентичности. Это логическая граница проверки, не утверждение о дефекте установленного Tapir.

**Вердикт:** `G2_DOOR_WINDOW_GDL_IDENTITY_NOT_PROVEN`; минимальная адаптация — расширить только existing read-only preflight/readback, используя готовые GetAvailableLibraryParts/GetFavoritesByType и подтверждённое в runtime поле libPart для Door/Window. До такого подтверждения **NOT_FOUND**, без тестового CREATE. Slab двойная санкция остаётся отдельным P0 blocker.
