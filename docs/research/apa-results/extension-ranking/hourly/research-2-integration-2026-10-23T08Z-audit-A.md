# Контрааудит A — контракты провайдера против writer | 08Z

**Независимая ось:** schema drift и fail-closed native mutations; это статический аудит, не тест.

1. Пинованный `Tapir 1.5.10` catalog, Git blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`, команда `CreateSlabs` version `1.0.3`: свойства `favoriteName,level,thickness,referencePlaneLocation,polygonCoordinates,polygonArcs,holes,floorIndex`; **нет** `structureType/buildingMaterialId/compositeId`. `ModifySlabs` version `1.4.0` имеет `slabsWithDetails[].elementId/structureType/thickness/buildingMaterialId`. Это разные команды/разные write permissions.
2. Независимо прочитан upstream `ENZYME-APD/tapir-archicad-automation` main: `AddOnVersion.hpp` blob `83856d53b18c4a63887474a50cb7db504b6d0741` объявляет `1.7.3`; `ElementCreationCommands.cpp` blob `ef5423a1c602b615793f28c1fe4ca1a60f1328c8` уже содержит `CreateSlabs.structureType/buildingMaterialId/compositeId`. **Вывод:** provider schema evolved; перенос полей 1.7.3 в pinned 1.5.10 без проверки установленного APX запрещён. Версия `1.7.3` — upstream source, не факт установленного релиза.
3. В `SceneWriter` blob `484c600a205192d5737e124f8d47c8583e07a9f3` строки 976–1010 вторая мутация `ModifySlabs` выполняется после записи `BASIC_MODIFY_ATTEMPTED`, но approval_record permission=`CreateSlabs`. Наличие журналирования не является самостоятельным разрешением второй операции. До LIVE: две явные authorizations и негативный OFFLINE-кейс.
4. В схеме `CreateWindows/CreateDoors` обязательны только `ownerWallId,centerOffset`; SceneWriter обращается к `width/height/sillHeight`. Этот факт уже опубликован в 07Z: не выдавать за новое открытие 08Z.
5. Лицензия upstream Tapir: MIT, Git blob `1cdb2cb904b53c3e5d004d801e28b3ccaa00d9dd`. Файл `LICENSE` для APA в PR162 ветке не найден; правовой статус APA не выводить из лицензии Tapir.

**Контраргумент:** upstream 1.7.3 может упростить создание Slab напрямую. **Отклонён для BUILD-01:** exact installed 1.5.10 не доказан и установка/обновление запрещены.

**Итог A:** SOURCE_CONFIRMED; OFFLINE=BUILD=INSTALLED=LIVE=ACCEPTED=0. Критерий снятия G2: immutable installed schema + explicit Create/Modify scopes + independent material readback. [Pinned schema](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json) · [Upstream source](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/archicad-addon/Sources/ElementCreationCommands.cpp).
