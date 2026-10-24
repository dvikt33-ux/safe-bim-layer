# APA №2 21Z — проверки 16–23
16. **Полнота C1?** → [PR168](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-dxf-geometry-c1-20261018/scripts/apa_dxf_geometry_c1.py): unsupportedGeneratedEntitiesExcluded=true, sourceAssemblyCompletenessVerified=false → не считать BIM; следующий: negative fixture.
17. **Backend B3?** → [PR170](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-ifc-geometry-b3-20261018/scripts/apa_ifc_geometry_b3.py): ifcopenshell==0.8.5, geom.iterator и serializers.obj/gltf → reuse, без второго IfcConvert; следующий: world/local.
18. **GLB world?** → PR170: settings.set('use-world-coords', action!='glb') → GLB local, OBJ/bounds world; следующий: matrix roundtrip.
19. **Полнота B3?** → PR170: processed==selected STEP ids, convert-back-units=false, IFC_WORLD_SI_METRES → число проверено, метры отдельно калибровать; следующий: two instances.
20. **Mirror/nonuniform?** → [placement0.8.5](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/placement.py#L128-L171): Axis2 dot<0 flips, Scale2/Scale3 → готов 3D matrix; следующий: determinant<0, 1×2×3.
21. **2D mapped?** → placement0.8.5: TODO 2d, get_mappeditem_transformation returns только для 3D → NOT_SUPPORTED; следующий: fail-closed.
22. **Nested mapped?** → [representation0.8.5](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/representation.py#L321-L340): resolve_items рекурсивно раскрывает mapped, rep_matrix @ matrix → проверить порядок; следующий: nested fixture.
23. **Missing QTO?** → [cost0.8.5](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/cost.py#L49-L60): no CostQuantities→None, zero→0.0 → разные состояния; следующий: unit/currency.
SOURCE only, no runtime.
