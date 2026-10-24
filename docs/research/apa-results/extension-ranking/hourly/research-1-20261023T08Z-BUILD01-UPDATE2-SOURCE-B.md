# APA №1 — BUILD-01 | 2026-10-23 08Z | Дополнение UPDATE2 | SOURCE-B (S16–S30)

Контрааудит приоритетен: закрытый issue может быть отозванным (#1042), а merged PR не доказывает installed APX. Документы AC29 Graphisoft имеют proprietary terms, Tapir MIT, лицензия APA не установлена. Все сведения только SOURCE.

### S16 — G4: Доказывает ли issue о пропавших углах стен ошибку floorPlanPolygons?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1042
**Версия/лицензия/статус:** AC29 build3200 AUT/Tapir 1.7.1; CLOSED; MIT
**Факт/поля:** Автор ОТОЗВАЛ репорт: проверил 119 составных стен и 25 L-углов; дополнительные маленькие полигоны были пропущены в первоначальном анализе.
**Решение/ограничение → №2:** Не считать defect и не создавать обход. №2: при union floorPlanPolygons учитывать все малые полигоны и реальное положение окон.

### S17 — G4: Можно ли безопасно автоматизировать OpenProject без знания dirty-state?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1381
**Версия/лицензия/статус:** Tapir 1.7.2, AC28 build7006 INT Windows11; OPEN; MIT
**Факт/поля:** GetProjectInfo не сообщает hasUnsavedChanges; OpenProject поверх открытого файла может молча потерять несохранённую стену (воспроизведено на AC28).
**Решение/ограничение → №2:** Не переносить как доказанный AC29 дефект. №2: fail-closed при неизвестном dirty-state, только GuardedSave и отдельный GUI-close/open допуск.

### S18 — G0/G1: Можно ли штатно создавать новый PLN из заданного template через Tapir?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/issues/928
**Версия/лицензия/статус:** AC29 DevKit API, Tapir request OPEN; MIT
**Факт/поля:** Предлагается NewProject через ACAPI_ProjectOperation_NewProject(newAndReset); template path параметром не принимается, используется UI New Project settings; команда в Tapir отсутствует.
**Решение/ограничение → №2:** Нельзя считать способом детерминированно открыть новый scratch из нужного шаблона. №2: заранее утверждённая saved scratch PLN + SHA, без NewProject.

### S19 — G4: Есть ли у Get3DGeometryOfElements buildingMaterialId для каждого тела?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1256
**Версия/лицензия/статус:** AC29 requested, Tapir 1.7.2/1.7.3 request OPEN; MIT
**Факт/поля:** Body3D содержит vertices/polygons/surfaceId, но не per-body buildingMaterialId; ACAPI_ModelAccess_GetBuildingMaterial требует separate-components sight.
**Решение/ограничение → №2:** Не выводить Building Material из surfaceId и агрегированных количеств. №2: материал читать по элементу/компоненту отдельно; при отсутствии per-body mapping ставить NOT_VERIFIED.

### S20 — G4: GetCollisions может отличить чистый L-стык от наложения?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1093
**Версия/лицензия/статус:** AC29 AUT/Tapir 1.7.1; OPEN; MIT
**Факт/поля:** Для правильно состыкованных двух стен GetCollisions сообщил hasBodyCollision=true; предложен ACAPI_ModelAccess_GetConnectionTable, ещё не доступен в Tapir.
**Решение/ограничение → №2:** Не считать collision=true браком без анализа контакта. №2: использовать reference lines, материал, floorPlanPolygons, и сохранять статус junction NOT_VERIFIED.

### S21 — G2: Достаточна ли optional-схема при создании свойств?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1402
**Версия/лицензия/статус:** Tapir 1.7.0/1.7.2, AC27/29/30 macOS; OPEN; MIT
**Факт/поля:** CreatePropertyDefinitions без defaultValue отклонялось, хотя schema помечает optional; ошибка -2130313104.
**Решение/ограничение → №2:** Это не обязательная команда BUILD-01; схема не гарантия runtime. №2: не создавать новые свойства в первой модели, использовать уже существующие definitions.

### S22 — G2: Можно ли при CreateWalls/Slabs/Columns/Beams назначить layerIndex одним вызовом?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/issues/1043
**Версия/лицензия/статус:** Tapir upstream main 2026-10-17; OPEN; MIT
**Факт/поля:** layerIndex отсутствует в перечисленных Create*; элемент наследует layer из defaults/Favorite; предлагается отдельное назначение.
**Решение/ограничение → №2:** Не считать post-CREATE layer автоматически правильным. №2: preflight ожидаемый слой vs template Favorite и independent readback; отдельную mutation только по разрешению.

### S23 — G2: Что фактически хранит Favorite и зависит ли от шаблона?
**Источник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-56.htm
**Версия/лицензия/статус:** Graphisoft Archicad 29 INT; proprietary; official
**Факт/поля:** Favorites сохраняются в проекте, включают размеры, классификации/свойства, имя library part; Transfer Sets определяют перенос дополнительных настроек.
**Решение/ограничение → №2:** №2: зафиксировать точную scratch template, имена Favorites, GDL библиотеку; Favorite name не тождественен library part name.

### S24 — G4: Может ли Partial Structure Display изменить наблюдаемый состав модели?
**Источник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/050_ViewsVB/050_ViewsVB-94.htm
**Версия/лицензия/статус:** Graphisoft Archicad 29 INT; proprietary; official
**Факт/поля:** Entire Model, Without Finishes, Core Only, Core of Load-Bearing Elements Only скрывают разные части composite/complex; настройка привязана к окну/виду.
**Решение/ограничение → №2:** №2: для визуальной/геометрической сверки фиксировать режим; не трактовать скрытые Finish skins как отсутствующие native элементы.

### S25 — G2: Можно ли назначить Composite Slab, не проверяя Use With?
**Источник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/025_Attributes/025_Attributes-27.htm
**Версия/лицензия/статус:** Graphisoft Archicad 29 INT; proprietary; official
**Факт/поля:** Composite выбирается для Wall/Slab/Roof/Shell только когда Use With включает данный тип; Partial Structure Display влияет на отображение.
**Решение/ограничение → №2:** №2: проверять composite availability и толщину до CREATE; CREATE→MODIFY — две отдельные санкционированные записи.

### S26 — G2: Универсальны ли параметры окон/дверей во всех локализациях?
**Источник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/150_UserInterfaceToolSettings/150_UserInterfaceToolSettings-16.htm
**Версия/лицензия/статус:** Graphisoft Archicad 29 INT; proprietary; official
**Факт/поля:** Наборы библиотек, панели Custom Settings и маркеры окон/дверей различаются по library/localization; документация описывает INT как основу многих языковых версий.
**Решение/ограничение → №2:** №2: не копировать параметры INT в JPN/RUS/AUT без installed library check; readback GDL + marker отдельно.

### S27 — G0: Разрешает ли лицензия Tapir повторное использование исходников?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/LICENSE
**Версия/лицензия/статус:** Tapir MIT; LICENSE Git blob 1cdb2cb904b53c3e5d004d801e28b3ccaa00d9dd
**Факт/поля:** MIT разрешает использование/изменение/распространение с сохранением notice; не является лицензией Graphisoft Archicad SDK или гарантом бинарной совместимости.
**Решение/ограничение → №2:** №2: переиспользовать штатные функции, не устанавливать/пересобирать APX; права на чужие GDL пакеты отдельно.

### S28 — G0: Какую версию сообщает upstream main, а не локальный APX?
**Источник:** https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/archicad-addon/Sources/AddOnVersion.hpp
**Версия/лицензия/статус:** Tapir MIT; blob 83856d53b18c4a63887474a50cb7db504b6d0741
**Факт/поля:** В исходнике ADDON_VERSION "1.7.3"; это не доказательство версии фактически загруженного Windows APX 1.5.10.
**Решение/ограничение → №2:** №2: PID→loaded APX path→SHA256→GetAddOnVersion→command registration, не смешивать версии.

### S29 — G0/G2: Есть ли зафиксированная схема локальной 1.5.10?
**Источник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json
**Версия/лицензия/статус:** APA PR162 pinned f7c37b8; blob e8ad53b6ea7c19dc34cbdcb723a79be995639cd7; license NOT_CONFIRMED
**Факт/поля:** Каталог содержит GetAddOnVersion и множество command schema, но он сохранённый snapshot, а не выгрузка текущего loaded APX.
**Решение/ограничение → №2:** №2: сравнить реальные registered commands и локальные required поля с snapshot; несовпадение = G0 BLOCKED.

### S30 — G2: Есть ли в SceneWriter скрытая вторая Slab mutation после Create?
**Источник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py#L976-L1025
**Версия/лицензия/статус:** APA PR162 pinned f7c37b8; blob 484c600a205192d5737e124f8d47c8583e07a9f3; license NOT_CONFIRMED
**Факт/поля:** После CreateSlabs при basic_guid выполняется ModifySlabs со structureType Basic/thickness/buildingMaterialId, отдельным BASIC_MODIFY_ATTEMPTED intent.
**Решение/ограничение → №2:** №2: отдельные scope CreateSlabs и ModifySlabs + независимый material readback; журнал не заменяет permission.
