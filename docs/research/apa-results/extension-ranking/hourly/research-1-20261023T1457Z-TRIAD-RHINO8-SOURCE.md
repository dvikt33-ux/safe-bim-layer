# APA №1 — 23.10.2026 14:57Z — 28 SOURCE-проверок, Rhino 8/GH, triad
**Scope:** 28 отдельных проверяемых технических утверждений; НЕ 28 независимых URL, НЕ локальные тесты. Официальные первоисточники McNeel/Graphisoft, отдельно помеченные сообщения McNeel/Graphisoft Community. Изучение публичной документации не устанавливает факт установки или работоспособности на Windows-хосте.

## Content Cache, Rhino 8 — C01–C10
**Официальный feature:** https://www.rhino3d.com/features/grasshopper/content-cache/; **описание контракта компонента:** https://www.rhino3d.com/docs/grasshopper/Rhino/Content-Cache/; **подробная инструкция разработчика в McNeel Forum от 17.05.2024:** https://discourse.mcneel.com/t/content-cache-updated-guide/181883 (прямо предупреждает: описываемая реализация требует Rhino 8.8 Release Candidate; совместимость с конкретным локальным SR НЕ ПРОВЕРЕНА).
C01. Content Cache является штатной новой функцией Grasshopper для Rhino 8, не отдельным платным расширением.
C02. Обновляет объекты в Rhino через кеш вместо обязательного удаления и нового Bake.
C03. Контракт входов: Name, Content, Action; выходов: Name, Content, Result (официальный компонент).
C04. Action принимает Push, Pull, Bake, Purge, а также Boolean/default; без Action нет оснований считать транзакцию выполненной.
C05. Push отслеживает объекты Rhino и может заменять их без создания дубликатов (описание McNeel Forum).
C06. Pull получает существующие Rhino-объекты и их Rhino object ID.
C07. Bake без исходного ID может создавать новые экземпляры; при существующем ID возможна замена — нельзя объявлять Bake безусловно безопасным.
C08. Cache Name может именовать группы/варианты и служить для последующего Pull.
C09. Result постоянно Pull-ит Rhino-содержимое, если вывод включён; это накладные расходы и возможный поток изменений.
C10. Автор McNeel предупреждает, что автоматический Content Cache и множество Push/Bake ухудшают производительность; Action допускает внешнее GH управление.

## Rhino 8 Model Objects / Attributes — C11–C14
**Официальное руководство:** https://www.rhino3d.com/en/docs/guides/grasshopper/object-attributes/
C11. Model Object содержит геометрию вместе с именем, слоем и прочими Rhino-атрибутами; обычная geometry-only ссылка их не заменяет.
C12. В Rhino 8 Grasshopper есть Query-компоненты для чтения слоёв/материалов и других Rhino document types.
C13. Pass-through компоненты могут деконструировать существующие атрибуты и переопределять только выбранное поле, сохраняя прочие.
C14. Import Model позволяет извлечь transform для согласования единиц внешнего 3D файла с активным Rhino документом; это не автоматически исправляет координатную систему Archicad.

## Готовые фильтры и контроль набора объектов — C15–C21
**Официальный McNeel tutorial:** https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/
C15. Query Model Objects фильтрует Rhino объекты по Layer; wildcard * выбирает вложенные слои.
C16. Group Content группирует объекты по User Text, включая Building ID.
C17. Group Content Values возвращает уникальные значения ключа, пригодные для QA состава.
C18. Match Text Filter проверяет пользовательские поля, например Use Type = Office.
C19. Greater Than Filter проверяет числовой атрибут на нижнюю границу.
C20. Smaller Than Filter проверяет числовой атрибут на верхнюю границу.
C21. Intersection Filter объединяет ограничения через логическое AND; Filter Content отдаёт только совпавшие объекты. Пример McNeel: 31 поверхность → 5 при трёх критериях. Это НЕ проверка нормативных СП и не readback Archicad.

## User Text, Blocks, interoperability — C22–C28
**Официальные McNeel:** https://www.rhino3d.com/features/grasshopper/usertext/, https://www.rhino3d.com/en/features/grasshopper/blocks/; **Graphisoft download:** https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/; **Graphisoft Community roof case:** https://community.graphisoft.com/t5/Parametric-design/Updating-existing-Roof-Components-instead-of-creating-new-ones/td-p/592049.
C22. Rhino 8 GH UserText-компонент может добавлять текстовые метаданные объектам Rhino.
C23. Тот же компонент может менять и удалять Rhino UserText; ключи можно использовать для APA provenance, но это только пользовательские данные, не native Archicad GUID.
C24. Rhino 8 GH Blocks поддерживает создание определений блоков и экземпляров.
C25. GH Blocks сохраняет атрибуты Rhino при размещении/импорте; не является Archicad GDL Library Part или native Wall/Door.
C26. Model Object/Query и Import Model вместе позволяют готовыми узлами организовать выбор геометрии по атрибутам и преобразование единиц; обратная AC синхронизация этим НЕ доказана.
C27. Официальный Graphisoft download на 23.10.2026 показывает Grasshopper–Archicad 29 Live Connection build3000 для Windows, Rhino7/8; несовместим с Start Edition. Локальное наличие и точная сборка НЕ ПРОВЕРЕНЫ.
C28. Graphisoft Community, март 2024, описывает пользовательский случай пересоздания Roof с новым GUID при изменении AC-колонн; один участник предложил отключать Synchronize на время AC-правки. Это COMMUNITY_REPORT, НЕ официальная гарантия поведения AC29 и НЕ проверка BUILD-01.

## Граница доказательств
Официально подтверждено: Rhino 8 ↔ Grasshopper обновление/чтение Rhino объектов и атрибутов; готовые фильтры и метаданные; официальный GH→AC bridge для поддерживаемых BIM типов. НЕ подтверждено: Rhino GUID == Archicad GUID, сохранение AC GUID при любой перестройке GH, автоматический arbitrary AC→GH→Rhino→AC sync, целостность GDL/SEO/host, транзакционный rollback, нормативный PASS. Локальные OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=NOT_RUN/NOT_RUN/UNKNOWN/NOT_RUN/NOT_RUN.
