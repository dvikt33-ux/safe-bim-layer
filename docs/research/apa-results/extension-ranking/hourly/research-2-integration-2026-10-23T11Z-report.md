# APA №2 | 23.10.2026 11Z | BUILD-01 — инженерный SOURCE-отчёт

## Новый вклад P0: G1 можно проверить на действительно пустой scratch без GetModelDumpV1

**G1 / приоритет 100/100.** В `scripts/archicad_scene_run.py::scan_for_existing_geometry` запрос `GetModelDumpV1` вызывается **условно**, когда `Get3DBoundingBoxes` возвращает инвертированные sentinel-границы существующего элемента (например, сегмента Beam/Column). На чистой scratch PLN, где `GetAllElements.elements=[]`, цикл bounding-box пуст: этот конкретный вызов `GetModelDumpV1` не требуется. Поэтому **не следует объявлять G1 безусловно заблокированным отсутствием BREP-команды в pinned 262**. Безопасный путь: сначала подтвердить identity/port/build/Tapir, затем GetStories и **полную пустую native inventory**, после чего read-only preflight существующего компилятора PR74. Это SOURCE-доказательство возможного маршрута, **не проведённый OFFLINE_PASS**. Если inventory не пуст и обнаружены sentinel bbox, G1 остаётся `BLOCKED_NATIVE_DUMP_FALLBACK` до runtime read-only BREP.

## Дополнительный P0: G2 неполная проверка библиотечных частей Door/Window

**G2 / 99/100.** В pinned `CreateDoors/CreateWindows` имеются `favoriteName` и `libraryPartName`; `GetFavoritesByType` и `GetAvailableLibraryParts(filterByTypeId)` присутствуют. Но `SceneWriter.verify_readback` для проёмов проверяет `ownerElementId`, `ownerElementType`, `width/height/sillHeight/centerOffset`, **не сравнивает выбранный GDL library part GUID/name и Favorite**. Пример `model-first-building.json` указывает размеры и host, но не фиксирует конкретные `favoriteName/libraryPartName` для дверей/окон. Следовательно, существующая проверка подтверждает native type/host/параметры, но не детерминированный тип GDL. Минимальная адаптация: **внутри существующего read-only preflight/readback**, без нового writer, сопоставить `GetAvailableLibraryParts` + `GetFavoritesByType` и фактический `GetDetailsOfElements` GDL identity. Точная структура GDL identity именно для Door/Window в runtime **NOT_FOUND**; нельзя заявлять ACCEPTED до подтверждения.

## G2/G3: пример нельзя считать независимым от PLN

**G2 / 99/100.** В `examples/accelerator/model-first-building.json` есть буквальный `buildingMaterialId.guid=63db2ce9-903d-45c0-b93c-b3c604c77394` в nativeComponents Walls/Roof, а `wallBasicMaterialName` разрешается отдельно. Для нового scratch нельзя считать GUID переносимым: перед G3 необходимо read-only `GetAttributesByType(attributeType=BuildingMaterial)`, сравнить точный GUID/имя для каждого явно указанного компонента и пересчитать план/hash в новой утверждённой версии задания. Исходный fixture не изменять.

**G3/G4 / 100/100.** Пример содержит `nativeGeometryAudit=true` и `nativeRoofJunctions=true`. В `run_project` для nativeRoofJunctions/structuralFunctions до WRITE запрашивается `GetModelDumpV1`, а `archicad_authored_geometry.run` требует его после WRITE. В pinned 262 команда отсутствует. **Это не значит, что её нет в локально загруженном APX**. До G3 — runtime command registration/read-only body capability. Не снимать audit flags молча: любое изменение требований — отдельное новое задание и новый plan hash. Не выполнять WRITE ради схемы.

## Путь G0–G5

| Gate | Текущее доказательство | Минимальный следующий безопасный шаг |
|---|---|---|
| G0 | SOURCE_ONLY, INSTALLED_UNKNOWN | Готовый `archicad_runtime_version_probe.py`: GetProjectInfo/GetProductInfo/GetAddOnVersion/GetStories; отдельно PID→loaded APX path/SHA256 и registration, без native WRITE. |
| G1 | SOURCE_ROUTE_IDENTIFIED, NOT_RUN | Новый пустой scratch, GetAllElements=0, typed DAG/storyBindings/host graph/plan hash, read-only preflight. |
| G2 | SOURCE_ONLY, 2 blockers | Slab Create+Modify требует двух разрешений; GDL identity Door/Window и все literal material GUID — точный readback. |
| G3 | NOT_AUTHORIZED | Никаких записей без owner-approved scratch/port/plan hash; отдельный scope каждой мутации. |
| G4 | BREP_NOT_PROVEN | GuardedSave, GUI close/reopen, независимый native body/host/material/child GUID readback. |
| G5 | NOT_RUN | Второе новое задание + новая разрешённая scratch PLN; CLI сейчас поддерживает только два фиксированных scratch пути. |

**Статусы этого прохода:** SOURCE=30 прямых предметных проверок; OFFLINE=0, BUILD=0, INSTALLED=0, LIVE=0, ACCEPTED=0. Экспертные баллы не являются benchmark. PR74/126/131/162 переиспользуются; второй writer/router/Clone не создавались. 06Z остаётся PARTIAL_NOT_ACCEPTED: 4 оригинальных приложения на месте, исходного основного текста нет. Не менялись NEXT, main, PLN/APX, код; не было установки, PR merge, LIVE. **MODEL_MODE_NOT_VERIFIABLE**.

**Лицензия:** upstream Tapir — MIT ([официальный репозиторий](https://github.com/ENZYME-APD/tapir-archicad-automation)); лицензия собственного APA автоматически не наследуется. В upstream релизе 1.7.2 от 19.10.2026 появился `Get3DGeometryOfElements`, но это **не** команда локальной 1.5.10 и не проверенная замена BREP ([releases](https://github.com/ENZYME-APD/tapir-archicad-automation/releases)). Никакой установки/обновления не рекомендовано как часть G0.
