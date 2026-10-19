# APA №1 02Z · SOURCE 4–6

SDK29 tag 29.3100, Graphisoft EULA. Runtime AC29 build5101/Tapir1.5.10 NOT_VERIFIED; no LIVE.

**4. Можно ли отфильтровать свойства атрибута?** [GetPropertyDefinitions](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___attribute.html#L424), blob `366125ffcd20`. Свидетельство: attrHead+filter → массив API_PropertyDefinition. Вывод: готовый read-only контракт. Контрааудит: Definition ≠ value. Далее: Пакетные значения.

**5. Можно ли пакетно прочесть значения?** [GetPropertyValuesByGuid](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___attribute.html#L433), blob `366125ffcd20`. Свидетельство: attrHead+массив propertyDefinition GUID → API_Property. Вывод: готовый read-only контракт. Контрааудит: GUID определения ≠ GUID элемента. Далее: Available.

**6. Как отличить неприменимое свойство от пустого?** [IsPropertyDefinitionAvailable](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___attribute.html#L445), blob `366125ffcd20`. Свидетельство: bool Available(attrHead,propertyGuid). Вывод: готовый read-only контракт. Контрааудит: False ≠ zero/empty. Далее: Visible.

