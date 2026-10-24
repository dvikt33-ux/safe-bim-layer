# APA №1 | 2026-10-23 12Z | AC29 + Rhino8 + Grasshopper | SOURCE-проверки

Результат: 30 отдельных проверок **разных инженерных вопросов**, не 30 независимых сайтов. Повторное использование одного официального руководства явно указано. Уровень SOURCE не означает INSTALLED/LIVE. Все действия ниже — задания №2, не выполненные операции. Лицензирование: официальная Graphisoft страница даёт дистрибутив; лицензии базовых AC/Rhino не подтверждены в рамках исследования; Rhino.Inside — open source; не заявлять «полностью бесплатно».

## S16 — Семантика остановки и удаления
**Вопрос BUILD-01:** Семантика остановки и удаления.
**Первоисточник:** https://community.graphisoft.com/t5/Parametric-design/Synchronize-Bug/m-p/292446/highlight/true
**Версия/факт:** Graphisoft community: отключение Sync оставляет ранее созданные элементы в AC; отдельный Stream Filter→Null обсуждён как способ удаления.
**Статус/ограничение:** COMMUNITY_SOURCE (2020), не проверено AC29; Null может привести к разрушительной записи.
**Адресное задание №2:** №2: не применять Null-reset в BUILD-01 без отдельного разрешения; описать безопасную инвентаризацию.

## S17 — Массовая синхронизация
**Вопрос BUILD-01:** Массовая синхронизация.
**Первоисточник:** https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564
**Версия/факт:** Graphisoft performance tips: при тысячах реальных BIM-элементов возможны зависания; выключать Sync на время редактирования входов.
**Статус/ограничение:** SOURCE; нет измерений именно AC29/Rhino8.
**Адресное задание №2:** №2: разделить модель на управляемые группы с отдельными toggle; benchmark позже.

## S18 — Дискретизация кривых
**Вопрос BUILD-01:** Дискретизация кривых.
**Первоисточник:** https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564
**Версия/факт:** Graphisoft tips: сложные кривые стен/балок создают избыточные элементы; рекомендуют замену дугами.
**Статус/ограничение:** SOURCE; автоматическое сглаживание может изменить геометрию.
**Адресное задание №2:** №2: измерять число Wall/Beam и отклонение исходной кривой, не менять проектную геометрию молча.

## S19 — Единицы и вырожденная геометрия
**Вопрос BUILD-01:** Единицы и вырожденная геометрия.
**Первоисточник:** https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564
**Версия/факт:** Graphisoft tips: несовпадение mm Rhino и толщины AC wall 30 cm порождает вырожденные элементы.
**Статус/ограничение:** SOURCE; проблема масштаба, не версия-specific.
**Адресное задание №2:** №2: preflight unit scale и допустимые толщины/длины до Sync TRUE.

## S20 — Нулевая высота колонны
**Вопрос BUILD-01:** Нулевая высота колонны.
**Первоисточник:** https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564
**Версия/факт:** Graphisoft tips: сдвиг списка anchor/end может породить последнюю колонну нулевой длины; убрать лишний anchor.
**Статус/ограничение:** SOURCE; необходимы проверки каждой пары точек.
**Адресное задание №2:** №2: контроль length>0, pair-count и readback перед G3.

## S21 — Home Story по геометрии
**Вопрос BUILD-01:** Home Story по геометрии.
**Первоисточник:** https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564
**Версия/факт:** Graphisoft tips: GH-created Home Story зависит от положения reference line/anchor, Morph — от минимального Z.
**Статус/ограничение:** SOURCE; этаж нельзя гарантировать одним именем Story.
**Адресное задание №2:** №2: сравнить фактические Home Story всех объектов с DAG/storyBindings.

## S22 — Выбор порта и GH документа
**Вопрос BUILD-01:** Выбор порта и GH документа.
**Первоисточник:** https://community.graphisoft.com/t5/Kollaboration-mit-anderer/Die-Grasshopper-Archicad-Live-Connection-f%C3%BCr-Archicad-26/ta-p/392707
**Версия/факт:** Graphisoft (AC26) показывает GH palette: выбрать порт проекта AC, конкретный GH документ, status и preview.
**Статус/ограничение:** SOURCE_AC26; требуется подтвердить сохранение UI в AC29.
**Адресное задание №2:** №2: сделать read-only протокол выбора target PLN/port/GH definition; не подключать к BDD.

