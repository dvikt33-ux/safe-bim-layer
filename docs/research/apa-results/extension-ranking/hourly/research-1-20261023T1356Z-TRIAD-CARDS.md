# APA №1 — 2026-10-23 13:56Z — 7 новых карточек
Все SOURCE_ONLY; лицензия/версия/направление/ограничение/задание №2 для каждой. Новые после 13Z.

## N01 — GH Property Settings и Classification | P0
Операция BUILD-01: native BIM стены/колонны/перекрытия со свойствами. Готовое: официальный Graphisoft GH–AC Live Connection AC29 build3000, GH Property Settings→element Settings→Synchronize, выход Element Classification. Контракт: Wall Settings имеет Layer, ID, Composite, Structural Function, Property Settings. Направление GH→AC, обратный arbitrary write не доказан. Первоисточники: https://help.graphisoft.com/AC/29/INT/GC.pdf стр.49 (индексированный фрагмент), https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ . Лицензия: add-on download, AC FULL/Rhino8 отдельно. Ограничение: поля ≠ проверка СП, native GUID preservation не доказан. №2: матрица полей и readback native classification/material/property; критерий G2 typed contract, затем только разрешённый LIVE.

## N02 — user ID против internal GUID | P0
Операция: доказать неизменность элемента после параметрического изменения и Save/Open. Готовое: штатные AC29 GDL GLOB_ID (пользовательский) и GLOB_INTGUID (внутренний, пользователем не управляется). Источник https://help.graphisoft.com/AC/29/INT/GDL.pdf ; лицензия: AC documentation. Направление native AC→read-only audit. Риск: совпадение ID не гарантирует GUID, host/SEO links. №2: разделить userId/nativeGuid в receipts; критерий before/after/reopen native GUID equality.

## N03 — McNeel Hops как no-code reusable GH compute | P1
Операция: повторно использовать GH геометрические определения без дублирования алгоритмов. Готовое: Hops Rhino7/8 Windows, free, .gh functions, Enabled, async/parallel. Источник https://developer.rhino3d.com/guides/compute/hops-component/ (28.10.2024). Направление GH→Rhino.compute→GH, не AC write. Риск: дополнительный процесс, кэш, неизвестная совместимость GH-AC Live Connection внутри Hops. №2: маршрут только вычисление/preflight→отдельный официальный GH-AC Sync; критерий no-second-writer, HOPS_AC_WRITE=NOT_PROVEN.

## N04 — Rhino8 GH PluginList / PackageManager Installed | P0 G0
Операция: инвентаризация реальной GH среды без программирования. Готовое: GrasshopperPluginList, -GrasshopperPluginList, GrasshopperLoadOneByOne и PackageManager Installed. Источники https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm и https://docs.mcneel.com/rhino/8/help/en-us/commands/packagemanager.htm ; лицензия: Rhino8 штатно. Направление Rhino/GH read-only. Ограничение: PluginList только для открытого GH документа, installed package ≠ loaded AC add-on. №2: G0 read-only inventory exact versions AC/Rhino/GH/Tapir/Live Connection; критерий три отдельных списка.

## N05 — FloorPlan6 CP-SAT + Tapir | P2 PARTIAL_SOURCE_CONFLICT
Операция: автоматическая планировка квартир/дома как upstream source для BUILD-01. Готовое https://github.com/poolpet/floorplan6 , Python3.10+ OR-Tools Shapely2 Tapir AC27–29; AGPL-3.0. Направление AC outline→solver→AC Zones/Wall/Door/Window (README заявляет); GH/Rhino отсутствует. Конфликт: CONTRIBUTING говорит zones only; STATE фиксирует port19723/19724 и active story bugs; 3D volumetric stage2 заморожен. №2: read-only diff конкретного writer vs docs, native schema, Windows; критерий доказать exact commit/real native types или REJECT как BUILD-01 writer.

## N06 — FloorPlan4 experimental native AC29 add-on | P2
Операция: CP-SAT квартира→native стены/двери/зоны. Готовое https://github.com/poolpet/floorplan4 , GPL-3.0, Archicad29 C++ add-on. Направление AC boundary→AC native. Ограничение: Windows .apx CI есть, end-to-end Windows install untested, добавление второго writer противоречит APA. №2: SOURCE-only сравнение алгоритма, не устанавливать; критерий REJECT или отдельно согласованный isolated pilot.

## N07 — Magnetizing Floor Plan Generator | P2
Операция: GH размещение помещений/коридоров общественного здания. Готовое https://github.com/hellguz/Magnetizing_FloorPlanGenerator , Rhino6+ заявлено, GH HouseInstance/RoomInstance/MagnetizingRooms_ES. Направление GH→curves, native AC отсутствует. Лицензия в README не указана, Rhino8 runtime неизвестен. №2: подтвердить пакет/лицензию/версию; критерий SOURCE-only и NOT_NATIVE_WRITER, при отсутствии лицензии REJECT.

Выбор: N01/N02/N04 для G0/G2; N03 только чистые вычисления; N05–N07 не обязательны для BUILD-01, не устанавливать.