# APA №1 | 2026-10-23 12Z | AC29 + Rhino8 + Grasshopper | SOURCE-проверки

Результат: 30 отдельных проверок **разных инженерных вопросов**, не 30 независимых сайтов. Повторное использование одного официального руководства явно указано. Уровень SOURCE не означает INSTALLED/LIVE. Все действия ниже — задания №2, не выполненные операции. Лицензирование: официальная Graphisoft страница даёт дистрибутив; лицензии базовых AC/Rhino не подтверждены в рамках исследования; Rhino.Inside — open source; не заявлять «полностью бесплатно».

## S01 — Версия соединения
**Вопрос BUILD-01:** Версия соединения.
**Первоисточник:** https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
**Версия/факт:** Для AC29 build5101 + Rhino8 существует официальный Live Connection 29 build3000 (Windows 16.8 MB; 01.10.2025).
**Статус/ограничение:** SOURCE; факт доступности дистрибутива, не установки.
**Адресное задание №2:** №2: проверить фактическое наличие и build add-on через Add-On Manager только READ.

## S02 — Лицензионное ограничение
**Вопрос BUILD-01:** Лицензионное ограничение.
**Первоисточник:** https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
**Версия/факт:** Live Connection не поддерживает Archicad Start Edition; стандартный AC29 требуется. На странице доступна загрузка, но условия лицензирования Rhino/AC отдельно не проверены.
**Статус/ограничение:** SOURCE; бесплатная загрузка не означает бесплатные базовые лицензии.
**Адресное задание №2:** №2: подтвердить редакцию Archicad и легальные лицензии Rhino8/AC29.

## S03 — Нативный BIM GH→AC
**Вопрос BUILD-01:** Нативный BIM GH→AC.
**Первоисточник:** https://community.graphisoft.com/t5/Modeling/Grasshopper-Archicad-Live-Connection/ta-p/304037
**Версия/факт:** Graphisoft описывает создание и управление BIM-элементами непосредственно из Grasshopper; GH не просто экспортирует меш.
**Статус/ограничение:** SOURCE; перечень гарантированных типов ограничен компонентами установленной версии.
**Адресное задание №2:** №2: составить таблицу фактических Design Components AC29 без предположений.

## S04 — Обратное чтение AC→GH
**Вопрос BUILD-01:** Обратное чтение AC→GH.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/GC.pdf
**Версия/факт:** AC29 guide: Deconstruct получает геометрию существующих вручную размещённых AC-элементов; не доказано редактирование того же GUID.
**Статус/ограничение:** SOURCE; AC→GH read, не полный write-back.
**Адресное задание №2:** №2: раздельно тест-план readback Wall/Slab/Beam и редактирование исходного GUID.

## S05 — Сохранение настроек при производном моделировании
**Вопрос BUILD-01:** Сохранение настроек при производном моделировании.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/GC.pdf
**Версия/факт:** Extract Settings разбирает параметры входного элемента, а Settings назначает параметры нового элемента.
**Статус/ограничение:** SOURCE; копирование настроек ≠ изменение исходного элемента.
**Адресное задание №2:** №2: построить существующий узловой маршрут AC reference→Extract Settings→новый GH Design, сравнить GUID.

## S06 — Динамические атрибуты
**Вопрос BUILD-01:** Динамические атрибуты.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/GC.pdf
**Версия/факт:** Input-компоненты AC29 дают обновляемые списки Composite, Building Material, Favorite, Layer, Surface, Profile, Story Plane, Hotlink Module и др.
**Статус/ограничение:** SOURCE; значения берутся из открытого AC, а не из универсального каталога.
**Адресное задание №2:** №2: привязать материальные/этажные параметры BUILD-01 к AC Input, а не жёстким GUID.

## S07 — Этажные отметки
**Вопрос BUILD-01:** Этажные отметки.
**Первоисточник:** https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564
**Версия/факт:** Story Plane input позволяет получить отметки этажей AC как плоскости для кривых Wall/Slab/Beam.
**Статус/ограничение:** SOURCE; правильность Home Story всё равно требует readback.
**Адресное задание №2:** №2: задать две Story Plane и сравнить actual story index/elevation.

