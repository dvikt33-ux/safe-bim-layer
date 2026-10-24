# APA №2 22Z — матрица 6–9
Новые пути SOURCE; исторический LIVE Hotlink отдельно. Баллы экспертные.

| Решение | Балл; решение | Готовая цепочка | Цена/риск; ГОТОВО |
|---|---|---|---|
| Hotlink batch | 96; БЫСТРО; REUSE | PR171/173 → SceneWriter+Tapir CreateHotlinkInstances → AC29 | LIVE-02: 2 шт saved/reopened snapshot, не replay; 0 rotation/nonmirror |
| IFC mapped geometry | 86; АДАПТАЦИЯ; REUSE | PR170 B3 → IfcOpenShell 0.8.5 util.placement → world AABB | LGPL3+, TODO 2D; mirror/nonuniform, units, two instances |
| IFC 4D read-only | 76; АДАПТАЦИЯ; REUSE | APA IFC → util.sequence.get_work_schedule_tasks/get_task_outputs → JSON | LGPL3+, нет viewer; 3 tasks/cycle/date, no cascade writes |
| IFC 5D read-only | 79; АДАПТАЦИЯ; REUSE | APA QTO → util.cost.get_cost_items_for_product/get_total_quantity → JSON | LGPL3+, цены не подтверждены; missing/zero/unit/rate, no write |

Граф: AC29 IFC export (не проверен здесь) → APA file sidecar → pinned IfcOpenShell → JSON evidence → Router/Graph. Второй исполнитель не нужен. VRAM 8 GB не требуется; 48 GB RAM не benchmark.

Источники:
https://github.com/dvikt33-ux/safe-bim-layer/pull/173
https://github.com/dvikt33-ux/safe-bim-layer/pull/170
https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util
