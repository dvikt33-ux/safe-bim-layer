# APA №1 | 12Z | Два контрааудита

## Аудит A — первоисточник, версия, лицензия
1. Официальный Graphisoft download подтверждает AC29 build3000, Rhino7/8, Windows, но **не** установленную локальную версию и не поддержку любой функции AC29 build5101 в runtime.
2. Руководство https://help.graphisoft.com/AC/29/INT/GC.pdf подтверждает Deconstruct/Extract Settings/Input/Morph/Sync. Однако сам PDF web.open вернул size error (22.8MB); проверялись индексированные фрагменты официального PDF, а не непрерывное постраничное чтение. Полный постраничный аудит остаётся NOT_DONE.
3. Официальная страница Graphisoft называет соединение «bi-directional», но её же guide показывает направленные Design/Deconstruct, а сообщения практиков описывают GH ownership и перезапись AC-геометрии. Поэтому заявлять **полный symmetric multi-master sync** нельзя. https://community.graphisoft.com/t5/Modeling/Grasshopper-Archicad-Live-Connection/ta-p/304037 ; https://community.graphisoft.com/t5/Collaboration-with-other/Working-Rhino-with-Archicad/m-p/681968
4. Rhino.Inside — framework для Windows с готовым Revit-проектом, но не найден официальный готовый Rhino.Inside.Archicad AC29. Не рекомендовать разрабатывать адаптер вместо официального Live Connection. https://www.rhino3d.com/features/rhino-inside/
5. Старый GSM-LCF exporter описан как Rhino 5/AC18–20; **не** переносить этот контракт на Rhino8/AC29. https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
6. Базовые Rhino8 и Archicad лицензии не подтверждены как бесплатные; доступность download add-on не отменяет их.

**Итог A:** OFFICIAL_SOURCE для возможностей отдельных направлений; INSTALLED_UNKNOWN, LIVE_NOT_RUN, полный автоматический трёхсторонний sync NOT_PROVEN.

## Аудит B — применимость, недублирование, отказоустойчивость
1. PR74/SceneWriter остаётся единственным APA write route; GH Live Connection — второй независимый нативный **производитель элементов**, поэтому одновременное владение одним GUID создаёт риск overwrite. До разрешённого LIVE — назначить owner per element/property и запретить две записи в одну область.
2. GH Synchronize=FALSE возвращает Null, но прежние AC элементы могут остаться; нельзя трактовать FALSE как rollback. Null-reset — потенциальное удаление, отдельный scope.
3. AC29 .3dm import/hotlink создаёт GDL objects, не Wall/Slab/Roof; Rhino export теряет BIM metadata. Нельзя считать 3DM roundtrip сохранением BIM или GUID. https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-44.htm
4. Home Story определяется реальной геометрией, а unit mismatch и zero-height columns могут дать ложный 3D PASS. Для каждого элемента readback story/type/material/host/geometry.
5. Rhino8 Blocks обновляют геометрию внутри Rhino, не выполняют автоматически AC native write; использовать только там, где GH Design имеет подтверждённый native тип.
6. BUILD-01 G0 всё ещё BLOCKED: PID/APX SHA/schema/target scratch не проверены; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. В этот час никаких OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED доказательств.
7. Прочитаны NEXT_RESEARCH_PRIORITIES.md, директива TRIAD-PIVOT, №2 11Z, issue192 и rev182 (commit 0495763..., blob c2ab2f9...). №3 11Z по проверенному предполагаемому имени не найден; матрица 61 не прочитана напрямую из-за отсутствия подтверждённого пути. Не утверждать полный аудит этих двух ресурсов.

**Итог B:** ближайший практический маршрут — GH official native generator с AC29 source-of-truth и readback через существующий APA, без универсального multi-master. Проверить безопасно сначала в режиме SOURCE/read-only; любое LIVE — только отдельный допуск.
