# APA AC29 №2 17Z — source evidence 01–10

Каждая строка: вопрос; точные поля исходника; вывод; следующий вопрос. **10 SOURCE checks, 0 OFFLINE runs**. PR165 V2 blob 39b8b60474bd31607c126f764cc167438ace7d7e.

01. **Каталог V2** [L23-L38](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L23-L38) — 8 IFC+4 DXF в COMMANDS; namespace APAHighDensityReadOnlyV2. **Вердикт:** REUSE Router, не новый writer. **Далее:** проверить 12 регистраций.

02. **IFC inventory** [L102-L110](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L102-L110) — by_type IfcProduct/IfcRoot/IfcSpatialStructureElement, EXPORTED_IFC_ONLY_NOT_NATIVE_MODEL_DUMP. **Вердикт:** не PLN. **Далее:** сверить native dump.

03. **GlobalId** [L112-L133](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L112-L133) — missingCount, duplicateCount, nativeGuidMappingChecked=false. **Вердикт:** REUSE только IFC QA. **Далее:** сверить native GUID map.

04. **Spatial** [L136-L150](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L136-L150) — IfcRelAggregates/IfcRelContainedInSpatialStructure, childrenSample[:20]. **Вердикт:** нет полного child GUID graph. **Далее:** сверить полный набор GUID.

05. **Hosted openings** [L153-L167](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L153-L167) — IfcRelVoidsElement host/opening и IfcRelFillsElement opening/window, physicalHostGeometryChecked=false. **Вердикт:** REUSE existing host-cut QA. **Далее:** проверить host geometry.

06. **MEP ports** [L170-L191](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L170-L191) — IfcDistributionPort/IfcRelConnectsPorts, nativeMEPConnectionVerified=false. **Вердикт:** экспортная связность не native. **Далее:** сверить Tapir GetMEPPorts.

07. **Psets** [L194-L205](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L194-L205) — IfcRelDefinesByProperties, coverageBySetName, russianCodeComplianceClaimed=false. **Вердикт:** не проверяет значения или СП. **Далее:** IDS fixtures.

08. **Classification** [L207-L218](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L207-L218) — IfcRelAssociatesClassification, Identification/ItemReference, relatedCount. **Вердикт:** нет нормативной проверки. **Далее:** версия классификатора.

09. **Georeference** [L220-L238](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L220-L238) — IfcMapConversion Eastings/Northings/Scale, IfcProjectedCRS; calibrationVerified=false. **Вердикт:** IFC2X3 может не иметь MapConversion. **Далее:** три репера.

10. **DXF layers** [L247-L256](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L247-L256) — $INSUNITS, modelspaceCount, unitConversionApplied=false. **Вердикт:** единицы блока отдельны. **Далее:** сверить block units.

Upstream: https://github.com/IfcOpenShell/IfcOpenShell (LGPL-3.0+), https://ezdxf.readthedocs.io/en/stable/concepts/units.html (ezdxf 1.4.5). SOURCE ≠ installed 0.8.5/1.4.5.
