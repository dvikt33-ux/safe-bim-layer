# APA №2 02Z — проверки 16–30 (SOURCE, без исполнения)

16. **Как различать статус значения?** [SDK29 `API_Property` L143–196](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___property.html#L143): `status` принимает `API_Property_NotAvailable`, `API_Property_NotEvaluated`, `API_Property_HasValue`; `value` допустимо читать только при HasValue, `isDefault` отдельно. **DEFER** SDK bridge; следующий: Publisher.

17. **Можно ли читать имена Publisher Sets без публикации?** [AC29 Python L1062–1075](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetPublisherSetNames()->List[str]`. **REUSE** в preflight; следующий: дерево GUID.

18. **Есть ли типизированное дерево?** [AC29 Python L852–868, L3358–3371](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetNavigatorItemTree(NavigatorTreeId)`, `NavigatorTreeId(type:str,name:Optional[str])`. **REUSE**, передавать точное имя; следующий: Tapir.

19. **Что делает Tapir без имени Publisher Set?** [Tapir 1.5.9 NavigatorCommands.cpp L1527–1595](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L1527): `navigatorMapId="PublisherSets"`, `publisherSetName` optional; без имени выбирает первый. **FAIL-CLOSED** при нескольких наборах; следующий: selected IDs.

20. **Что если selectedNavigatorItemIds=[]?** [Tapir 1.5.9 L63–104](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L63): `selectedLinksPtr=nullptr` если массив пуст; далее `ACAPI_ProjectOperation_Publish(&publishPars,selectedLinksPtr)`. Это риск публикации всего набора. **NO PUBLISH** до nonempty GUID allowlist. Следующий: IFC inheritance.

21. **Есть ли готовое наследование классификаций?** [IfcOpenShell 0.8.5 `util/classification.py` L24–40](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/classification.py#L24): `get_references(element,should_inherit=True)` читает type через `util.element.get_type`. **REUSE** в PR165 вместо второго графа; следующий: overrides.

22. **Как учитывается override по системе?** [тот же файл L41–59](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/classification.py#L41): type refs grouped by `get_classification(ref)`; occurrence refs `update` заменяют совпадающую систему. **ADAPTER**: diff inherited/own/system; следующий: parent system.

23. **Как получить корневую систему?** [тот же файл L61–69](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/classification.py#L61): `get_classification(reference)` рекурсивно идёт по `ReferencedSource` до `IfcClassification`. **REUSE**, сохранять Identification/ItemReference с IFC schema; следующий: 5D.

24. **Отсутствующее количество равно нулю?** [IfcOpenShell 0.8.5 `util/cost.py` L49–60](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py#L49): `get_total_quantity(IfcCostItem)` возвращает `None` при отсутствии `CostQuantities`, сумму при наличии. **REUSE**, отсутствие≠0; следующий: divide.

25. **Надёжен ли cost DIVIDE?** [`util/cost.py` L63–87](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py#L63): `calculate_applied_value` при `ArithmeticOperator="DIVIDE"` ловит `ZeroDivisionError` и `pass`. **BLOCKER**: недопустимо принимать без отдельного denominator guard; следующий: Space.

26. **Попадает ли IfcSpace в PRODUCT?** [`util/cost.py` L238–253](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py#L238): `get_cost_assignments_by_type(filter_by_type="PRODUCT")` переводит в `IfcElement`; IfcSpace — не IfcElement. **ADAPTER**: SPACE_UNSUPPORTED, не тихий ноль; следующий: готовый bSDD client.

27. **Есть ли готовый bSDD wrapper?** [IfcOpenShell 0.8.5 `src/bsdd/pyproject.toml` L1–40](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/bsdd/pyproject.toml#L1): отдельный `bsdd` Python>=3.10, LGPL-3+, `requests,typing-extensions,pydantic`; [`bsdd.py` L509](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/bsdd/bsdd.py#L509) содержит `Client`. **ADAPTER**, не новый REST SDK; следующий: defaults.

28. **Безопасен ли default get_dictionary?** [`bsdd.py` L688–698](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/bsdd/bsdd.py#L688): `include_test_dictionaries:bool="False"` (строка); ternary `"true" if include_test_dictionaries else "false"` даёт true. **SOURCE bug**, явно передавать `False` и проверять ответ; следующий: HTTP/version.

29. **Есть ли контроль HTTP, версии и лицензии?** [`bsdd.py` L520–524](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/bsdd/bsdd.py#L520): `requests.get(...timeout=10).json()` без `raise_for_status`, retry/cache; `__version__="0.0.0"` L33. [buildingSMART OpenAPI L293–319,3290–3338](https://github.com/buildingSMART/bSDD/blob/master/Documentation/bSDD%20OpenAPI.yaml#L293): `Dictionary/v1`, поля `version,isLatestVersion,isVerified,isPrivate,license,licenseUrl`; `Class/v1`, `Class/Properties/v1`, `Property/v5`, `TextSearch/v2`. **ADAPTER**: exact URL/response gate, pinned SHA, offline cache, license; следующий: 4D.

30. **Есть ли готовые связи задач и риск orphan?** [IfcOpenShell 0.8.5 `util/sequence.py` L299–306,332–395](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/sequence.py#L299): `get_work_schedule_tasks`, `get_task_outputs` (`IfcRelAssignsToProduct`), `get_task_inputs` (`IfcRelAssignsToProcess`), `get_tasks_for_product(product,schedule)`. Последний вызывает `get_task_work_schedule(task).id()` при фильтре без None guard. **REUSE+ADAPTER**, отдельно обрабатывать unscheduled; следующий: OFFLINE fixtures с 3 задачами.

**Контроль B1:** все вызовы IFC/bSDD — исходники tag `ifcopenshell-python-0.8.5`, не latest; `bsdd` объявляет версию 0.0.0, поэтому идентифицировать blob `fbc14cc3`, не выдавать 0.0.0 за рабочий релиз. Tapir source 1.5.9 ≠ локальная 1.5.10. Graphisoft SDK29 29.3100 ≠ доказанный бинарный runtime 5101. 15 SOURCE-проверок, без установок, native calls и PLN writes.
