# APA №2 21Z — 15 технических проходов A
Каждый проход: вопрос → первоисточник/поле → вердикт → следующая проверка. SOURCE only. Ниже «проверено» означает чтение файла, не запуск.

01. **Приоритет?** → [очередь №3](../NEXT_RESEARCH_PRIORITIES.md): T2-20-01…08, PR173 batch ещё NOT LIVE на 20Z → статус устарел после LIVE-02; следующий: сверить receipt.
02. **Каталог?** → [матрица](../priority_matrix_20261018.json): count=61, IFCOPENSHELL=100, TAPIR=93, EZDXF=68 → рейтинг не benchmark; следующий: PR source.
03. **MEP уже покрыт?** → [PR165](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L168-L195): _ifc_ports считает IfcDistributionPort/IfcRelConnectsPorts, nativeMEPConnectionVerified=false → нужен owner graph; следующий: util.system.
04. **IFC4 owner?** → [util.system 0.8.5](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py#L85-L116): get_ports читает IsNestedBy.RelatedObjects и FlowDirection → готовый reader; следующий: IFC2X3.
05. **IFC2X3 owner?** → тот же pinned файл: HasPorts.RelatingPort → поддержка legacy отдельно; следующий: dangling fixture.
06. **Peer?** → тот же файл: get_connected_port возвращает первый ConnectedTo или ConnectedFrom, иначе None → не доказывает cardinality; следующий: проверить reciprocal/duplicate edges.
07. **Направление?** → тот же файл: get_connected_to/from обходят соответствующие отношения → готовая adjacency, но не гидравлический solver; следующий: FlowDirection.
08. **Система?** → тот же файл: get_element_systems фильтрует IfcRelAssignsToGroup и исключает Zone/StructuralAnalysisModel → не смешивать системы; следующий: IFC export completeness.
09. **MINSERT parser нужен?** → [ezdxf v1.4.5](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/disassemble.py#L542-L575): recursive_decompose при mcount>1 вызывает multi_insert → уже готов; следующий: PR168.
10. **PR168 использует его?** → [C1](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-dxf-geometry-c1-20261018/scripts/apa_dxf_geometry_c1.py#L30-L85): recursive_decompose([parent]), но groups[digest].append один раз после обхода parent → cell-level повтор не отражён; следующий: fixture 1×6.
11. **Zero spacing?** → [INSERT](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/entities/insert.py#L658-L707): mcount использует row/column count только при ненулевом spacing → count не обязательно rows×cols; следующий: нулевой шаг.
12. **OCS?** → INSERT.multi_insert: offset=Vec3(col*spacing,row*spacing), done=set(), rotate_deg(rotation), grid не масштабируется → уникальные OCS offsets; следующий: nested/rotated fixture.
13. **XCLIP применён?** → ezdxf disassemble прямо говорит XCLIP игнорируется → геометрия может быть скрыта; следующий: gate.
14. **Готовый XCLIP metadata?** → [XClip](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xclip.py#L67-L148): has_clipping_path, is_clipping_enabled, is_inverted_clip, get_block_clipping_path; 2D only → fail-closed; следующий: nested/inverted.
15. **Единицы и точность C1?** → C1: coordinateFrame=DXF_WCS, insunitsCode=$INSUNITS, unitConversionApplied=false, curveRepresentation=EZDXF_BEZIER_APPROXIMATION → только кандидаты BIM; следующий: unit/scale and curve fixture.

**Лицензия:** ezdxf v1.4.5 LICENSE MIT; IfcOpenShell pinned header LGPL-3.0-or-later. В текущем цикле OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED не запускались.
