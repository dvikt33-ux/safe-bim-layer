# APA №2 21Z — интеграция 6–9
| Решение и готовая цепочка | Reuse APA, балл, трудоёмкость, риск | ГОТОВО |
|---|---|---|
| Tapir PublishPublisherSet → AC29 output | Router/Bridge; adapter **88**, БЫСТРО; пустой selectedNavigatorItemIds публикует весь набор | nonempty whitelist, unique set, output manifest |
| PR154 PDF+PR160 marks → api.document0.8.5 → IfcRelAssociatesDocument | PDF/IFC reader; adapter **85**, АДАПТАЦИЯ; native host GUID NOT_FOUND | 2 GlobalId, page/sheet/revision/source SHA |
| util.sequence0.8.5 → JSON 4D | IFC reader; reuse/adapter **82**, АДАПТАЦИЯ; cycles, setter mutates | 3 tasks/cycle/float, no setters |
| util.cost0.8.5 → QTO 5D | inspect_quantified_exchange; reuse/adapter **78**, АДАПТАЦИЯ; None≠0, rates unknown | unit/currency/source; no assign_cost_value |

Выбран путь А: существующий Router/SceneWriter/sidecar + pinned API + readback. Отклонён путь Б: новый IFC/DXF writer, SceneWriter, 4D scheduler. `ifc4d-gantt0.1.0` отложен (CDN/HTML); PyMuPDF AGPL/commercial не добавлять ради page labels, предпочесть pdfplumber. Лицензии: ezdxf MIT, Tapir MIT, IfcOpenShell LGPL-3+. AC29 entitlement отдельно; installed wheel SHA не проверен. Windows11/8GB VRAM/48GB RAM: GPU не нужен, peak RAM NOT_MEASURED.

Источники: [Tapir Publisher](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp), [IFC0.8.5](https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5), [PR154](https://github.com/dvikt33-ux/safe-bim-layer/pull/154), [PR160](https://github.com/dvikt33-ux/safe-bim-layer/pull/160).
