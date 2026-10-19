# APA №2 16Z — SOURCE проверки 19–24

**19. Combo order?** [Первичный источник](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/GraphicOverrideCommands.cpp). Контракт/параметры: L705-782: ordered rule IDs, silent skip on error. Адаптер/блокер: Ordered count/ID readback. Вердикт: SOURCE, следующая проверка: Priority order fixture.

**20. Grid degenerate?** [Первичный источник](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/GridElementCommands.cpp). Контракт/параметры: L460-555: begin/end, length<1e-6 error. Адаптер/блокер: Preflight finite coordinates. Вердикт: SOURCE, следующая проверка: Same point fixture.

**21. Grid unknown GDL?** [Первичный источник](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/GridElementCommands.cpp). Контракт/параметры: L223-268: warning and skip. Адаптер/блокер: Require warnings=[] and GREL. Вердикт: SOURCE, следующая проверка: Unknown parameter.

**22. MEP domain AC29?** [Первичный источник](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/MEPCommands.cpp). Контракт/параметры: L1389-1420,1639-1725: Piping/Ventilation; CableCarrier invalid. Адаптер/блокер: Read-only V2 adapter. Вердикт: SOURCE, следующая проверка: Bad domain fixture.

**23. ElectricalPanels AC29?** [Первичный источник](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/MEPCommands.cpp). Контракт/параметры: L1834-1913: requires AC30. Адаптер/блокер: Reject AC30-only for AC29. Вердикт: SOURCE, следующая проверка: Version gate.

**24. IFC port peers все?** [Первичный источник](https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py). Контракт/параметры: L91-129: get_connected_port returns first. Адаптер/блокер: Enumerate all ConnectedTo/From in V2. Вердикт: SOURCE, следующая проверка: Multi-edge fixture.

Все проверки статические; никаких OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED запусков.