## S23 — Конфликт ручной правки AC
**Вопрос BUILD-01:** Конфликт ручной правки AC.
**Первоисточник:** https://community.graphisoft.com/t5/Collaboration-with-other/Working-Rhino-with-Archicad/m-p/681968
**Версия/факт:** Graphisoft community 2025: GH-created элементы по умолчанию locked; после unlock геометрические правки AC могут быть перезаписаны при следующем GH update, отдельные материалы иногда сохраняются.
**Статус/ограничение:** COMMUNITY_SOURCE, не формальный контракт и не доказательство AC29 build5101.
**Адресное задание №2:** №2: зафиксировать ownership per property; провести отдельный разрешённый конфликтный тест.

## S24 — 3DM импорт не даёт Wall
**Вопрос BUILD-01:** 3DM импорт не даёт Wall.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm
**Версия/факт:** AC29 Help: Open/Merge Rhino .3dm создаёт non-editable GDL objects в Embedded Library, не стены/крыши.
**Статус/ограничение:** OFFICIAL_SOURCE_AC29; импорт ≠ полноценная нативная BIM-модель.
**Адресное задание №2:** №2: исключить обычный .3dm Import из обязательного пути native BUILD-01.

## S25 — Готовый Rhino Hotlink
**Вопрос BUILD-01:** Готовый Rhino Hotlink.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-43.htm
**Версия/факт:** AC29 Help: File>External Content>Place Hotlink принимает .3dm; модуль помещается на текущем этаже, сегментация фиксируется при вставке.
**Статус/ограничение:** OFFICIAL_SOURCE_AC29; linked reference, не GH event-driven native update.
**Адресное задание №2:** №2: использовать только для контекста/контрольной подложки, проверить ручной Update и слои.

## S26 — AC→Rhino экспорт без BIM
**Вопрос BUILD-01:** AC→Rhino экспорт без BIM.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-44.htm
**Версия/факт:** AC29 Help: экспорт .3dm передаёт геометрию/слои/цвета, но не свойства, теги, ведомости и количества.
**Статус/ограничение:** OFFICIAL_SOURCE_AC29; файл .3dm не сохраняет BIM-семантику.
**Адресное задание №2:** №2: не использовать .3dm round-trip для GUID/классификаций.

## S27 — AC→Rhino BREP/Mesh
**Вопрос BUILD-01:** AC→Rhino BREP/Mesh.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-44.htm
**Версия/факт:** AC29 Help: Hybrid экспортирует плоские поверхности как BREP, криволинейные как Mesh; Surface Model дробит разноцветный элемент.
**Статус/ограничение:** OFFICIAL_SOURCE_AC29; количество элементов и топология могут меняться.
**Адресное задание №2:** №2: геометрический QA сравнивать по группам/объёму, не по 1:1 Rhino object ID.

## S28 — Оригинальный Rhino ID при импорте
**Вопрос BUILD-01:** Оригинальный Rhino ID при импорте.
**Первоисточник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm
**Версия/факт:** AC29 Help: imported Rhino GDL Object содержит Rhino Layer и original Rhino ID как свойства.
**Статус/ограничение:** OFFICIAL_SOURCE_AC29; ID в свойствах не является автоматически стабильным AC GUID.
**Адресное задание №2:** №2: отличать Rhino original ID, AC GUID, GH reference ID и IFC GlobalId.

## S29 — Rhino.Inside не готовый AC29-мост
**Вопрос BUILD-01:** Rhino.Inside не готовый AC29-мост.
**Первоисточник:** https://www.rhino3d.com/features/rhino-inside/
**Версия/факт:** McNeel Rhino.Inside open-source Windows embedding framework, примеры Revit/AutoCAD; официального готового Rhino.Inside.Archicad на этой странице нет.
**Статус/ограничение:** SOURCE_NEGATIVE_SCOPE, отсутствие упоминания не доказывает отсутствия проекта вообще.
**Адресное задание №2:** №2: не заменять официальную GH Live Connection гипотетическим Rhino.Inside.Archicad.

## S30 — GSM-LCF exporter исторический
**Вопрос BUILD-01:** GSM-LCF exporter исторический.
**Первоисточник:** https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
**Версия/факт:** Graphisoft download описывает GSM-LCF exporter для Rhino 5 и LCF Observer для AC18–20, не документирует Rhino8/AC29.
**Статус/ограничение:** SOURCE_VERSION_MISMATCH; не утверждать несовместимость без теста.
**Адресное задание №2:** №2: не включать старый GDL exporter в стек AC29/Rhino8; для library objects использовать AC29 GH Object Settings.
