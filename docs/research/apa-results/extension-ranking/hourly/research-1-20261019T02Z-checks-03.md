# APA №1 02Z · SOURCE 7–9

SDK29 tag 29.3100, Graphisoft EULA. Runtime AC29 build5101/Tapir1.5.10 NOT_VERIFIED; no LIVE.

**7. Отдельна ли видимость свойства?** [IsPropertyDefinitionVisible](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___attribute.html#L448), blob `366125ffcd20`. Свидетельство: bool Visible(attrHead,propertyGuid). Вывод: готовый read-only контракт. Контрааудит: Visible ≠ editable/valid. Далее: Системы.

**8. Как перечислить системы в PLN?** [GetClassificationSystems](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___classification.html#L191), blob `32d7b6a37c73`. Свидетельство: Массив API_ClassificationSystem. Вывод: готовый read-only контракт. Контрааудит: Не внешний актуальный словарь. Далее: Иерархия.

**9. Как пройти дерево классификации?** [GetClassificationItemChildren](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___classification.html#L200), blob `32d7b6a37c73`. Свидетельство: itemGuid → массив детей. Вывод: готовый read-only контракт. Контрааудит: Не все узлы одним вызовом. Далее: Валидность значения.

