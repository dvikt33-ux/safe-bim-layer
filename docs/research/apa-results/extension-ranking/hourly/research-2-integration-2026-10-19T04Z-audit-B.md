# APA №2 04Z — независимый контрааудит Б: монтаж

Существующий APA: DynamicCommands Router, PR154 V1 IfcTester/IfcDiff, PR165 V2 12 IFC/DXF routes, PR167 B2, PR170 B3, PR173 SceneWriter/SQLite Hotlink. Второй Router/MCP/IFC engine не нужен.

Альтернативы XML: (A) APA file QA → tagged v0.8.0 parser → JSON (выбрано для чтения); (B) редактировать/импортировать в AC29 (DEFER: 3D Axonometry loss). Property: (A) существующий IFC export → B2/IfcTester → JSON (выбрано для экспортируемых свойств); (B) официальный live JSON (crash risk); (C) Tapir native property getter (DEFER до изолированного safety gate). GDL: (A) standalone archicad-gdl → AC29 LP_XMLConverter (DEFER до units/license), (B) второй MCP server (REJECT). Terrain: (A) native Mesh/Slab read → drape.py/CDT → deviation JSON (ADAPTER); (B) чужой create_road_marking → GDL writes (REJECT).

Опасности: IFC stale export/GlobalId mismatch, skipped rules score=100, official model-only inventory, XML reimport loss, heuristic OBJ units, mesh holes and max500 nodes, hidden native property crash. PR173 LIVE saved/reopened — не ACCEPTED; не повторять операции.

Gates: SOURCE pinned; OFFLINE negative fixtures; BUILD/INSTALLED только с разрешения и hash; LIVE отдельное разрешение/scratch PLN; ACCEPTED независимый GUID/unit/geometry/readback. В текущем цикле новых стадий после SOURCE нет.