## S08 — Composite Slab/Roof/Wall
**Вопрос BUILD-01:** Composite Slab/Roof/Wall.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/GC.pdf
**Версия/факт:** Composite Input существует в AC29 guide; для native composite нужны Settings соответствующего инструмента, а не материал поверхности Rhino.
**Статус/ограничение:** SOURCE; наличие composite input не доказывает все операции создания Roof/Slab.
**Адресное задание №2:** №2: зафиксировать поддерживаемые Composite/StructureType для каждого GH Design Component.

## S09 — Favorites из AC
**Вопрос BUILD-01:** Favorites из AC.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/GC.pdf
**Версия/факт:** Favorite Input — штатный источник параметров, обновляемых из проекта Archicad.
**Статус/ограничение:** SOURCE; Favorite имя/параметры не тождественны GDL library identity.
**Адресное задание №2:** №2: сравнить выбранный Favorite, фактическую библиотечную часть и тип элемента.

## S10 — Hotlink Module input
**Вопрос BUILD-01:** Hotlink Module input.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/GC.pdf
**Версия/факт:** AC29 guide перечисляет Hotlink Module среди Input-компонентов.
**Статус/ограничение:** SOURCE; это не доказательство автоматического обновления .3dm и нативной типизации.
**Адресное задание №2:** №2: проверить сценарий только как reference, отдельно от native BUILD-01.

## S11 — Ориентация балок/колонн
**Вопрос BUILD-01:** Ориентация балок/колонн.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/GC.pdf
**Версия/факт:** AC29 guide включает Beam/Column Sorter для линейных структур независимо от ориентации.
**Статус/ограничение:** SOURCE; не доказана геометрия всех сегментированных AC29 beam/column.
**Адресное задание №2:** №2: определить роль готового Sorter в GH-сборке каркаса и контроль нулевой длины.

## S12 — Rhino mesh→AC Morph
**Вопрос BUILD-01:** Rhino mesh→AC Morph.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/GC.pdf
**Версия/факт:** AC29 guide: Morph Solid принимает Mesh, Morph Curve — Curve; результат — нативный Morph, не Roof/Wall/Slab.
**Статус/ограничение:** SOURCE; нативный Morph не равен конструктивному BIM-типу.
**Адресное задание №2:** №2: резервировать Morph только для свободной формы/деталей, не для обязательных стен.

## S13 — Morph материал и слой
**Вопрос BUILD-01:** Morph материал и слой.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/GC.pdf
**Версия/факт:** Morph Settings в AC29 guide содержит Building Material, Layer, ID, Structural Function, Position, Renovation Status, Property Settings.
**Статус/ограничение:** SOURCE; метаданные не превращают Morph в Roof/Slab.
**Адресное задание №2:** №2: проверить фактический material/ID/property readback после авторизованного прогона.

## S14 — Контроль BREP→Mesh
**Вопрос BUILD-01:** Контроль BREP→Mesh.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/GC.pdf
**Версия/факт:** AC29 guide рекомендует Mesh-Brep converting component для ограничения числа полигонов Morph.
**Статус/ограничение:** SOURCE; конверсия может терять аналитическую точность.
**Адресное задание №2:** №2: документировать допуски объёма/границ/триангуляции, не применять для точных стен.

## S15 — Транзакционный переключатель
**Вопрос BUILD-01:** Транзакционный переключатель.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/GC.pdf
**Версия/факт:** AC29 guide: у всех Design/Document генераторов Boolean Synchronize; TRUE синхронизирует, FALSE не общается и отдаёт Null.
**Статус/ограничение:** SOURCE; FALSE не равно откату/удалению ранее созданных AC-элементов.
**Адресное задание №2:** №2: использовать Boolean Toggle как явный ручной write gate после проверки inputs.
