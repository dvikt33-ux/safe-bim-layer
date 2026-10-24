# APA №2 | 2026-10-24 12Z | 30 предметных SOURCE-проверок

**Подсчёт:** 30 конкретных проверяемых утверждений по реально прочитанным в этом проходе первоисточникам и репозиторным файлам. Источники повторяются; это НЕ 30 независимых сайтов, НЕ OFFLINE/INSTALLED/LIVE. Все SOURCE_ONLY. Исторические документы помечены.

| № | Проверка | Доказательство |
|---:|---|---|
| 01 | BUILD-01 требует новой нативной двухэтажной модели и G0–G5 | [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) |
| 02 | Главный P0 — инженерная сборка, не число исследований | [NEXT_RESEARCH_PRIORITIES](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md) |
| 03 | №2 обязан искать готовый AC29+Rhino8+GH маршрут без нового writer/router | [TRIAD-PIVOT](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md) |
| 04 | Матрица содержит count=61 и items=61 | [priority_matrix](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json), JSON прочитан |
| 05 | У 61 элементов матрицы уникальные id; формула priority явно задана | [priority_matrix](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json), поля id/method |
| 06 | Исторический PROJECT_PLAN revision=182 | [PROJECT_PLAN](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/control/PROJECT_PLAN.json), JSON read-only |
| 07 | №1 10:56Z: Speckle Rhino/GH→AC даёт GDL, не native Wall/Slab/Roof | [№1](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261024T1056Z-TRIAD-SPECKLE-RHINO-REFERENCE-QA.md) |
| 08 | Последний доступный прочитанный №3 20.10 07Z не подтверждает BUILD-01 | [№3](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-07.md) |
| 09 | Официальный GH–AC29 add-on build3000, дата 01.10.2025 | [Graphisoft](https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/) |
| 10 | Официальный GH–AC29 add-on Windows поддерживает Rhino 7/8 | [Graphisoft](https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/) |
| 11 | AC30 build3000 в каталоге — отдельный add-on, не AC29 | [Graphisoft](https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/) |
| 12 | Live Connection несовместим с Start Edition | [Graphisoft](https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/) |
| 13 | AC29 GH Design native elements при создании locked, не preview | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf), Important Notes |
| 14 | GH-uncontrolled параметры берутся из текущих AC Tool Default Settings при создании | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf), Important Notes |
| 15 | GH-controlled значения имеют приоритет при последующем исполнении GH | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf), Important Notes |
| 16 | AC-only / uncontrolled параметры могут сохраниться после GH re-execution | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf), Important Notes |
| 17 | Lock/Unlock GH Elements: relock возвращает GH-controlled значения | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf), Palette |
| 18 | Select in GH указывает генерирующий компонент только для GH-generated элементов | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf), Palette |
| 19 | Sync Changes to GH ON автоматически обновляет connected AC references в GH | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf), Palette |
| 20 | GH Design Synchronize=False выдаёт Null, не гарантирует удаления AC элемента | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf), Synchronize; отрицательная граница |
| 21 | GH-created AC elements после Save/Open могут оставаться без исходного .gh | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf), File Handling |
| 22 | В одном Rhino может быть несколько .gh, но только один .gh соединён с AC | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf), File Handling |
| 23 | Открытый ожидающий диалог AC приостанавливает GH connection, pending inputs ждут | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf), Suspended Connection |
| 24 | Copy/Paste GH-created элемента в AC создаёт копию без связи с GH code | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf), Important Notes |
| 25 | Rhino8 Content Cache Push отслеживает и обновляет объект вместо бесконечного Bake | [McNeel Rhino8](https://www.rhino3d.com/features/grasshopper/content-cache/) |
| 26 | McNeel Content Cache Pull включает Rhino object ID, Bake без ID может создавать копии | [McNeel developer guide](https://discourse.mcneel.com/t/content-cache-updated-guide/181883/1) |
| 27 | McNeel Content Cache Purge затрагивает объекты/неиспользуемые определения слоёв/материалов/блоков | [McNeel developer guide](https://discourse.mcneel.com/t/content-cache-updated-guide/181883/1) |
| 28 | PR74 nativeComponents whitelist не содержит CreateBeams | [PR74 code](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L288-L296) |
| 29 | PR74 CreateRoofs только Basic/pivotLine/material и envelope margin 0.35m | [PR74 code](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L297-L313) |
| 30 | Existing connected CLI требует exact whole inventory; preflight bind 19724 и execute fresh plan hash | [CLI inventory](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L425-L440), [preflight](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L528-L575) |

**Вывод:** проверены интерфейсы, но не локальные APX/PLN/Rhino/GH. Любое повышение до INSTALLED/LIVE/ACCEPTED без отдельного receipt запрещено. MODEL_MODE_NOT_VERIFIABLE.
