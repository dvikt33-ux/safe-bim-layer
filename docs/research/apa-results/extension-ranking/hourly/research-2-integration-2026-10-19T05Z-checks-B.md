# APA №2 05Z — P10–P18. Фактические SOURCE-проходы

**P10 — Атрибуты по типу.** [Graphisoft AC29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetAttributesByType(attributeType:str) → List[AttributeIdWrapperItem]`. APA Router → official JSON; список GUID, не содержимое. **REUSE**; далее 2 типа и неизвестный type.

**P11 — Индексы и GUID.** [AC29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetAttributesIndices(attributeIds) → List[AttributeIndexAndGuidOrError]`. Индекс не межпроектный ключ; хранить project/type/GUID, index только диагностика. **ADAPTER**; далее перестановка index без смены GUID.

**P12 — Разные формы ответов.** [Tapir snapshot](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-ac29-native-contract-gaps-d1-20261018/schemas/tapir-live-1.5.10/tapir-scene-live.json): `GetAttributesByType(attributeType) → AttributeHeadersOrError`, в Graphisoft — список ID. Не объединять payloads без маркировки `sourceSchema`; минимальный нормализатор, без второго каталога. **REUSE**; далее сопоставление одной копии.

**P13 — Происхождение классификации.** [AC29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetAllClassificationSystems → ClassificationSystem(source,version,date,name,classificationSystemId)`. Официальный read через Router; source/date не подтверждают актуальность СП. **REUSE**; далее независимая проверка реестра.

**P14 — Дерево и детали.** [AC29](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetAllClassificationsInSystem(systemId)` и `GetDetailsOfClassificationItems(ids)` возвращают дерево и union ошибки. Ключ (system GUID,item GUID), не display name. **ADAPTER**; далее orphan/duplicate-name fixture.

**P15 — IFC-классификации уже частично есть.** [PR165 V2](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L208-L218) считает `IfcRelAssociatesClassification`, `Identification/ItemReference`, relatedCount, но не сверяет source/version/date Archicad. Использовать V2, добавить только provenance QA. **ADAPTER**; далее два IFC GUID и metadata.

**P16 — IFC4D связи.** [IfcOpenShell 0.8.5](https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/sequence/index.html): `util.sequence.get_tasks_for_product(product,schedule=None) → (assignedTasks,referencedTasks)`. APA → existing vendor Python → Router → JSON, без нового scheduler. **ADAPTER**; далее три задачи и сохранение двух ролей.

**P17 — Мутации 4D запрещены.** [IfcOpenShell sequence API](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/sequence/index.html): `recalculate_schedule`, `cascade_schedule`, `create_baseline` изменяют IFC. В этом цикле не вызывать, выбирать только `util.sequence`. **DEFER**; далее read-only negative fixture/cycle.

**P18 — Пробел текущего V2.** [PR165](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L23-L38) перечисляет 12 IFC/DXF routes, нет 4D task relation. Узкий read-only adapter на существующем V1 vendor interpreter, не новый исполнитель. **ADAPTER**; далее 3-task fixture + SHA исходника + no modelWrites.
