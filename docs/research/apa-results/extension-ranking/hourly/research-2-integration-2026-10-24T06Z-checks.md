# APA №2 | 2026-10-24 06Z | 28 SOURCE-проверок

Это 28 **предметных документарных/кодовых сверок**, не 28 запусков программ. Проверены GitHub research branch, immutable PR74, официальные Graphisoft источники; расчёты матрицы сделаны непосредственно из JSON. Все SOURCE_ONLY.

| № | Проверенный контракт/факт | Результат | Источник |
|---|---|---|---|
| 01 | Issue #192 открыт, P0 BUILD-01 | PASS | https://github.com/dvikt33-ux/safe-bim-layer/issues/192 |
| 02 | PR74 открыт как draft, не merged | PASS | https://github.com/dvikt33-ux/safe-bim-layer/pull/74 |
| 03 | PR74 head=5a3a9201a715a5528c93bed4a5318e2acb32eea7 | PASS | https://github.com/dvikt33-ux/safe-bim-layer/pull/74 |
| 04 | TRIAD-PIVOT прочитан | PASS | https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md |
| 05 | NEXT находится в extension-ranking, а не в корне | PASS | https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md |
| 06 | priority_matrix: declared=61, actual=61 | PASS | https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json |
| 07 | priority_matrix: unique ID=61 | PASS | https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json |
| 08 | priority_matrix: formula mismatches=0/61 | PASS | https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json |
| 09 | №1 0601Z: AC→GH и GDL ownership изучены | PASS | https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261024T0601Z-TRIAD-AUTO-SYNC-LIBPART-OWNERSHIP.md |
| 10 | №2 05Z: dual IFC QA и G0 BLOCKED | PASS | https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-2-integration-2026-10-24T05Z-report.md |
| 11 | №3 последний обнаруженный audit 20.10 18Z; устарел | PASS/STALE | https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md |
| 12 | Graphisoft AC29 Live Connection Windows build3000, Rhino7/8 | PASS | https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/ |
| 13 | Graphisoft AC29 Live Connection дата 01.10.2025 | PASS | https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/ |
| 14 | GH Design/Document Synchronize TRUE: GH→AC automatic | PASS | https://help.graphisoft.com/AC/29/INT/GC.pdf#page=17 |
| 15 | GH Design/Document Synchronize FALSE: Null output, no new element | PASS | https://help.graphisoft.com/AC/29/INT/GC.pdf#page=17 |
| 16 | Boolean Toggle может управлять группой Synchronize | PASS | https://help.graphisoft.com/AC/29/INT/GC.pdf#page=17 |
| 17 | GH Synchronize требует активного AC-GH Connection | PASS | https://help.graphisoft.com/AC/29/INT/GC.pdf#page=17 |
| 18 | AC29 Deconstruct Roof поддерживает только Single-Plane Roof | PASS | https://help.graphisoft.com/AC/29/INT/GC.pdf#page=40 |
| 19 | AC29 Deconstruct возвращает reference geometry и Settings | PASS | https://help.graphisoft.com/AC/29/INT/GC.pdf#page=40 |
| 20 | Deconstruct Brep: Beam/Column/Slab/Wall/Mesh/Zone/Shell/Single-Plane Roof | PASS | https://help.graphisoft.com/AC/29/INT/GC.pdf#page=41 |
| 21 | GH Property Settings может overwrite AC Properties | PASS | https://help.graphisoft.com/AC/29/INT/GC.pdf#page=46 |
| 22 | GH Create New Library Part пишет Embedded Library | PASS | https://help.graphisoft.com/AC/29/INT/GC.pdf#page=45 |
| 23 | Удаление/переключение GH Object Settings удаляет generated Library Part | PASS | https://help.graphisoft.com/AC/29/INT/GC.pdf#page=45 |
| 24 | PR74 nativeComponents allowlist без CreateBeams | PASS | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L288-L320 |
| 25 | PR74 CreateRoofs требует typed Basic Single-Plane/pivotLine/material | PASS | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L295-L312 |
| 26 | PR74 roof outline margin 0.35 m | PASS | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L305-L311 |
| 27 | PR74 CreateSlabs.level абсолютная Z | PASS | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py#L103-L112 |
| 28 | PR74 roof junction completion требует одну native Roof | PASS | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_extension.py#L243-L260 |

**Дополнительное историческое наблюдение, не входит в 28:** Graphisoft Community 2020 сообщает, что Synchronize=False ставит ранее созданные элементы на паузу, но **AC29 LIVE_NOT_VERIFIED**: https://community.graphisoft.com/t5/Parametric-design/Synchronize-Bug/m-p/292446/highlight/true .

**Не засчитывать как SOURCE PASS:** автоматический GH→authored JSON адаптер; multi-plane native roundtrip; единый Rhino/AC GUID; atomic triad rollback; автоматическая нормативная экспертиза. Это NOT_FOUND/NOT_PROVEN, а не подтверждённые функции.
