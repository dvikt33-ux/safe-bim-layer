# APA №2 — контрааудит A: G0/G2, SOURCE

A1. Pinned `tapir-scene-live.json` PR162: `provider_version=1.5.10`, `origin=live TapirCommand.GenerateDocumentation`, `binding.port=19723` и другой тестовый PLN. Снимок не доказывает SHA реально загруженного APX и его регистрацию в нужной среде.

A2. `archicad_runtime_version_probe.py` возвращает `READ_ONLY_VERSION_CHECK` при `buildMatchesUserScreenshot=false/null`; не сверяет SHA APX, командный inventory и схемы. Контрпример выведен из кода, не запущен на Windows.

A3. В закреплённом `CreateSlabs.slabsData[]` отсутствуют `structureType/buildingMaterialId`; в `ModifySlabs.slabsWithDetails[]` они присутствуют. PR131 предлагает Favorite с проверенным `settingsHash`. Нельзя выдавать схему провайдера за установленную и нельзя проверять WRITE ради чтения схемы.

A4. `GetProjectInfo` возвращает isUntitled/isTeamwork/projectLocation/projectPath/projectName, но не dirty/readOnly. Автоматический Close/Reopen без независимого GUI guard запрещён.

Итог: G0 BLOCKED, материал Slab G2 BLOCKED до installed read-only contract и разрешённого native readback. SOURCE_ONLY, тестов 0.
