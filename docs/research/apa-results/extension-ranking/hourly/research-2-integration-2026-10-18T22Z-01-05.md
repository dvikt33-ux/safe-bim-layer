# APA №2 22Z — проверки 01–05
SOURCE, не runtime. Каждая: вопрос → точный источник → контракт → решение → следующий вопрос.

01. Вход APA? PR165 `scripts/apa_high_density_readonly_v2.py` L381–408: `register(router)`, 12 read-only команд. REUSE, не второй Router. Далее: MEP.
02. Граф портов уже есть? PR165 тот же файл L170–190: `_ifc_ports`, `IfcDistributionPort`, `IfcRelConnectsPorts`, `nativeMEPConnectionVerified:false`. REUSE+adapter owner. Далее: IFC4.
03. Готовый IFC4 reader? IfcOpenShell 0.8.5 `util/system.py` L91–100: `get_ports(element,flow_direction=None)`, `IsNestedBy`. REUSE; не native AC29. Далее: IFC2X3.
04. IFC2X3? `util/system.py` L101–108: `HasPorts.RelatingPort` fallback. REUSE, schema gate. Далее: peer.
05. Peer? `util/system.py` L111–116: `get_connected_port` возвращает первый `ConnectedTo/ConnectedFrom`; для полного графа читать raw relations. ADAPTER, не утверждать полноту. Далее: owner.

Источники:
https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py
https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py
