# APA №2 — 24.10.2026 03Z | 26 SOURCE-проверок (не 26 независимых документов)

**Метод:** каждый пункт ниже сверялся с фактически прочитанным текстом GitHub-коннектора или официальным первоисточником; несколько проверок одного файла — **один источник**, но разные утверждения. Не выполнять OFFLINE/LIVE. MODEL_MODE_NOT_VERIFIABLE.

| № | Предмет | Проверенное доказательство | Статус |
|---:|---|---|---|
| 01 | Branch | GitHub search_branches вернул `research/apa-extension-ranking-hub-20261018` | PASS |
| 02 | P0 | GitHub issue #192: G0→G5, одно новое native здание, старый CREATE не повторять | PASS |
| 03 | NEXT | `docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md`, blob `6f074693...`: SOURCE не равно BUILD | PASS |
| 04 | Pivot | `research-1-20261023T11Z-TRIAD-PIVOT.md`, blob `896fa3af...`: без нового writer, G3 без разрешения | PASS |
| 05 | №1 свежий | `research-1-20261024T03Z-TRIAD-DUPLICATE-CONTENT-CACHE-IDENTITY.md`, blob `eb5bb3f...`: Content Cache identity hazards | PASS |
| 06 | №3 доступность | hourly directory listing: последние найденные `audit-2026-10-20-18-A/B.md`; более свежего №3 не обнаружено | PASS / STALE_AUDIT |
| 07 | Матрица | `priority_matrix_20261018.json`: count=61, items.length=61, unique ID=61, blob `9cb5e6f...` | PASS |
| 08 | Authored schema | PR74 `archicad_project_accelerator.py` строки 265–277: schema `apa-authored-project/1`, units meters, exact target path | PASS |
| 09 | Authored read-only | PR74 `run_project` строки 428–443: authored требует `preflight/execute` и callable transport, не offline | PASS |
| 10 | Native allowlist | PR74 `compile_authored_intent` строки 288–295: 5 команд (Columns/Doors/Windows/Walls/Roofs) | PASS |
| 11 | Native max | тот же файл: `nativeComponents` list, `len>100` запрещён | PASS |
| 12 | Roof typed | тот же файл строки 296–302: Roof 1 row, floorIndex, pivotLine, Basic, buildingMaterialId | PASS |
| 13 | Roof envelope | тот же файл строки 303–314: polygonCoordinates внутри outline ±0.35 м | PASS |
| 14 | Roof sample | `examples/accelerator/model-first-building.json`: outline 142..152 / 40..48; Roof polygon 141.85..152.15, 39.840004166..48.140004166 | PASS |
| 15 | Rectangles | `archicad_semantic_spatial.py`: outline и room rectangles xMin/xMax/yMin/yMax | PASS |
| 16 | Orthogonal axes | тот же файл: только `X`/`Y` и wall-on-room-boundary | PASS |
| 17 | Slab level | `archicad_authored_native_plan.py` строки 105–108: CreateSlabs level=float(story.level), абсолютный Z | PASS |
| 18 | Story constraints | тот же файл строки 35–43: 2.4≤height≤4.5 и согласованность level+height | PASS |
| 19 | AC target guard | `archicad_scene_run.py` строки 27, 50–79, 140–163: expected path/Tapir 1.5.10 и bind authorized saved copy | PASS |
| 20 | Live Connection build | Graphisoft official download: AC29 Windows build3000, Rhino7/8, 01.10.2025 | PASS |
| 21 | RhinoCode version | McNeel CLI guide: `rhinocode` штатно в Rhino >=8.11, script server отдельно запускается | PASS |
| 22 | RhinoCode identity | McNeel CLI guide: `list --json` выдаёт processId, processVersion, activeDoc.title/location | PASS |
| 23 | Cache replace | McNeel Content Cache Updated Guide 17.05.2024: Push/Bake с ID заменяет; Bake без ID создаёт новый | PASS |
| 24 | Cache freeze | тот же McNeel: Action False не отключает Pull при видимом Result; Purge может удалять definitions | PASS |
| 25 | Cache versions | та же ветка, посты разработчика #16/#20: fix reset 8.9, append 8.11 | PASS |
| 26 | jSwan license | `andrewheumann/jSwan/LICENSE`: MIT License, Copyright 2024 Andrew Heumann | PASS |

**Первичные ссылки:** https://developer.rhino3d.com/en/guides/scripting/advanced-cli/ ; https://discourse.mcneel.com/t/content-cache-updated-guide/181883 ; https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ ; https://github.com/andrewheumann/jSwan/blob/master/LICENSE ; https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_semantic_spatial.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py .

**Итог:** 26 документарных проверок PASS; это не OFFLINE, INSTALLED, LIVE или ACCEPTED.
