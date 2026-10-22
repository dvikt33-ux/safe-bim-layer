# APA №1 — BUILD-01 — SOURCE 23–26 (G4/G0)

23. **Достаточен ли один GetElementsByType?** [Graphisoft API29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): возвращает GUID заданного типа «on the plan», не гарантирует обход всех Tapir databases. **№2:** сравнивать с отдельной поэтажной инвентаризацией, не считать универсальным.

24. **Можно ли сверить материал по компонентам?** [Graphisoft API29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): GetPropertyValuesOfElementComponents принимает IDs компонентов и property IDs, выдаёт PropertyValuesOrError. **№2:** сначала GetComponentsOfElements, затем явный контроль ошибок и material.

25. **Как защититься от дрейфа индекса материала?** [Graphisoft API29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): GetAttributesIndices возвращает AttributeIndexAndGuidOrError. **№2:** хранить GUID и индекс вместе до/после Save/Open, не принимать только имя.

26. **Готов ли автономный real-Archicad тест без вмешательства?** [Tapir PR887](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/887), MIT: community runner временно заменяет APX, запускает Archicad и требует GitHub token. **Решение:** НЕ ПРИМЕНЯТЬ: запрещены установка, изменение APX, LIVE и новые исполнители. **№2:** только ссылка как отклонённый вариант.

**4 проверки, 2 источника. SOURCE_ONLY; MODEL_MODE_NOT_VERIFIABLE.**
