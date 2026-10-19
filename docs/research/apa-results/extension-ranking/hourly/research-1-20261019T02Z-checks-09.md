# APA №1 02Z · SOURCE 25–27

Только первоисточники; версии в ссылках. BUILD/INSTALLED/LIVE/ACCEPTED не проводились.

**25. Можно ли в 0.8.5 связать IfcSpace QTO со сметой?** [IfcSpatialElement](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/api/cost/assign_cost_item_quantity.py#L106), blob `20fc24ab3727`. Свидетельство: if product.is_a(IfcSpatialElement): continue — IfcSpace пропущен. Вывод: SOURCE подтверждён. Контрааудит: Upstream #7331 fix не доказывает исправление этого тега. Далее: bSDD.

**26. Есть ли готовый bSDD Class API?** [Class/v1](https://github.com/buildingSMART/bSDD/blob/master/Documentation/bSDD OpenAPI.yaml#L37), blob `aa76b54e4ccb`. Свидетельство: OpenAPI v1: GET /api/Class/v1. Вывод: SOURCE подтверждён. Контрааудит: Данные словаря и права отдельно. Далее: Property.

**27. Одинакова ли версия Property и Class?** [Property/v5](https://github.com/buildingSMART/bSDD/blob/master/Documentation/bSDD OpenAPI.yaml#L1026), blob `aa76b54e4ccb`. Свидетельство: Property/v5 против Class/v1. Вывод: SOURCE подтверждён. Контрааудит: Нельзя всем подставлять v1. Далее: URI.

