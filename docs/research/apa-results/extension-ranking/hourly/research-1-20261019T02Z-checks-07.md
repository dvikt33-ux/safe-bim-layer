# APA №1 02Z · SOURCE 19–21

IfcOpenShell/Ifc5D tag ifcopenshell-python-0.8.5; LGPL-3.0-or-later. Windows wheel/APA runtime NOT_VERIFIED.

**19. Есть ли готовый ODS экспорт?** [IFC to ODS](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifc5d/README.md#L13), blob `ba37664a88f0`. Свидетельство: README заявляет IFC→ODS. Вывод: готовая функция/ограничение. Контрааудит: Не доказывает runtime. Далее: Обратный импорт.

**20. Поддерживается ли импорт ODS/XLSX?** [Importing ods/xlsx](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifc5d/README.md#L47), blob `ba37664a88f0`. Свидетельство: README: только CSV. Вывод: готовая функция/ограничение. Контрааудит: Не обещать двусторонний ODS. Далее: Заголовки CSV.

**21. Какие колонки ожидает конвертер?** [CsvHeader](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifc5d/ifc5d/csv2ifc.py#L37), blob `c33d6e847e9b`. Свидетельство: Index/Name/Unit, условные Quantity/Property/Query. Вывод: готовая функция/ограничение. Контрааудит: ФЕР/ГЭСН не готовы без mapping. Далее: Locale.

