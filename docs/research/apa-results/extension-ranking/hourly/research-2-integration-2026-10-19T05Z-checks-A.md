# APA №2 05Z — P01–P09. Фактические SOURCE-проходы

Формат: вопрос → первоисточник → контракт → готовый путь/блокер → вердикт → следующая проверка. Ниже только проверенные исходники; тесты не запускались.

**P01 — Каталог свойств.** [Graphisoft AC29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetAllPropertyIds(propertyType=None) → List[PropertyIdArrayItem]`, фильтр Built-in/User Defined. APA → существующий официальный JSON → Router; каталог определений не значения. **REUSE**; далее сверить две категории.

**P02 — Прямое соответствие.** [AC29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetPropertyDefinitionAvailability(propertyIds)` возвращает `PropertyDefinitionAvailabilityOrError`, включая отдельную ошибку. Готовый штатный метод; пустой результат не PASS. **ADAPTER** typed JSON; далее тест 2 свойств.

**P03 — Обратное соответствие.** [AC29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetClassificationItemAvailability(classificationItemIds)` возвращает `ClassificationItemAvailabilityOrError`. В [Tapir snapshot 1.5.10](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-ac29-native-contract-gaps-d1-20261018/schemas/tapir-live-1.5.10/tapir-scene-live.json) обе availability-команды отсутствуют: direct Tapir **NOT_FOUND в snapshot**. Выбрать официальный JSON без APX; далее двунаправленный diff с error/empty.

**P04 — Охват элементов.** [AC29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetPropertyValuesOfElements(elements,properties,onlySupportedTypes=None)`; `onlySupportedTypes=true` фильтрует неподдерживаемые типы. Existing Router должен сравнить requested/returned GUID и cardinality. **ADAPTER**; далее fixture с unsupported type.

**P05 — Разные статусы.** [AC29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `NotAvailablePropertyValue.status=notAvailable`, `NotEvaluatedPropertyValue.status=notEvaluated`, `Error(code,message)` — отдельные union branches. Путь — существующее чтение + typed envelope, не второй property engine. **REUSE**; далее normal/notAvailable/notEvaluated/error fixture.

**P06 — Единицы.** [AC29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): NormalLength м, NormalArea м², NormalVolume м³, NormalAngle рад. [Tapir](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-ac29-native-contract-gaps-d1-20261018/schemas/tapir-live-1.5.10/tapir-scene-live.json) `GetPropertyValuesOfElements` требует `elements,properties`. Не приводить статус к нулю; **ADAPTER** SI display-only; далее тест mm→m, deg→rad.

**P07 — Состав композита.** [AC29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetCompositeAttributes(attributeIds) → CompositeAttributeOrError`; `totalThickness,compositeSkins,compositeLines,useWith`. Штатный Graphisoft read → Router → QA. **REUSE**; далее сравнить сумму толщин на синтетическом композите.

**P08 — Данные слоя.** [AC29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `CompositeSkin(buildingMaterialId:AttributeIdOrError,thickness:float,isCore:bool,isFinish:bool,framePenIndex?:int)`. Сохранять material GUID, порядок, error; номинал ≠ размещённый BREP. **ADAPTER**; далее fixture с неразрешённым material.

**P09 — Отсутствие Tapir read.** [Tapir source snapshot](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-ac29-native-contract-gaps-d1-20261018/schemas/tapir-live-1.5.10/tapir-scene-live.json) содержит `CreateComposites`, но не `GetCompositeAttributes`; создание/перезапись запрещены. Путь через официальный AC29 read, не SDK29. **REUSE/NOT_FOUND для Tapir-read**; далее runtime capability probe без записи.
