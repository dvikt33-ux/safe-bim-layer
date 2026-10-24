# APA №2 | 2026-10-24 08Z | SOURCE-проверки (реестр 33 утверждений)

**Метод:** отдельные проверяемые утверждения из фактически прочитанных GitHub issue/files, официальных страниц Graphisoft и индексированных выдержек официального GC.pdf (стр.28/40). Это не 33 уникальных сайтов и не 33 runtime-запусков. Дополнительные проверки матрицы выполнены через JSON.parse и JS recompute. Верификация публикации отдельно в index.

| № | Проверенное утверждение | Первичный источник |
|---:|---|---|
| 1 | Issue #192 требует новое целое здание, не число отчётов | [I](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) |
| 2 | Issue #192 требует G0–G5 и запрещает повтор старого CREATE | [I](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) |
| 3 | Issue #192 требует отдельного разрешения scratch PLN на G3 | [I](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) |
| 4 | NEXT расположен внутри extension-ranking | [N](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md) |
| 5 | TRIAD-PIVOT требует триаду и раздельные статусы | [P](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md) |
| 6 | Матрица count=61 и фактически 61 entries | [M](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json) |
| 7 | Все 61 ID матрицы уникальны | [M](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json) |
| 8 | Формула приоритета совпадает 61/61 | [M](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json) |
| 9 | PR74 authored schemaVersion=apa-authored-project/1 и units=meters | [C](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 10 | PR74 brief.targetProjectPath == RUN.EXPECTED_PATH | [C](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 11 | PR74 schema provenance требует live origin/provider_version и SHA двух JS | [C](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 12 | PR74 schema сравнивается с повторно распарсенным каталогом | [C](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 13 | PR74 nativeComponents ограничен 100 | [C](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 14 | PR74 nativeComponents allowlist без CreateBeams | [C](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 15 | PR74 Roof требует pivotLine, Basic, buildingMaterialId | [C](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 16 | PR74 Roof ограничен outline margin=0.35m | [C](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 17 | PR74 authored slab: один footprint на этаж | [S](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py) |
| 18 | PR74 slab level абсолютная Z | [S](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py) |
| 19 | PR74 authored offline mode отвергается | [C](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 20 | PR74 authored preflight требует callable transport | [C](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 21 | PR74 guarded_project вызывается перед authored compilation | [C](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 22 | PR74 execute требует run_id и matching confirmPlanHash | [C](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 23 | RUN saved-copy binding требует path/name/SHA256/authorization_ref | [R](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py) |
| 24 | Официальный AC29 GH Live Connection build3000 поддерживает Windows/Rhino7/8 | [D](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/) |
| 25 | GH Roof planar polygon задаёт contour/pitch/elevation | [G](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| 26 | GH Roof Favorite pitch/offset не влияют при planar polygon | [G](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| 27 | GH Deconstruct Roof не поддерживает Multi-plane | [G](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| 28 | Native Multi-plane Roof Archicad создаётся единым элементом | [X](https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-66.htm) |
| 29 | Graphisoft Support фиксирует риск ridge junction после pitch edit | [J](https://support.graphisoft.com/hc/en-us/articles/24479784963089-My-roof-s-apex-connection-is-no-longer-clean-in-section) |
| 30 | Graphisoft Support описывает adjust/rejoin как исправление | [J](https://support.graphisoft.com/hc/en-us/articles/24479784963089-My-roof-s-apex-connection-is-no-longer-clean-in-section) |
| 31 | №1 08:02Z фиксирует roof plane-vs-favorite и Rhino SR caveat | [L](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261024T0802Z-TRIAD-ROOF-PLANE-RHINO-SR26-CACHE-GATES.md) |
| 32 | Аудитор №3 требует реального G0, IsAlive не доказывает PLN | [A](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md) |
| 33 | Аудитор №3 требует library/material GUID checks | [B](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-B.md) |

**Граница доказательств:** PDF целиком не загружался из-за большого размера; для GH Roof/Deconstruct использованы индексированные выдержки официального PDF, не локальная GUI-проверка. PR74 код на immutable commit 5a3a9201, а не установленная сборка. Нет новых OFFLINE, BUILD, INSTALLED, LIVE, ACCEPTED. MODEL_MODE_NOT_VERIFIABLE.
