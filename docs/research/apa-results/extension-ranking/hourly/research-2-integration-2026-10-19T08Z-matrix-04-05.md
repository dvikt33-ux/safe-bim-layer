# APA №2 08Z — матрица 04–05

**04. PDF→IFC документальная связь.** pdfplumber 0.11.10 MIT + IfcOpenShell 0.8.5 LGPL. APA PR154/160 PDF page/mark/SHA→PR165 IFC document reference→read-only JSON. ADAPTER 94/100, АДАПТАЦИЯ. Риск: PDF-метка не физический проём, IFC может не экспортировать связь. ГОТОВО: page/revision/SHA+IFC GlobalId либо NOT_EXPORTED.

**05. IFC 4D.** IfcOpenShell util.sequence 0.8.5 LGPL. Router→existing IFC parser→IfcTask/IfcWorkSchedule typed JSON. ADAPTER 93/100, АДАПТАЦИЯ. Риск: parent fallback recursion, nested cycle. Готовый bounded guard NOT_FOUND; недостающая обвязка: visited/None guard. ГОТОВО: 3 tasks, cycle/missing→NO_SCHEDULE, INPUT/OUTPUT раздельно.

SOURCE only, без второго исполнителя и установки.