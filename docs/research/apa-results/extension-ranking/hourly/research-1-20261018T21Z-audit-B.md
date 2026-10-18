# APA №1 21Z — контрааудит Б: польза, дублирование, риски

1. PR154 PDFVectors уже извлекает векторную геометрию; PR165/170 уже дают IFC sidecar/geometry; PR159/162/164 имеют native group/CloneNativeGroupV1; PR171 single Hotlink LIVE; PR173 batch НЕ LIVE. Второй writer/Router/parser/Clone не нужен.
2. ezdxf recursive_decompose MINSERT уже реализован, но zero spacing делает unique count меньше row×col; XCLIP не применяется. При active clipping точный DXF→BIM должен выдавать UNCERTAIN, а не успех.
3. IfcOpenShell 0.8.5 Axis2 mirror и Scale2/3 присутствуют, но TODO2d остаётся. PR170 world bounds не гарантирует полную сохранность матриц. Проверять существующий маршрут, не писать новый IFC geometry engine.
4. ifc4d-gantt README «standalone HTML» противоречит двум CDN ссылкам в source. Неэкранированные HTML поля и JSON внутри script создают потенциальный риск при недоверенном IFC; никакой exploit не исполнялся, только SOURCE_RISK.
5. Publisher SAF UI не закрывает канонический A11.S08 BLOCKED; IFC port read-only не закрывает A11.S10 BLOCKED. Нет benchmark 100× и новых ACCEPTED.
6. Официальные https://fgiscs.minstroyrf.ru/frsn/fsnb и /prices возвращали 403 в ChatGPT web; структура, лицензия и актуальные цены NOT_VERIFIED. Никаких фиктивных сметных данных.
7. Баллы карточек — инженерный приоритет, не ускорение; БЫСТРО/АДАПТАЦИЯ/ДОЛГО — трудоёмкость, не статус реализации. PR receipts не переисполнялись.

Вердикт: полезные новые ограничения и точные upstream контракты подтверждены SOURCE, интеграция/производственные изменения не разрешались и не проводились. Никаких main/PLN/APX/plan182/NEXT_RESEARCH_PRIORITIES.md изменений.