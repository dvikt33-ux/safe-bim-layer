# APA №2 | 2026-10-24 04Z | 30 предметных SOURCE-проверок

**Метод:** фактическое чтение GitHub-коннектором на указанной исследовательской ветке/immutable PR74 и официальных страниц Graphisoft. Пункт = отдельное утверждение, **не** независимый документ и **не** runtime тест. Никаких OFFLINE/INSTALLED/LIVE/ACCEPTED.

| № | Проверенное утверждение | Первоисточник / конкретная граница | Результат |
|---:|---|---|---|
| 01 | Целевая исследовательская ветка существует | GitHub search_branches: `research/apa-extension-ranking-hub-20261018` | SOURCE_PASS |
| 02 | NEXT лежит в `docs/research/apa-results/extension-ranking/`, не в корне | fetch_file blob `6f074693360231c5cb42ada815984a6b0dd504c0` | SOURCE_PASS |
| 03 | Pivot №1 требует совместного AC29/Rhino8/GH и запрещает новый writer | `research-1-20261023T11Z-TRIAD-PIVOT.md`, blob `896fa3af...` | SOURCE_PASS |
| 04 | №1 03Z разделяет Duplicate Content/Content Cache и native GUID | `research-1-20261024T03Z-TRIAD-DUPLICATE-CONTENT-CACHE-IDENTITY.md`, blob `eb5bb3f...` | SOURCE_PASS |
| 05 | №3 известный 20.10 18Z не доказывает G0 receipt | `audit-2026-10-20-18-A.md`, blob `5aa388a4...` | SOURCE_PASS; STALE |
| 06 | Матрица 61: count=61, length=61, unique IDs=61 | `priority_matrix_20261018.json`, blob `9cb5e6f2...` | SOURCE_PASS |
| 07 | BUILD-01 требует новое 2-этажное здание, G0→G5 и отдельное G3 разрешение | https://github.com/dvikt33-ux/safe-bim-layer/issues/192 | SOURCE_PASS |
| 08 | Authored contract = `apa-authored-project/1`, units meters, exact target PLN | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L262-L277 | SOURCE_PASS |
| 09 | `nativeComponents` allowlist ровно Columns/Doors/Windows/Walls/Roofs | тот же файл #L288-L296 | SOURCE_PASS |
| 10 | `nativeComponents` ограничен 100 дополнительными шагами | тот же файл #L288-L290 | SOURCE_PASS |
| 11 | Roof в authored: Basic + pivotLine + material + 1 row + outline margin 0.35m | тот же файл #L297-L311 | SOURCE_PASS |
| 12 | Roof реально подключается как opt-in typed adapter `adapters(['roof'])` | тот же файл #L454-L463 | SOURCE_PASS |
| 13 | Typed roof readback проверяет SinglePlane, level, angle, thickness, material, pivot | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L183-L198 | SOURCE_PASS |
| 14 | Native roof junctions в existing extension требуют ровно один Roof | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_extension.py#L243-L257 | SOURCE_PASS |
| 15 | Roof holes блокируются, связи — `SubtractionUpwards` через SEO | тот же файл #L265-L327 | SOURCE_PASS |
| 16 | Slab `CreateSlabs.level` задан абсолютной отметкой этажа | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py#L105-L112 | SOURCE_PASS |
| 17 | Authored story heights 2.4..4.5 и continuity | тот же файл #L34-L43 | SOURCE_PASS |
| 18 | Room/outline только rectangles, room overlap запрещен | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_semantic_spatial.py#L26-L30 и #L75-L100 | SOURCE_PASS |
| 19 | Authored `offline` не допускается, нужен read-only preflight transport | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L428-L443 | SOURCE_PASS |
| 20 | Официальный AC29 GH Live Connection build3000, Rhino7/8, Windows, 01.10.2025 | https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/ | SOURCE_PASS |
| 21 | Официальный GH–AC29 Roof Component создаёт Single-plane Roof | https://help.graphisoft.com/AC/29/INT/GC.pdf, раздел Roof Component | SOURCE_PASS |
| 22 | AC28 официально расширил Beam/Column и Rhino8 support; AC29 installed не доказан | https://help.graphisoft.com/AC/28/INT/_AC28_Help/005_NewFeatures/005_NewFeatures-9.htm | SOURCE_PASS / VERSION_BOUND |
| 23 | AC29 умеет File→External Content→Place Hotlink→Rhino .3dm | https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-43.htm | SOURCE_PASS |
| 24 | При импорте Rhino AC29 создаёт **non-editable GDL Objects**, не native Wall | https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm, строки 2–7 | SOURCE_PASS |
| 25 | Каждый Rhino element становится отдельным .gsm в Embedded Library | https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm, строки 125–127 | SOURCE_PASS |
| 26 | Rhino original ID и Layer доступны как свойства в AC29 | https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm, строки 155–164 | SOURCE_PASS |
| 27 | Hidden Rhino elements по умолчанию не импортируются; Surfaces/Layers создаются | https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm, строки 67–114 | SOURCE_PASS |
| 28 | Rhino Hotlink фиксирует сегментацию, размещается на активном этаже | https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-43.htm, строки 19–25 | SOURCE_PASS |
| 29 | Hotlink может удалять embedded library parts; Relink очищает Undo | https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-56.htm + https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-60.htm | SOURCE_PASS |
| 30 | AC29 Crop to Single-plane Roof неассоциативен и может расщепить Wall; Trim/SEO ассоциативны | https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-88.htm + https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-269.htm | SOURCE_PASS |

**Итог:** 30 документарных утверждений с конкретными источниками; часть проверок относится к одним и тем же файлам. Никаких локальных команд, Rhino/AC установок, LIVE-операций или новой модели не выполнялось. MODEL_MODE_NOT_VERIFIABLE.
