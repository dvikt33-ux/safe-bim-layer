# APA №2 — SOURCE 01–15, 2026-10-22 23Z

Проверены прямыми GitHub чтениями в данном цикле. Только SOURCE, без локального запуска.

01. **BUILD-01 #192** — G0–G5 требуют нового native результата; G3 только по отдельному допуску. Источник: https://github.com/dvikt33-ux/safe-bim-layer/issues/192

02. **NEXT priorities** — P0=BUILD-01; NEXT ведёт №3, здесь только READ. Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md

03. **Матрица 61** — 61 уникальный ID; формула приоритета 61/61; blob 9cb5e6f2. Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json

04. **Кандидаты 61** — 61/61 совпадающих ID с матрицей; blob 87ee1c0b. Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/candidates.json

05. **Аудит №3 20.10 07Z** — SOURCE не равен LIVE; G0 остаётся BLOCKED. Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-07.md

06. **№1 22.10 21Z** — 4 приложения WRITE_BLOCKED; опубликован только индекс. Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261022T21Z-BUILD01-INDEX.md

07. **PR34** — Исходный BIM Graph/story binding; 25 synthetic operations, не BUILD-01. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/34

08. **PR48** — Исторический native 8 Walls/2 Slabs/2 Columns/1 Door/4 Windows, не новое здание. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/48

09. **PR74** — 21-element native 2-storey prototype; отдельный SceneWriter уже поддерживает CreateSlabs→ModifySlabs. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/74

10. **PR82** — SinglePlane/MultiPlane Roof variants; нельзя считать универсальным Roof. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/82

11. **PR97** — CW/Railing/Shell отдельный scope; BUILD-01 базовой коробки не блокирует. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/97

12. **PR126** — execute_batch 1–200 через прежний writer; не смешивать с single-GUID PR74 без проверки. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/126

13. **PR131** — V2 qualified Favorite/host-fit; отдельная ветка, не автоматическая installed гарантия. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/131

14. **PR149** — Отдельный scoped verifier ModifySlabs floor0 Basic; не ограничение самого Tapir schema. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/149

15. **PR150** — Healthcheck/release six verifiers, Windows in-place deployment NOT RUN. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/150
