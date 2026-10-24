# APA №2 | 2026-10-24 05Z | Публикационная квитанция и навигация

**P0 BUILD-01 #192:** https://github.com/dvikt33-ux/safe-bim-layer/issues/192

**Новая дельта:** приёмка нативной BIM-модели не может опираться на один IFC: AC29 BREP сохраняет junctions, но теряет редактируемые параметры в экспортном представлении; parametric сохраняет параметры, но может терять специальные junctions. Roof и Shell при default mapping оба `IfcSlab.ROOF`. Композиты могут стать container+parts. Предложен **native readback + IFC-BREP + IFC-parametric/native parameter** G4 gate, без второго writer. Всё SOURCE_ONLY, G4 NOT_RUN.

**Файлы и verified readback:**

| Файл | Git blob SHA-1 (GitHub fetch_file) | Commit SHA (create_file) | Exact content compare |
|---|---|---|---|
| [Полный отчёт](research-2-integration-2026-10-24T05Z-report.md) | `a5f29a732b5f19839dfaeffc63c85f41301d616a` | `d3433de7dc34a41cac347f01a7e668975086d668` | TRUE |
| [26 SOURCE-сверок](research-2-integration-2026-10-24T05Z-checks.md) | `c9f1aeb5ef26ee19f8dc7af2e1476420bf85cfe5` | `2cd7d9351949bc75f9ca0f10358bf1da7320c44a` | TRUE |
| [2 контрааудита](research-2-integration-2026-10-24T05Z-audits.md) | `e743da27cace32df28fbcf4f66d1e9bbe41b845b` | `ddeae85e8efbd5580735faecbcb3b2ad18f441ac` | TRUE |

**Проверка:** `create_file` для каждого файла с явным `branch=research/apa-extension-ranking-hub-20261018`; затем `fetch_file(ref=branch)`, строковое точное сравнение полного UTF-8 содержимого, GitHub blob SHA-1 и commit SHA записаны. Git blob SHA указан как возвращённый GitHub, а не как независимо вычисленный. Содержимое файлов не изменялось после публикации. SHA256 не вычислялся.

**Статус:** SOURCE=26 предметных утверждений, OFFLINE=0 новых, BUILD=0, INSTALLED=NOT_VERIFIED, LIVE=0 новых, ACCEPTED=0. G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_PARTIAL; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. Full 3-way GUID-preserving sync NOT_FOUND.

**Запреты соблюдены:** main, исходный код, PLN/APX, установки, LIVE, merge, Work/Codex/Arena, платные API, исторический PROJECT_PLAN rev182 не менялись. MODEL_MODE_NOT_VERIFIABLE.
