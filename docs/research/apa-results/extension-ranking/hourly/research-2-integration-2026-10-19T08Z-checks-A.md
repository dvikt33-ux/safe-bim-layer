# APA №2 08Z — проверки 01–10

Все проверки SOURCE: вопрос → независимый первоисточник → точный контракт → вердикт → следующая проверка. Ни одной новой операции Archicad.

1. **Очередь №3** — [источник](../NEXT_RESEARCH_PRIORITIES.md). Контракт: 20Z: 8 задач №2, новые ACCEPTED отсутствуют. **REUSE**. Далее: проверить свежую очередь.

2. **Матрица 61** — [источник](../priority_matrix_20261018.json). Контракт: count=61; НЕ_ВНЕДРЯТЬ_ПОКА выше score. **PASS**. Далее: не предлагать второй writer.

3. **№1 07Z** — [источник](research-1-20261019T07Z.md). Контракт: основной отчёт есть, cards/checks-B 404. **PARTIAL_SOURCE**. Далее: запросить отсутствующие приложения.

4. **MEP owner** — [источник](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py#L91-L109). Контракт: get_ports: IFC4 IsNestedBy, IFC2X3 HasPorts. **ADAPTER**. Далее: IFC2X3/IFC4 fixtures.

5. **MEP peer** — [источник](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py#L109-L130). Контракт: get_connected_port возвращает первого соседа. **BLOCK**. Далее: полный перебор RelConnectsPorts.

6. **APA PR165** — [источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L153-L185). Контракт: IFCPortRelations, sample≤5000, nativeMEPConnectionVerified=false. **REUSE**. Далее: PARTIAL_SAMPLE/owner.

7. **APA C1** — [источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-dxf-geometry-c1-20261018/scripts/apa_dxf_geometry_c1.py#L35-L80). Контракт: одна assembly на parent handle. **ADAPTER**. Далее: 2×3→6 cells.

8. **ezdxf** — [источник](https://ezdxf.readthedocs.io/en/stable/blocks/insert.html). Контракт: Insert.multi_insert, XCLIP не гарантирован. **REUSE**. Далее: ATTRIB/XCLIP_UNKNOWN.

9. **SQLite** — [источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-group-scenewriter-live-20261018/scripts/apa_ac29_group_scenewriter_sqlite_audit_readonly.py#L79-L112). Контракт: mode=ro/query_only/quick_check/scenes/steps. **REUSE**. Далее: STOPPED/LIVE_UNSAVED отдельно.

10. **Hotlink** — [источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/docs/evidence/apa-ac29-hotlink-batch-20261018/live02/native-calls.json). Контракт: CreateHotlinkInstances=1, batch=2, Save=1. **HISTORIC_LIVE**. Далее: никаких повторов.
