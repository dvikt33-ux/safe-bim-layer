# APA №1 — BUILD-01 — SOURCE 19–22 (G0/G4)

19. **Можно ли доверять фильтру версий документации?** [Tapir PR1054](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1054), MIT: поиск и version filter относятся к HTML-справочнику, не проверяют локальный APX. **№2:** использовать только для SOURCE discovery, G0 через IsAddOnCommandAvailable + APX SHA.

20. **Coverage checklist означает доступность API?** [Tapir PR1053](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1053), MIT: список API AC25–30 показывает покрытие и заявки, не installed command. **№2:** не переносить отметку coverage в RUNTIME_READY.

21. **Может ли AC29 пропустить элементы при чтении свойств?** [Graphisoft Python 29.3000](https://pypi.org/project/archicad/29.3000/), проприетарный API: GetPropertyValuesOfElements(onlySupportedTypes=true) фильтрует неподдержанные типы. **№2:** для G4 не использовать фильтр как доказательство полного инвентаря.

22. **Есть ли независимая проверка типа по GUID?** [Graphisoft API29 GetTypesOfElements](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): возвращает TypeOfElementOrError для списка GUID. **№2:** сравнить типы обязательных элементов с typed DAG, ошибки не игнорировать.

**4 проверки, 3 источника. SOURCE_ONLY; MODEL_MODE_NOT_VERIFIABLE.**
