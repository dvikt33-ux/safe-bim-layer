# APA №2 | 2026-10-24 05Z | 26 предметных SOURCE-проверок

Метод: 26 **раздельных проверенных утверждений**, не 26 независимых документов; проверка GitHub connector (конкретная ветка/immutable PR74) и официальной документации Graphisoft AC29. Никакого OFFLINE/INSTALLED/LIVE/ACCEPTED. Исторические утверждения не объявляются локальным PASS.

| № | Проверенный факт | Источник / предел | Статус |
|---:|---|---|---|
| 01 | BUILD-01 #192 требует G0–G5, единственный SceneWriter и отдельный G3 допуск | https://github.com/dvikt33-ux/safe-bim-layer/issues/192 | SOURCE_PASS |
| 02 | PR74 open/draft, исторические 21 элемента не новая BUILD-01 | https://github.com/dvikt33-ux/safe-bim-layer/pull/74 | SOURCE_PASS |
| 03 | NEXT находится в docs/research/apa-results/extension-ranking/, приоритет целое здание | blob 6f074693360231c5cb42ada815984a6b0dd504c0 | SOURCE_PASS |
| 04 | Pivot №1 11Z требует триаду без нового writer | blob 896fa3af0953468ca58fca710f32cb926504f582 | SOURCE_PASS |
| 05 | Матрица декларирует count=61; её items не пересчитывались в этом проходе | blob 9cb5e6f2a59f80762cc77073eeb10404829af75a | SOURCE_PASS_LIMITED |
| 06 | Свежий №1 04:58Z описывает IFC Roof/Shell type collision | blob 12aa05b3f2dba73006084ce8428bdb67a67e672e | SOURCE_PASS |
| 07 | Доступный №3 20.10 18Z не является новым G0 runtime receipt | hourly/audit-2026-10-20-18-A.md | SOURCE_PASS_STALE |
| 08 | PR74 authored schema `apa-authored-project/1`, units=meters, target PLN strict | immutable 5a3a9201, scripts/archicad_project_accelerator.py lines 262–277 | SOURCE_PASS |
| 09 | `nativeComponents` allowlist Columns/Doors/Windows/Walls/Roofs | immutable 5a3a9201, project_accelerator.py lines 288–296 | SOURCE_PASS |
| 10 | `nativeComponents` максимум 100 дополнительных шагов | тот же исходник, lines 287–290 | SOURCE_PASS |
| 11 | SinglePlane Roof требует Basic, pivotLine, material и polygon внутри outline±0.35m | тот же исходник, lines 297–311 | SOURCE_PASS |
| 12 | Authored offline mode запрещён, требуется read-only preflight transport | тот же исходник, lines 428–443 | SOURCE_PASS |
| 13 | PR74 требует фактические story bindings, CSE material GUID, heights 2.4–4.5m | immutable 5a3a9201, scripts/archicad_authored_native_plan.py lines 20–70 | SOURCE_PASS |
| 14 | Slab `CreateSlabs.level` абсолютный project Z, один прямоугольный footprint на этаж | тот же файл lines 78–113 | SOURCE_PASS |
| 15 | Roof SEO extension требует ровно один Roof и upper Walls | immutable 5a3a9201, scripts/archicad_authored_extension.py lines 243–257 | SOURCE_PASS |
| 16 | Roof holes блокируются, SEO operation `SubtractionUpwards` | тот же файл lines 260–333 | SOURCE_PASS |
| 17 | Graphisoft AC29 Live Connection build3000 Windows Rhino7/8, 01.10.2025 | https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/ | SOURCE_PASS / INSTALLED_UNKNOWN |
| 18 | IFC mapping by Element Type: native Roof и Shell оба `IfcSlab.ROOF` | https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-51.htm | SOURCE_PASS |
| 19 | IFC mapping by Classification зависит от настроек translator | https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-35.htm | SOURCE_PASS |
| 20 | IFC BREP точно передаёт junctions, но в IFC теряются редактируемые параметры | https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-37.htm lines 47–61 | SOURCE_PASS |
| 21 | IFC Parametric сохраняет параметры, но может терять спец. junctions/skins | тот же источник lines 63–89 | SOURCE_PASS |
| 22 | Export gross geometry игнорирует вырезы в host; отключение может дать BREP | тот же источник lines 39–45 | SOURCE_PASS |
| 23 | Collision filter и Split/Explode composite меняют геометрию/структуру IFC | тот же источник lines 21–24, 125–164 | SOURCE_PASS |
| 24 | IFC Building Material properties/Element/Component/Door-Window/Base Quantities — отдельные флаги; IFC2x3 vs IFC4 отличаются | https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-42.htm lines 15–80 | SOURCE_PASS |
| 25 | IFC Unit Conversion имеет отдельный preset; Story GlobalId может совпасть в двух проектах | https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-43.htm ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-48.htm lines 56–64 | SOURCE_PASS |
| 26 | IFC Space Containment только Object/Lamp/Morph/Slab, Space Boundaries дают IfcRelSpaceBoundary | https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-42.htm lines 85–99 | SOURCE_PASS |

**Итог: 26 утверждений, 0 новых runtime проверок.** В частности, source `GetModelDumpV1` не доказывает локальную регистрацию команды; полноценная AC↔GH↔Rhino GUID-preserving sync NOT_FOUND.
