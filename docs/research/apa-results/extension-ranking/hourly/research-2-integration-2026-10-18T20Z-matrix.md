# APA №2 20Z — матрица интеграции 9 решений

Все оценки 0–100 — инженерная полезность, не ускорение. Не более трёх внешних звеньев. Reuse/adapter/defer; никаких вторых Router/SceneWriter/BIM Graph.

| Инструмент → существующий APA | Балл | Способ / трудоёмкость | Ограничение / ГОТОВО |
|---|---:|---|---|
| PR164 forensic | 98 | SQLite ro → ModelDump/BREP; reuse, БЫСТРО | Drift 1.5.8→1.5.10, NO RETRY; каталог+binary SHA |
| PR171 Hotlink | 96 | SceneWriter → Tapir1.5.10 → AC29; reuse, БЫСТРО | Предыдущий LIVE scratch; independent close/reopen |
| IFC MEP QA | 92 | PR165 Router → IfcOpenShell util.system → BIM Graph; adapter, АДАПТАЦИЯ | 3 fixtures, flow/owner/GUID; native MEP не доказан |
| PDF→IFC provenance | 91 | PR154 PDFVectors → IFC GUID map → api.document; adapter, АДАПТАЦИЯ | sheet/revision/SHA, 2 GlobalId, immutable originals |
| PR167 IFC/BCF | 88 | Router → B2 → BCF ZIP; reuse, БЫСТРО | BCF2.1 link/GUID readback, sidecar INSTALLED ≠ LIVE |
| 4D audit | 86 | IFC reader → util.sequence → JSON; adapter, АДАПТАЦИЯ | 3-task/cycle fixture; Gantt viewer DEFER |
| 5D cost QA | 83 | BIM Graph Qto → util.cost → JSON; adapter, АДАПТАЦИЯ | units/currency/rate, ГЭСН mapping NOT_FOUND |
| Mapped assembly | 81 | PR170 Bounds → util.placement 4×4; adapter, АДАПТАЦИЯ | 2 instances, 3 points, nonuniform/mirror |
| External library | 74 | BIM Graph → api.library → IFC copy; defer, АДАПТАЦИЯ | URI reference, не доступ к внешнему сервису |

**Два архитектурных пути 4D:** A — готовый `ifc4d-gantt 0.1.0` CLI → HTML (LGPL, ifcopenshell>=0.8.1); B — штатный `util.sequence` → текущий APA JSON evidence. A имеет HTML/внешние JS-CSS ограничения, поэтому выбрать B для безопасного read-only; A отложить. **5D:** A — `api.cost` с изменением IFC копии; B — `util.cost` только чтение Qto. Для ближайшего QA выбрать B; A после независимой проверки rate/currency.

**Безопасные ворота:** SOURCE pin/version/license → OFFLINE IFC fixtures+SHA → BUILD Win11 Python3.11/3.12 → INSTALLED wheel SHA/Router catalog → LIVE отдельно утверждённый scratch PLN → ACCEPTED независимые GUID/units/geometry. Текущий цикл только SOURCE. 8 GB VRAM не требуются для этих CPU API; 48 GB RAM не гарантируют обработку любого IFC.
