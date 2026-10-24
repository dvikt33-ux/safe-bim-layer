# APA №2 02Z — проверки 01–15 (SOURCE, без исполнения)

Каждая запись: **вопрос → первоисточник/строки → контракт → адаптер/блокер → вердикт и следующий вопрос**. Сверены файлы на фиксированных refs. `SOURCE` не означает `INSTALLED`.

01. **Что уже делает APA для IFC classifications?** [PR165 V2 `apa_high_density_readonly_v2.py` L208–219](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L208): `_ifc_classifications` читает `IfcRelAssociatesClassification`, отдаёт `classificationType,code,relatedCount`, ограничение `SAMPLE_LIMIT=5000`. **REUSE**; наследование type→occurrence не покрыто. Следующий: vendor inheritance.

02. **Как APA изолирует IFC?** [PR167 B2 L85–100](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-ifc-artifacts-b2-20261018/scripts/apa_ifc_artifacts_b2.py#L85): `importlib.metadata.version` проверяет exact `0.8.5`, `copy=source.ifc` в `TemporaryDirectory`, SHA до открытия. **REUSE** B2, не создавать второй IFC executor. Следующий: исходный SHA после.

03. **Есть ли контроль полноты геометрии?** [PR170 B3 L53–121](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-ifc-geometry-b3-20261018/scripts/apa_ifc_geometry_b3.py#L53): `processed=={x.id() for x in selected}`, `convert-back-units=False`, `sourceUnchanged`. **REUSE** для будущего геометрического QA, но не утверждать BREP equivalence. Следующий: native GUID.

04. **Как проверить реальный AC29 build?** [AC29 Python `GetProductInfo` L906–919](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): возвращает version/build/language. **REUSE**, но в этом цикле не вызывался. Следующий: local 5101.

05. **Есть ли штатная инвентаризация атрибутов?** [AC29 Python L402–420](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetAttributesByType(attributeType:str)->List[AttributeIdWrapperItem]`. **REUSE**, C++ не нужен для списка. Следующий: GUID/index.

06. **Можно ли получить GUID и индекс?** [AC29 Python L422–439](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetAttributesIndices(attributeIds)->List[AttributeIndexAndGuidOrError]`. **REUSE**, каждый error отдельно. Следующий: material detail.

07. **Есть ли данные строительного материала?** [AC29 Python L441–457](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetBuildingMaterialAttributes(attributeIds)->List[BuildingMaterialAttributeOrError]`. **REUSE**, GUID не element GUID. Следующий: папки.

08. **Есть ли дерево папок атрибутов?** [AC29 Python L363–381](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetAttributeFolderStructure(attributeType,path=None)`; `None` означает root. **REUSE**, не создавать новую иерархию. Следующий: classification system.

09. **Можно ли перечислить системы классификации?** [AC29 Python L495–527](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): `GetClassificationSystemIds()->List[ClassificationSystemIdArrayItem]`, `GetClassificationSystems(ids)`. **REUSE**, но это список систем, не присвоения атрибутам. Следующий: element classification.

10. **Подходит ли GetClassificationsOfElements для атрибутов?** [AC29 Python L528–546](https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html): параметр `elements:List[ElementIdArrayItem]`, `classificationSystemIds`; результат `ElementClassificationOrError`. **NO**, не подменять attribute→classification. Следующий: SDK29.

11. **SDK29 умеет классификацию атрибутов?** [SDK29 `group___attribute.html` L409](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___attribute.html#L409): `ACAPI_Attribute_GetClassificationItems(API_Attr_Head, GS::Array<GS::Pair<API_Guid,API_Guid>>&)`. **SOURCE**, готовый JSON bridge NOT_FOUND в изученных AC29 Python/Tapir. Следующий: одна система.

12. **Можно ли получить атрибутный класс конкретной системы?** [SDK29 L412](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___attribute.html#L412): `ACAPI_Attribute_GetClassificationInSystem(attrHead,systemGuid,item)`. **DEFER**, требует разрешённый AC29 addon/ABI. Следующий: определения свойств.

13. **SDK29 читает определения атрибутных свойств?** [SDK29 L424](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___attribute.html#L424): `GetPropertyDefinitions(attrHead,filter,definitions)`. **SOURCE**, read-only, но нет готового штатного JSON метода. Следующий: значения.

14. **Можно ли пакетно читать значения по GUID определений?** [SDK29 L433](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___attribute.html#L433): `GetPropertyValuesByGuid(attrHead,GS::Array<API_Guid>,GS::Array<API_Property>)`. **DEFER** до проверенного SDK29 bridge. Следующий: availability.

15. **Доступность и видимость совпадают?** [SDK29 L445,448](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___attribute.html#L445): отдельные `IsPropertyDefinitionAvailable` и `IsPropertyDefinitionVisible`, оба принимают `attrHead,propertyGuid`. **НЕ СКЛЕИВАТЬ**; отдельно учитывать NotAvailable/NotEvaluated/HasValue. Следующий: API_Property status.

**Контроль A1:** все AC29 Python контракты взяты из `archicad.releases.ac29`, а не из общего latest; SDK — tag `29.3100`. Это не доказывает local AC29 build5101, local Tapir1.5.10 или установленный APX. Риск дублирования: B/C отложены, A уже реализуется официальным API. Все 15 записей — реальные чтения SOURCE, не 15 тестов.
