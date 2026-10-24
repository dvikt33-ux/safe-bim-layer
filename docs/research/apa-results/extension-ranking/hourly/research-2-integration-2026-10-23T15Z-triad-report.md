# APA №2 — 2026-10-23 15Z — инженерный отчёт: BUILD-01 / Rhino8 / GH / AC29

## Новый вклад в G1/G2 — P=100/100
**Исправлена ложная альтернатива «сложная кровля невозможна или уже готова»:** pinned Tapir 1.5.10 CreateRoofs поддерживает native MultiPlane по умолчанию (без pivotLine), levels до 16. PR82 исторически подтверждает 4-plane hip roof и GUID-preserving edit. Но PR74 authored compiler требует pivotLine, Basic, buildingMaterialId в nativeComponents, то есть пропускает лишь SinglePlane. **Точный барьер:** `BLOCKER_ROOF_MULTIPLANE_AUTHORED_NOT_WIRED`. Не создавать новый writer: сначала проверить подключение существующего PR82 маршрута к одному SceneWriter. Произвольный Rhino NURBS→same GUID native Roof NOT_FOUND.

**Второй вклад G2 — P=99/100:** CreateSlabs в pinned Tapir 1.5.10 имеет `favoriteName` (наследует настройки Favorite), но не имеет `structureType/buildingMaterialId`; PR74 compile_candidate не подаёт favoriteName. SceneWriter реально выполняет CreateSlabs→readback→ModifySlabs→readback с durable SQLite state `BASIC_MODIFY_ATTEMPTED`. Однопроходная Basic Slab через Favorite в текущем authored pipeline **NOT_WIRED**, второй WRITE нельзя замалчивать.

**Третий вклад G1 — P=100/100:** Semantic Brief `GENERATE_FROM_ZERO` только описывает этажи, НЕ создаёт новую PLN или stories. Нужна НОВАЯ подготовленная scratch PLN с реальными story index/floorId/level и разрешённым путем. `ADAPT_EXISTING` не означает повтор старого CREATE.

## Безопасная воспроизводимая цепочка — кандидат, не LIVE
1. **G0 READ:** GetProjectInfo/GetStories/GetAddOnVersion, installed APX SHA + runtime command inventory/schema, материалы/Favorites/GDL, Archicad 29 build5101, Rhino8, Graphisoft AC29 Live Connection build3000, отдельная scratch PLN. Provider version ≠ installed contract.
2. **GH/Rhino:** считать outline, bearingLines, storyHeights, толщины, roof slope, координаты проёмов. jSwan MIT Serialize/Merge JSON + GH Panel Stream Destination → отдельный staging JSON. Остановить поток, проверить JSON parse, типы, units=meters, exact targetProjectPath/story/material bindings и SHA; Rhino8+jSwan compatibility NOT_VERIFIED. Это **one-way file handoff**, не трёхсторонняя синхронизация.
3. **G1 READ-only:** existing PR74 `--intent` + `--preflight` → BIM Graph, topological order, hostWall GUID refs, collision/plan hash; требует реального Archicad READ. `evidenceKind=LIVE` на preflight НЕ CREATE.
4. **G2:** native Walls/Slabs/Columns/SinglePlane Roof/Doors/Windows, Beam adapter NOT_WIRED, MultiPlane PR82 отдельно, GDL libPart expectations только при заполнении. Pinned schema не подменяет installed runtime.
5. **G3 только после отдельного допуска:** SceneWriter/SQLite единственный native writer, intent-before-write, confirm plan hash, отдельно разрешённый ModifySlabs, no duplicate CREATE. GH Live Connection Design native WRITE для APA-owned элементов выключить. UNKNOWN/timeout → STOP и READ reconciliation, не автоматический rollback.
6. **G4/G5:** GUID/BIM type/story/host/GDL/material/BREP readback → GuardedSave → GUI Close/Reopen → independent readback; второе отличающееся задание на другой новой scratch PLN. До этого BUILD-01 не ACCEPTED.

## Ограничения совместного моделирования
- Rhino→GH: вычисление геометрии, не BIM.
- GH→APA: staging JSON, one-way, не continuous.
- APA→AC: только санкционированный native writer SceneWriter.
- AC→GH: Graphisoft Parameter/Deconstruct + Send Changes, ограниченный READ. MultiPlane Roof Deconstruct НЕ поддерживается.
- GH→AC: Graphisoft Design создаёт native элементы вне SQLite APA и может пересоздавать GUID при пересчёте; не считать общим журналом/владением.
- Полная автоматическая двусторонняя AC↔GH↔Rhino same-GUID sync: NOT_FOUND.
- Нормативные проверки параметров GH (габариты, уклоны, доступность, эвакуационные размеры) — предварительные расчёты, не официальная экспертиза.

## Состояние и доказательность
SOURCE=30 предметных утверждений в checks.md, 10 сценариев в matrix.md, два самостоятельных SOURCE-контрааудита в audits.md. **OFFLINE=0, BUILD=0, INSTALLED=0, LIVE=0, ACCEPTED=0.** G0 BLOCKED_RUNTIME; G1 SOURCE_CANDIDATE_NOT_RUN; G2 SOURCE_ONLY, Roof MultiPlane/Beam/Favorite NOT_WIRED; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN.
Прочитаны BUILD-01 issue #192, NEXT, TRIAD-PIVOT №1, матрица 61, предыдущие №2 и ссылки на №3 из NEXT. Новый отдельный №3 за 23.10 не подтверждён. PROJECT_PLAN rev182 по проверенным путям не найден и не менялся. 06Z по предыдущим отчётам PARTIAL_NOT_ACCEPTED.
Никаких изменений main/NEXT/code/PLN/APX, установок, LIVE, merge, Work/Codex/Arena/paid API. MODEL_MODE_NOT_VERIFIABLE.

## Первоисточники
- https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py
- https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_authored_native_plan.py
- https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_semantic_brief.py
- https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py
- https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json
- https://github.com/dvikt33-ux/safe-bim-layer/pull/82
- https://github.com/dvikt33-ux/safe-bim-layer/issues/192
- https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
- https://help.graphisoft.com/AC/29/INT/GC.pdf
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-56.htm
- https://github.com/ENZYME-APD/tapir-archicad-automation
- https://github.com/andrewheumann/jSwan
- https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm
