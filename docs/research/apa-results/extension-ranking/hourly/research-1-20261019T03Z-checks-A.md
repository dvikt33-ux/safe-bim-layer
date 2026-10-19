# APA №1 20261019T03Z — содержательные проверки P01–P15

### P01 — Можно ли получить связь помещений с элементами без IFC-экспорта?
**Первоисточник/свидетельство:** AC29 b3000commands GetElementsRelatedToZones(zones: List[ElementIdArrayItem], elementTypes: List[str]) → List[ElementsOrError]; порядок результатов соответствует порядку зон; строки 700–718. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Готовый read-only запрос для проверки ограждений/состава зоны без второго геометрического ядра.
**Контрааудит:** «Связанные» не означает геометрически соприкасающиеся или нормативно корректные; точная семантика смежности в реальном PLN NOT_VERIFIED.
**Следующий вопрос №2:** №2: проверить типы стен/окон/дверей и пустую зону на копии, сопоставить GUID.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P02 — Не маскирует ли пакетный ответ ошибки отдельных зон?
**Первоисточник/свидетельство:** AC29 тип ElementsOrError(elements: List[ElementIdArrayItem] | None, error: Error | None), строки 2654–2669; Error(code:int,message:str), 2765–2779. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Ответ требует поэлементного разбора union, а не проверки только длины общего массива.
**Контрааудит:** Ошибка зоны ≠ пустая зона; без разборки union ложное «нет стен».
**Следующий вопрос №2:** №2: негативный тест несуществующего GUID зоны и различение error/empty.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P03 — Есть ли готовый способ перечислить компоненты сложной конструкции?
**Первоисточник/свидетельство:** AC29 GetComponentsOfElements(elements) → List[ElementComponentsOrError]; порядок ответов совпадает с входными элементами, строки 548–565. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Возможен read-only инвентарь компонентов без разбора IFC вручную.
**Контрааудит:** Компонент ≠ самостоятельный Element GUID; существующие BIM-элементы не создаются.
**Следующий вопрос №2:** №2: сравнить 1 композитную стену, 1 однослойную, 1 ошибочный GUID.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P04 — Как однозначно адресовать компонент?
**Первоисточник/свидетельство:** AC29 ElementComponentId(elementId: ElementId, componentId: ComponentId), строки 2549–2561; ElementComponentIdArrayItem.elementComponentId, 2564–2575. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Пара идентификаторов удерживает владельца; не следует использовать componentId как самостоятельный GUID.
**Контрааудит:** Не смешивать API ComponentId с GUID элемента или IFC GlobalId.
**Следующий вопрос №2:** №2: проверить стабильность пары при сохранении/повторном открытии scratch PLN.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P05 — Можно ли получить свойства именно компонентов, а не всей стены?
**Первоисточник/свидетельство:** AC29 GetPropertyValuesOfElementComponents(elementComponents, properties) → List[PropertyValuesOrError], строки 1018–1037. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Готовый компонентный канал для QTO/материалов и QA многослойных конструкций.
**Контрааудит:** Метод не доказывает корректность физических объёмов и не является сметным движком.
**Следующий вопрос №2:** №2: выбрать измеряемое свойство, проверить единицу и ошибку отсутствующего свойства.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P06 — Чем компонентный запрос отличается от поэлементного?
**Первоисточник/свидетельство:** AC29 GetPropertyValuesOfElements(elements,properties,onlySupportedTypes:bool|None=None), строки 1039–1060; фильтр onlySupportedTypes=true отбрасывает неподдерживаемые типы. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Сравнение полноты двух API обнаруживает потерю типов, но нельзя автоматически считать их равнозначными.
**Контрааудит:** Тихая фильтрация onlySupportedTypes может исказить итог QTO.
**Следующий вопрос №2:** №2: посчитать входные и выходные GUID при true/false, сверить ошибки.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P07 — Можно ли независимо прочитать структуру композита?
**Первоисточник/свидетельство:** AC29 GetCompositeAttributes(attributeIds) → List[CompositeAttributeOrError], строки 567–585. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Нативный состав композита доступен отдельно от списка компонентов элементов.
**Контрааудит:** Описание атрибута не доказывает фактический объём/геометрию экземпляра.
**Следующий вопрос №2:** №2: сверить слои композита и компонентные значения на одном элементе.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P08 — Есть ли исходный материал с GUID без внешнего каталога?
**Первоисточник/свидетельство:** AC29 GetBuildingMaterialAttributes(attributeIds) → List[BuildingMaterialAttributeOrError], строки 441–457. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Материальный паспорт можно читать через штатный API29.
**Контрааудит:** Материал не равен физическому слою; индекс атрибута не следует подменять GUID.
**Следующий вопрос №2:** №2: сравнить GUID материала композита с элементными компонентами.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P09 — Есть ли готовая грубая геометрическая проверка 3D?
**Первоисточник/свидетельство:** AC29 Get3DBoundingBoxes(elements) → List[BoundingBox3DOrError]; глобальный origin в 3D; поддержка только Element Information, строки 212–229. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Дешёвый AABB cross-check для уже существующего native BREP, не замена точной геометрии.
**Контрааудит:** Bounding box не выявляет пересечения точно и не подтверждает BREP; неподдерживаемые типы дают ошибки.
**Следующий вопрос №2:** №2: сопоставить AABB и BREP для одного повернутого объекта.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P10 — Можно ли сравнить 2D и 3D границы одной модели?
**Первоисточник/свидетельство:** AC29 Get2DBoundingBoxes(elements) → List[BoundingBox2DOrError], global origin на плане, строки 195–211. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Сопоставление XY-проекций пригодно для диагностики PDF/DXF якорей.
**Контрааудит:** 2D box плана и проекция 3D BREP не гарантированно совпадают при настройках отображения.
**Следующий вопрос №2:** №2: проверить элементы на разных этажах и 2D/3D расхождения.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P11 — Можно ли проверить размер листа без запуска Publisher?
**Первоисточник/свидетельство:** AC29 GetLayoutSettings(layoutNavigatorItemId:NavigatorItemId) → LayoutParameters, строки 814–832. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Готовая read-only проверка параметров листа перед публикацией.
**Контрааудит:** Размер листа ≠ реально сгенерированный PDF; команда уже близка к существующему Navigator preflight №2.
**Следующий вопрос №2:** №2: проверить листы с разными мастер-макетами, не дублировать существующий маршрут.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P12 — Как узнать структуру документации без создания листов?
**Первоисточник/свидетельство:** AC29 GetNavigatorItemTree(navigatorTreeId:NavigatorTreeId) → NavigatorTree, строки 852–868. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Готовый снимок дерева для сверки комплектности видов и листов.
**Контрааудит:** Дерево ≠ доказательство актуальности чертежа; базовый Navigator уже исследован №2.
**Следующий вопрос №2:** №2: добавить только контроль связей и полноты, не второй инвентаризатор.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P13 — Как обнаружить неверный тип элемента навигатора?
**Первоисточник/свидетельство:** AC29 GetNavigatorItemsType(navigatorItemIds) → List[NavigatorItemIdAndTypeOrError], строки 870–886; ошибка отдельно для каждого неизвестного ID. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Можно исключить путаницу лист/вид/папка перед экспортом.
**Контрааудит:** Тип не сообщает состояние обновления чертежа и не подтверждает PDF.
**Следующий вопрос №2:** №2: проверить 1 валидный лист, 1 папку, 1 отсутствующий ID.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P14 — Доступны ли свойства комбинаций слоёв без SDK-плагина?
**Первоисточник/свидетельство:** AC29 GetLayerCombinationAttributes(attributeIds) → List[LayerCombinationAttributeOrError], строки 795–813. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Готовый источник представления проекта для QA выпусков.
**Контрааудит:** Существующий №2 уже знает инвентаризацию атрибутов; новизна только cross-check view→combination.
**Следующий вопрос №2:** №2: выяснить, содержит ли возвращаемый тип требуемые флаги видимости слоёв.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.

### P15 — Можно ли сравнить перья модели и альбома?
**Первоисточник/свидетельство:** AC29 GetActivePenTables() → Tuple[AttributeIdOrError,AttributeIdOrError], строки 231–244; отдельно model view и layout book. [Источник](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html).
**Вывод:** Готовый детектор несовпадения идентификаторов наборов перьев.
**Контрааудит:** Разные ID могут быть намеренным оформлением, не дефектом.
**Следующий вопрос №2:** №2: определить whitelist допустимых различий, без изменения перьев.
**Стадии:** SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO.
