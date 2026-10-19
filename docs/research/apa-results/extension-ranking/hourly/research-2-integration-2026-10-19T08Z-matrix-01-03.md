# APA №2 08Z — матрица 01–03

**01. IFC MEP.** [IfcOpenShell util.system 0.8.5](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py#L91-L130), LGPL-3.0+. APA Router→PR165 IFCPortRelations→get_ports/get_port_element→BIM Graph. IFC2X3 HasPorts, IFC4 IsNestedBy; GlobalId/flow. ADAPTER, **98/100**, БЫСТРО, риск: first-peer. ГОТОВО: все peer/owner/flow, 3 fixtures, missing→NOT_EXPORTED.

**02. DXF MINSERT.** [ezdxf 1.4.5](https://ezdxf.readthedocs.io/en/stable/blocks/insert.html), MIT. Router→[PR168 C1](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-dxf-geometry-c1-20261018/scripts/apa_dxf_geometry_c1.py#L35-L80)→multi_insert→6 cell JSON. ADAPTER, **97/100**, АДАПТАЦИЯ. Риск: XCLIP/ATTRIB, virtual handles. ГОТОВО: 2×3→6 row/col/parent records, source SHA, XCLIP_UNKNOWN.

**03. SceneWriter/Hotlink.** [PR164 SQLite read-only](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-group-scenewriter-live-20261018/scripts/apa_ac29_group_scenewriter_sqlite_audit_readonly.py#L79-L112)→[PR173 receipt](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/docs/evidence/apa-ac29-hotlink-batch-20261018/live02/receipt.json). REUSE, **96/100**, БЫСТРО. 69→119 GUID, 2 roots+48 children, 1 batch+Save/reopen. Риск: original scratch drift. ГОТОВО: exact saved SHA, 69 retained BREP, 48 owners. ACCEPTED не доказан.

SOURCE only; баллы не benchmark. Новых установок и операций нет.
