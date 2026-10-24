# APA №1 — первичные проверки 21–29, 19.10.2026 00Z

Версии: Graphisoft DevKit29 tag 29.3100; IfcOpenShell pinned 0.8.5; buildingSMART IDS Audit source 1.0.124. Все SOURCE, не LIVE.

### 21. IFC assignments без PLN-записи
[Первоисточник](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_i_f_c_a_p_i_1_1_hook_manager.html): L204 RegisterAssignmentsHook(AssignmentsHookFunction). **Вывод:** Экспортные отношения IfcGroup/IfcSystem можно формировать callback. **Контрааудит:** Не путать IFC assignment и нативную группу APA. **Следующий вопрос:** №2: готовый IFCHook_Test, register/unregister lifecycle. **Статус:** SOURCE.

### 22. IFC opening/void relationships
[Первоисточник](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___i_f_c_relationship_data.html): L147 relFillsTable, L151 relVoidsTable, L155 assignmentTable. **Вывод:** SDK29 даёт точную структуру IFC GlobalId связей при ACAPI_ProjectOperation_Save. **Контрааудит:** Это экспортный аргумент, не готовая команда чтения или hosted opening anchor. **Следующий вопрос:** №2: проверить mapping IfcOpeningElement↔Wall/Slab. **Статус:** SOURCE.

### 23. Независимый IFC→SQLite snapshot
[Первоисточник](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcpatch/ifcpatch/recipes/Ifc2Sql.py): L69–105 Patcher(sql_type='SQLite',full_schema=True,should_expand=False). **Вывод:** IfcOpenShell 0.8.5 уже создаёт SQL без нового IFC parser. **Контрааудит:** full_schema создаёт таблицы всех классов; should_expand=True делает ifc_id неуникальным. **Следующий вопрос:** №2: оценить объём и уникальность STEP IDs. **Статус:** SOURCE.

### 24. Свойства и IDs в SQL
[Первоисточник](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcpatch/ifcpatch/recipes/Ifc2Sql.py): L367–382 create_id_map(); L408–417 psets(ifc_id,pset_name,name,value). **Вывод:** Готовый read-only по смыслу QA снимок IFC атрибутов. **Контрааудит:** SQL запись на диск; STEP id != IFC GlobalId. **Следующий вопрос:** №2: проверка joins и lossless psets. **Статус:** SOURCE.

### 25. Геометрия и Windows SQL
[Первоисточник](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcpatch/ifcpatch/recipes/Ifc2Sql.py): L419–441 shape/geometry BLOB; L242–244 commit/close Windows. **Вывод:** Готовая геометрическая выборка; можно исключить geometry при тяжёлых моделях. **Контрааудит:** should_get_geometry=True по умолчанию, нет benchmark по памяти. **Следующий вопрос:** №2: сравнить два режима на изолированном IFC. **Статус:** SOURCE.

### 26. Независимый IDS audit CLI
[Первоисточник](https://github.com/buildingSMART/IDS-Audit-tool/blob/main/ids-tool/ids-tool.csproj): net8.0; Version=1.0.124; PackageId ids-tool.CommandLine; MIT. **Вывод:** Официальный аудит IDS XSD/семантики, не IFC compliance. **Контрааудит:** Версия csproj не доказывает установленный NuGet пакет. **Следующий вопрос:** №2: negative IDS fixtures и коды ошибок. **Статус:** SOURCE.

### 27. IDS audit reusable library
[Первоисточник](https://github.com/buildingSMART/IDS-Audit-tool/blob/main/ids-lib/ids-lib.csproj): netstandard2.0;net8.0;net10.0; Version=1.0.124; MIT. **Вывод:** Готовая библиотека buildingSMART для проверки спецификаций. **Контрааудит:** Windows .NET runtime и ABI не проверены. **Следующий вопрос:** №2: package signature/SHA и API Run. **Статус:** SOURCE.

### 28. IDS 1.0 поля для правил
[Первоисточник](https://github.com/buildingSMART/IDS/blob/development/Schema/ids.xsd): version=1.0.0; propertyType: propertySet/baseName required; dataType optional. **Вывод:** Есть официальный schema-контракт для проверки правил. **Контрааудит:** Стандарт CC BY-ND 4.0, не лицензия MIT инструмента. **Следующий вопрос:** №2: сверить embedded schema версии ids-lib. **Статус:** SOURCE.

### 29. IFC CRS fail-closed
[Первоисточник](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/geolocation.py): L147–177 auto_xyz2enh; без map conversion возвращает XYZ; L271–277 get_crs. **Вывод:** Готовый геодезический QA без нового движка. **Контрааудит:** Без CRS результат может выглядеть правдоподобным и быть неверным. **Следующий вопрос:** №2: missing CRS / shift / scale + inverse fixtures. **Статус:** SOURCE.

