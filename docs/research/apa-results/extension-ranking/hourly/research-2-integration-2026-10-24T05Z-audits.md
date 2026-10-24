# APA №2 | 2026-10-24 05Z | Два документарных контрааудита

**Статус:** SOURCE_ONLY. Это две самостоятельные проверки гипотез, выполненные исследователем №2, **не** независимое заключение исследователя №3 и **не** LIVE.

## Контрааудит A — «Один IFC-BREP достаточно для native BIM acceptance?»

**Контргипотеза:** экспорт BREP воспроизводит junctions, значит по одному IFC можно подтвердить GUID, native Roof, материал и параметры. **ОПРОВЕРГНУТО.**

1. AC29 Geometry Conversion: BREP точен для поверхностей и junctions, но IFC representation теряет редактируемые параметры; Parametric сохраняет часть параметров, но не гарантирует сложные стыки. Источник https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-37.htm .
2. AC29 Built-in IFC Type Mapping: Roof и Shell при by Element Type оба `IfcSlab.ROOF`; при by Classification тип зависит от translator. Источники https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-51.htm ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-35.htm .
3. Data Conversion: Building Material, Component Parameters и Door/Window properties опциональны; IFC2x3 и IFC4 размещают material properties по-разному. Отсутствие IFC-поля не доказывает отсутствие native свойства. Источник https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-42.htm .
4. Geometry Conversion: split composites может создавать container+parts; у контейнера может не быть собственного BREP. Источник https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-37.htm ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-48.htm .

**Вердикт A:** G4 = native GUID/Tool/material readback + IFC-BREP geometry + отдельно IFC-parametric/native parameters; preset signature обязателен. Одно IFC не ACCEPTED. Сценарий пока SOURCE_PROPOSED.

## Контрааудит B — «Два IFC файла + GH Live Connection = полноценная трёхсторонняя синхронизация?»

**Контргипотеза:** после обновления GH достаточно экспортировать два IFC, сравнить IfcGlobalId, и можно автоматически принять изменение/откат во всех трёх программах. **ОПРОВЕРГНУТО.**

1. IFC — экспортные представления из Archicad, не обратный редактор Rhino/GH и не транзакция SceneWriter. IFC Story GlobalId может совпасть между разными PLN при одинаковых Building ID/Story Number. Источник https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-48.htm .
2. PR74 `apa-authored-project/1` проверяет target PLN и разрешает ограниченный nativeComponents; GH-owned elements вне единого SceneWriter. Источник immutable PR74 `5a3a9201...`, scripts/archicad_project_accelerator.py lines 262–311.
3. GH–AC29 Live Connection — отдельный writer для поддержанных native элементов; его присутствие не доказывает единый rollback, conflict resolution, cycle suppression и GUID preservation между Rhino, GH, Archicad. Источник https://help.graphisoft.com/AC/29/INT/GC.pdf (официальное руководство, в этом проходе PDF не извлекался заново) и https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/ .
4. IFC Space Containment не применяется к Wall/Window; отсутствие relation не означает потерю hosted opening. Space Boundaries и IfcRelVoids/IfcRelFills требуют отдельных проверок. Источник https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-42.htm .
5. Любое удаление, повторное создание или UNKNOWN write outcome → STOP и native reconciliation. Undo Rhino и Undo Archicad не общий атомарный rollback; при отсутствии сохранённой scratch копии статус BLOCKED.

**Вердикт B:** два IFC профиля — независимая QA, не синхронизация. Full 3-way atomic commit/conflict resolution = **NOT_FOUND**. Новых G0–G5 PASS нет.
