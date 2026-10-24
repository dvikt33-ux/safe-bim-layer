# APA №2 22Z — матрица подключения 1–5
Баллы 0–100 экспертная полезность, не скорость. Статус нового исследования SOURCE. Gate ГОТОВО означает будущую проверку, не выполненную сейчас.

| Решение | Балл; сложность; выбор | APA → готовое звено → результат | Цена/риск; ГОТОВО |
|---|---|---|---|
| IFC MEP topology | 92; БЫСТРО; REUSE | PR165 V2 → IfcOpenShell 0.8.5 util.system.get_ports/get_port_element → IFC owner/peer | LGPL3+, IFC ≠ native; 3 IFC fixtures, reciprocal GlobalId, no missing owner |
| DXF XCLIP visibility | 95; АДАПТАЦИЯ; ADAPTER | PR168 C1 → ezdxf 1.4.5 Frontend+CustomJSONBackend → visible 2D JSON | MIT, no source handles; raw/visible, inverse clip and MINSERT fixtures |
| IFC PDF provenance | 88; АДАПТАЦИЯ; ADAPTER | PR154 PDFVectors + PR160 mark → IfcOpenShell 0.8.5 document API → IFC copy | LGPL3+, PDF rights; SHA/page/revision, 2 GlobalId, relation readback |
| DXF MINSERT cells | 90; АДАПТАЦИЯ; ADAPTER | PR168 C1 → ezdxf.multi_insert → cell-level geometry report | MIT; zero spacing/OCS; 2×3 fixture, exactly 6 unique locations or explicit collapse |
| Publisher | 91; АДАПТАЦИЯ; ADAPTER | APA Router → Tapir PublishPublisherSet (tag1.5.9 source) → native AC29 SDK29 | proprietary Graphisoft+Tapir, local 1.5.10 unknown; nonempty whitelist, unique set, sandbox, manifest |

Источники: https://github.com/mozman/ezdxf/tree/v1.4.5/src/ezdxf/addons/drawing
https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell
https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___project_operation.html
