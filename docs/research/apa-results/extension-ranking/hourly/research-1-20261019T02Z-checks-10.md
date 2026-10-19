# APA №1 02Z · SOURCE 28–30

Только первоисточники; версии в ссылках. BUILD/INSTALLED/LIVE/ACCEPTED не проводились.

**28. Можно ли читать JSON через identifier URI?** [DEPRECATED](https://github.com/buildingSMART/bSDD/blob/master/Documentation/bSDD API.md#L30), blob `0ae67e5bc0b4`. Свидетельство: buildingSMART объявляет JSON identifier deprecated. Вывод: SOURCE подтверждён. Контрааудит: Использовать versioned Class/Property API. Далее: 4D.

**29. Можно ли хранить planned/baseline/actual графики?** [add_work_schedule](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/api/sequence/add_work_schedule.py#L29), blob `06a3fa9e8f3c`. Свидетельство: IfcWorkSchedule(name,predefined_type,start_time,work_plan). Вывод: SOURCE подтверждён. Контрааудит: Не вычисляет сроки. Далее: Связь с продуктом.

**30. Можно ли связать IfcTask с созданным элементом?** [assign_product](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/api/sequence/assign_product.py#L24), blob `5f029f1c4245`. Свидетельство: IfcRelAssignsToProduct для task→product. Вывод: SOURCE подтверждён. Контрааудит: Не календарная симуляция. Далее: Два аудита.

