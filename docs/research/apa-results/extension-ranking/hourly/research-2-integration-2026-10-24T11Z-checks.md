# APA №2 | 2026-10-24 11Z | 29 проверенных SOURCE-утверждений

**Правило подсчёта:** 29 конкретных утверждений по фактически прочитанным материалам; источники повторяются, это НЕ 29 независимых сайтов и НЕ 29 LIVE-тестов. Статус всех строк SOURCE_ONLY. Ссылки на исторические версии не подтверждают поведение AC29 build5101.

| № | Проверенное утверждение | Доказательство / статус |
|---:|---|---|
| 01 | BUILD-01 требует новую нативную двухэтажную модель, G0–G5 и новый scratch | [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) SOURCE |
| 02 | Административный P0 — BUILD-01 выше числа отчётов | [NEXT_RESEARCH_PRIORITIES](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md) SOURCE |
| 03 | №2 обязан искать готовые AC29+Rhino8+GH маршруты без writer/router | [TRIAD-PIVOT](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md) SOURCE |
| 04 | Матрица имеет count=61 и 61 фактический item | [priority_matrix](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json) SOURCE, JSON parsed |
| 05 | Все 61 ID уникальны, все 61 `priority` совпадают с формулой 12*need+7*(5-effort)+confidence | [priority_matrix](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json) SOURCE, JS recomputation |
| 06 | Исторический `PROJECT_PLAN.json` revision=182 | [PROJECT_PLAN](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/control/PROJECT_PLAN.json) SOURCE read-only |
| 07 | Graphisoft официальный AC29 GH add-on Windows build3000, Rhino7/8, дата 01.10.2025 | [Graphisoft](https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/) SOURCE |
| 08 | Официальный каталог отдельно содержит AC30 build3000, но это НЕ AC29 add-on | [Graphisoft](https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/) SOURCE |
| 09 | Live Connection несовместим с Archicad Start Edition | [Graphisoft](https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/) SOURCE |
| 10 | AC29 `Sync Changes to GH` ON непрерывно автоматически обновляет connected GH reference | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf) SOURCE |
| 11 | `Select in GH` трассирует только GH-generated selected AC elements | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf) SOURCE |
| 12 | `Lock/Unlock GH Elements`: relock восстанавливает GH-controlled values; AC-only параметры могут сохраниться | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf) SOURCE |
| 13 | GH Design `Synchronize=True` запускает синхронизацию в Archicad | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf) SOURCE |
| 14 | GH Design `Synchronize=False` возвращает GH output `Null` | [AC29 GC](https://help.graphisoft.com/AC/29/INT/GC.pdf) SOURCE |
| 15 | FALSE/disabled GH оставлял существующие AC Wall/Window/Object в опыте 2020 | [Graphisoft Community](https://community.graphisoft.com/t5/Parametric-design/Synchronize-Bug/td-p/292443) HISTORICAL SOURCE |
| 16 | Исторический Stream Filter/empty input — отдельный deletion workaround, не `False` | [Graphisoft Community](https://community.graphisoft.com/t5/Parametric-design/Synchronize-Bug/td-p/292443) HISTORICAL SOURCE |
| 17 | Исторический User Guide 2.3 утверждает сохранение GH-generated AC elements после Save/Open без GH code | [Graphisoft 2.3](https://gsdownloads.graphisoft.com/cdn/ftp/techsupport/documentation/addons/archicad-rhino-grasshopper/AC-Grasshopper%20Connection%20User%20Guide%202.3.pdf) HISTORICAL SOURCE |
| 18 | В обсуждении 2026 пользователь описал AC29/Rhino8 двухпалитровое подключение на Windows | [Graphisoft Community](https://community.graphisoft.com/t5/Parametric-design/Archicad-29-and-Rhino-8-grasshopper-connection-issue/td-p/695667) ANECDOTAL SOURCE |
| 19 | Последний №1 10:56Z отверг Speckle Rhino/GH→AC GDL как native Wall/Roof writer | [№1](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261024T1056Z-TRIAD-SPECKLE-RHINO-REFERENCE-QA.md) SOURCE |
| 20 | №1 06:01Z документировал AC→GH automatic и GH GDL library part ownership | [№1](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261024T0601Z-TRIAD-AUTO-SYNC-LIBPART-OWNERSHIP.md) SOURCE |
| 21 | Authored PR74 schema строго `apa-authored-project/1`, units meters, exact target path | [code L263–281](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L263-L281) SOURCE |
| 22 | Authored nativeComponents максимум 100 | [code L288–290](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L288-L290) SOURCE |
| 23 | Authored nativeComponents whitelist не включает `CreateBeams` | [code L293–296](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L293-L296) SOURCE |
| 24 | Authored CreateRoofs требует Basic/pivotLine/material и envelope margin .35m | [code L297–313](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L297-L313) SOURCE |
| 25 | Authored native plan создаёт 1 footprint slab на этаж | [code L77–112](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py#L77-L112) SOURCE |
| 26 | Authored CreateSlabs level = absolute `s.level`, floorIndex=native | [code L110–119](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py#L110-L119) SOURCE |
| 27 | Connected CLI Beam требует explicit Basic straight section, 1 элемент на write | [code L95–110](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L95-L110) SOURCE |
| 28 | Connected CLI `verify_inventory` сравнивает exact inventory включая чужие GUID | [code L425–440](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L425-L440) SOURCE |
| 29 | Connected preflight port19724, expected inventory, retained geometry hash; execute требует fresh hash | [code L528–575](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L528-L575) SOURCE |

**Не подтверждено:** AC29 локально INSTALLED, exact Rhino8 SR, реальное поведение GH FALSE/deletion/SaveOpen в BUILD-01, автоматический GH→authored JSON, Multi-Plane Roof roundtrip, native GUID-preserving three-way sync. Никакого повышения SOURCE до LIVE/ACCEPTED.
