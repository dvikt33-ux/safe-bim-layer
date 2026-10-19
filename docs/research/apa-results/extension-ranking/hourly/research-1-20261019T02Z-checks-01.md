# APA №1 02Z · SOURCE 1–3

SDK29 tag 29.3100, Graphisoft EULA. Runtime AC29 build5101/Tapir1.5.10 NOT_VERIFIED; no LIVE.

**1. Как пакетно инвентаризировать атрибуты?** [GetAttributesByType](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___attribute.html#L340), blob `366125ffcd20`. Свидетельство: API_AttrTypeID → массив API_Attribute. Вывод: готовый read-only контракт. Контрааудит: Атрибут не размещённый элемент. Далее: Классификации атрибута.

**2. Можно ли прочесть классификации материала?** [GetClassificationItems](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___attribute.html#L409), blob `366125ffcd20`. Свидетельство: API_Attr_Head → пары system/item GUID. Вывод: готовый read-only контракт. Контрааудит: Не element classifications. Далее: Одна система.

**3. Можно ли проверить класс в конкретной системе?** [GetClassificationInSystem](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___attribute.html#L412), blob `366125ffcd20`. Свидетельство: attrHead+systemGuid → API_ClassificationItem. Вывод: готовый read-only контракт. Контрааудит: Нет автоподстановки при отсутствии. Далее: Определения свойств.

