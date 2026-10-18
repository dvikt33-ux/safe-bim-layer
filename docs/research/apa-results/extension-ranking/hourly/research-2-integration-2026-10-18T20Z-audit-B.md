# APA №2 20Z — независимый контрааудит B: монтаж/дублирование/безопасность

PR165 `_ifc_ports` считает IFC связи, но `nativeMEPConnectionVerified=false`: не объявлять исправность native MEP. PR170 OBJ/GLB/bounds не выдаёт `IfcMappedItem` matrix. PR154 PDFVectors не создаёт IFC document associations. PR167 уже обеспечивает IFC/BCF через существующий Router; второй provider не нужен.

`sequence.assign_product` — OUTPUT, `assign_process` — INPUT; смешение недопустимо. QTO missing/zero и валюту нельзя угадывать. В [ifc4d-gantt](https://github.com/brunopostle/ifc4d-gantt/blob/main/src/ifc4d_gantt/__init__.py#L166-L245) schedule names вставляются в HTML, а JS/CSS загружаются с CDN; готовый безопасный автономный просмотрщик не подтверждён. Не создавать второй Gantt engine. Все преобразования только на копиях IFC с SHA и output readback. Никакого ускорения без benchmark.

**Передать №3:** Hotlink readback 96; MEP graph 92; PDF provenance 91; 4D QA 86; 5D QA 83; mapped matrix 81. Баллы — полезность.

**Вопросы №1:** source↔wheel 0.8.5; офлайн-Gantt без CDN; QTO→ГЭСН/ФЕР mapping; native MEP→IFC ports; document page/revision/hash; mirrored/nonuniform matrices.

SOURCE — текущий цикл. OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED — новых нет. main/PLN/APX/код/план182/очередь не менялись.
