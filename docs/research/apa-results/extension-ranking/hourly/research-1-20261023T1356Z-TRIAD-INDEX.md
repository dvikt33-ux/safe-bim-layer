# APA №1 — 23.10.2026 13:56Z — новое для Archicad29 + Rhino8 + Grasshopper

## Реальное влияние на BUILD-01
Новых ворот не закрыто. G0 BLOCKED (локальный PLN/port/APX/GH plugins/library build не считаны), G1 NOT_RUN, G2 SOURCE_ONLY, G3 NOT_AUTHORIZED, G4/G5 NOT_RUN. Нативное новое здание не создавалось.

Новые полезные SOURCE-результаты: Graphisoft GH Property Settings+Element Classification позволяют задавать BIM-поля до native create; GDL GLOB_ID не равен внутреннему GUID; Rhino8 GrasshopperPluginList даёт готовую инвентаризацию G0; бесплатный Hops позволяет переиспользовать GH-функции, но не доказан как AC writer; FloorPlan6 AGPL-3.0 имеет CP-SAT+Tapir, однако README/CONTRIBUTING противоречат о native Walls/Doors, STATE фиксирует неверную AC instance/story; FloorPlan4 Windows APX не прошёл end-to-end; Magnetizing GH создаёт curves, не native BIM.

## Доказательства
- [30 проверок](research-1-20261023T1356Z-TRIAD-SOURCE.md)
- [7 новых карточек](research-1-20261023T1356Z-TRIAD-CARDS.md)
- [2 контрааудита](research-1-20261023T1356Z-TRIAD-AUDITS.md)

## Поручения №2
I1356-01: G0 read-only AC build/edition, projectPath, port, active story для каждой AC инстанции; library build; Rhino PackageManager Installed и GH PluginList; Live Connection build3000 и Tapir1.5.10.
I1356-02: GH Property Settings+Classification→native AC readback матрица типов и полей, не объявлять СП проверенными.
I1356-03: раздельный userId/nativeGuid и before/after/reopen GUID/host/SEO invariant.
I1356-04: Hops только GH compute/preflight, отдельный единственный native writer; HOPS_AC_WRITE=NOT_PROVEN.
I1356-05: FloorPlan6 exact upstream code contract против README/CONTRIBUTING/STATE, без запуска, решить REJECT/KEEP_SOURCE.
I1356-06: FloorPlan4 и Magnetizing — только SOURCE qualification, не устанавливать.

## Ограничения
Прочитаны NEXT_RESEARCH_PRIORITIES.md, TRIAD-PIVOT, №1 13Z, issue #192, PR #74. №2/№3 по проверенным путям не найдены, матрица 61 не прочитана, PROJECT_PLAN rev182 не изменён. Нельзя заявлять автоматическую symmetric three-way GUID-preserving sync. Нет нового writer, изменений main/PLN/APX/кода, установок, LIVE, merge, платных API. MODEL_MODE_NOT_VERIFIABLE.