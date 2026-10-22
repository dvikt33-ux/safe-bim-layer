# APA №1 BUILD-01 — карточки C1–C3

## C1 — официальный Tapir AC29 Win APX, G0
[Релиз 1.7.2 от 19.10.2026](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.7.2), MIT. Артефакт 5 914 112 байт, SHA256 `4714fcbfadb47307b0b3cecf578fe18ff326f3c06ee0b8e7db5a31a979a01bf7`. Вход: PID, локальный APX. Выход: сравнение версии/хеша. Ограничение: не доказано наличие APA-команд; установки запрещены. №2: фактический loadedApxSha256 и command registration. Статус DEFER/SOURCE.

## C2 — GetQuantitiesOfElements, G4
[PR860](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/860), 1.7.2, MIT. Вход: GUID, minOpeningSize. Выход: quantities/errors и composite skins/material. AC29 сборка заявлена, LIVE указан лишь AC30. Интеграция: дополнительная проверка Slab/Wall/Roof, не Window/Door. №2: не ставить в критический путь до runtime. Статус OPTIONAL_SOURCE.

## C3 — Get3DGeometryOfElements, G4
[PR865](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/865), 1.7.2, MIT. Вход: GUID. Выход: vertices/faces/holes/surfaceId, GH Mesh (не BREP). PR unbuilt/untested, subelement completeness не доказана. Интеграция: только дополнительный mesh oracle; GetModelDumpV1 не заменять. №2: отложить до отдельного runtime proof. Статус DEFER.
