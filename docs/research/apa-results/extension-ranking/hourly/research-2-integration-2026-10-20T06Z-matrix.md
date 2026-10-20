# APA №2 — восстановленная матрица 06Z (локальная реконструкция)

Девять маршрутов и оценки сверены с опубликованным основным 06Z-отчётом (`research-2-integration-2026-10-20T06Z.md`, GitHub blob `b32d56fcfa77aa60ee98aedc0480210d0554eab4`). **Это реконструкция таблицы, а не заявка на байтовую идентичность утраченному приложению.** LOCAL_ONLY, не GitHub ACCEPTED.

| ID | Готовая цепочка | Решение | Польза (экспертная) | Блокер / критерий |
|---|---|---|---:|---|
| I06-01 | PDFVectors PR154 → PR131 host-fit → Tapir CreateWindows/Doors → SceneWriter | ADAPTER | 100 | PDF mark→wall GUID NOT_FOUND; однозначный host, units, save/reopen |
| I06-02 | Router → Tapir Navigator tree → nonempty whitelist → Publish только с допуском | DEFER | 100 | empty selection может публиковать весь набор; error-aware tree |
| I06-03 | PR189 DXF → ezdxf 1.4.5 XClip WCS → 2D clipping | ADAPTER | 99 | nested/inverted unsupported без эталона |
| I06-04 | existing IFC → IfcDiff 0.8.5 explicit relationships → BIM Graph | REUSE | 97 | default geometry-only, opening отдельный аудит |
| I06-05 | IFC → util.system.get_ports + relation traversal → BIM Graph | REUSE | 99 | все peers и relation GUID, IFC2X3/IFC4 |
| I06-06 | Tapir GetHotlinks → при необходимости SDK29 read-only → BIM Graph | ADAPTER | 99 | node/instance/cache/proxy/source и errors |
| I06-07 | Router → PR191 limited Slab MoveElements(copy=true) → SceneWriter | REUSE LIMITED | 96 | только Basic rectangle/no holes/no SEO, не LIVE |
| I06-08 | PR190 group-intent → registered verifier → existing writer | REUSE | 95 | explicit sourceRef/memberGuids/groupGuid |
| I06-09 | Router → Tapir command error envelope → typed UNKNOWN_ERROR | REUSE | 100 | локальный APX1.5.10 SHA и 4009 negative fixture |

Версии/лицензии: Tapir1.5.9 MIT (локальный 1.5.10 непроверен); ezdxf1.4.5 MIT; IfcOpenShell0.8.5 LGPL-3.0-or-later; SDK29.3000 Graphisoft EULA. Все SOURCE, никакого нового OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED.