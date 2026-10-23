# APA №1 — 2026-10-23 13:56Z — SOURCE checks
30 отдельных технических проверок, НЕ 30 независимых URL. Документы Graphisoft, McNeel и авторские репозитории; SOURCE не равен локальному INSTALLED/LIVE. PDF AC29 22,8 MB полностью постранично не открыт: использованы официальные индексированные фрагменты.
## Graphisoft S01–S12
S01. Graphisoft AC29 GH Live Connection build3000, Rhino7/8, Windows, дата 01.10.2025. https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
S02. Add-on не поддерживает Archicad Start Edition. Тот же источник.
S03. AC29 guide требует последнюю обновлённую AC29. https://help.graphisoft.com/AC/29/INT/GC.pdf
S04. Перед установкой новой GH-AC Connection требуется удалить прежнюю версию. Тот же guide.
S05. Rhino7/8 должен быть 64-bit. Тот же guide.
S06. AC29 Property Settings GH component имеет выход Property Settings для 3D element Settings. Тот же guide, индексированный фрагмент стр.49.
S07. Второй выход Element Classification; Wall Settings включает Composite, Layer, ID, Structural Function, Renovation Status и Property Settings. Тот же guide, стр.49.
S08. GDL GLOB_ID — пользовательский ID. https://help.graphisoft.com/AC/29/INT/GDL.pdf
S09. GDL GLOB_INTGUID — внутренний GUID, не контролируется пользователем; user ID не доказывает native identity. Тот же GDL guide.
S10. Archicad 29.2.1 FULL build5101 выпущен 28.07.2026. https://www.graphisoft.com/en-us/downloads/?gssubtype=archicad&gstype=downloads&product=archicad&section=update
S11. Graphisoft рекомендует проверять build глобальных библиотек отдельно от AC build. https://support.graphisoft.com/hc/de/articles/25007835463697-Zusammenarbeit-auf-der-BIMcloud-Archicad-Version (04.08.2026).
S12. Для Teamwork Graphisoft рекомендует совпадение версии, build и локализации; это не утверждение о solo scratch. Тот же support.
## McNeel S13–S23
Первичный документ: https://developer.rhino3d.com/guides/compute/hops-component/ , обновлён 28.10.2024.
S13. Hops работает с Rhino7/8 Windows, отдельный GH component.
S14. Hops оборачивает внешнее .gh определение в функцию с input/output, пригодно для повторного использования.
S15. Hops поддерживает асинхронное решение внешних GH документов.
S16. Hops поддерживает параллельное решение; это НЕ безопасность параллельных native AC writes.
S17. Hops имеет Enabled input; gate вычисления не является AC транзакцией.
S18. Hops Cache In Memory сохраняет результаты, которые нельзя приравнивать к актуальному readback AC.
S19. Hops по умолчанию запускает локальный Rhino.compute; дополнительный процесс/среда.
S20. Официальный FAQ: Hops free to use; лицензия Rhino8 отдельно.
S21. FAQ допускает GH plugins внутри Hops Function, но GH-AC GUI/live connectivity в отдельном compute НЕ доказана.
S22. Rhino8 GrasshopperPluginList и -GrasshopperPluginList перечисляют зависимости текущего GH определения: https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm .
S23. Rhino8 GrasshopperLoadOneByOne диагностирует загрузку проблемных GH plugins; GrasshopperIgnorePlugin изолирует: тот же документ.
## Оригинальные проекты S24–S30
S24. FloorPlan6 README заявляет Tapir AC27/28/29, CP-SAT и экспорт Zones/Walls/Doors/Windows/Labels. https://github.com/poolpet/floorplan6/blob/main/README.md ; blob 6ab43a22bbc31e5c59b44bf4af0c8ed759dcf7fd.
S25. FloorPlan6 CONTRIBUTING одновременно утверждает «currently we export Zones only» — конфликт источников, не присваивать ACCEPTED native walls. https://github.com/poolpet/floorplan6/blob/main/CONTRIBUTING.md ; blob 01b9c5342e6c0f2e9dd960617221f8926be5cc8b.
S26. FloorPlan6 STATE фиксирует две AC инстанции 19723/19724 и unresolved active-story/target problem. https://github.com/poolpet/floorplan6/blob/main/docs/STATE.md ; blob ad0c12a9ae911078ea205c29638eebb2ddbaf872.
S27. FloorPlan6 ROADMAP замораживает volumetric stage2; это НЕ готовый полный 3D-building generator. https://github.com/poolpet/floorplan6/blob/main/docs/ROADMAP_domy.md ; blob f29005fefdd33fef941a62af9d994a172531870d.
S28. FloorPlan6 AGPL-3.0; Python3.10+, OR-Tools, Shapely2, PyQt5, networkx. https://github.com/poolpet/floorplan6/blob/main/LICENSE ; blob be3f7b28e564e7dd05eaf59d64adba1a4065ac0e.
S29. FloorPlan4 GPL-3.0 experimental native AC29 walls/doors/zones, Windows APX CI wired but end-to-end install untested. https://github.com/poolpet/floorplan4/blob/master/README.md ; blob dcbe71890c38a10090e433d85c5767662abb4982.
S30. Magnetizing Floor Plan Generator GH component outputs room/corridor curves only; README Rhino6+ and license heading empty. https://github.com/hellguz/Magnetizing_FloorPlanGenerator/blob/master/README.md ; blob 468b6c9ae267f44c165c455c61703d5100306e70.
## Count
30 проверок утверждений на 10+ оригинальных документах, часть повторно проверяет другой контракт того же документа. Не 30 независимых источников. Ни одного локального теста.