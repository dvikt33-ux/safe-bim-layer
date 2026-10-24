# APA №2 | 2026-10-24 07Z | Реестр 30 SOURCE-проверок

**Метод:** 30 отдельных проверяемых утверждений по реально прочитанным репозиторным файлам, issue и первичным документам. Не 30 запусков, не 30 независимых URL. Для PDF GC.pdf Beam проверен непосредственно в выдаче официального PDF; некоторые остальные детали GC.pdf сопоставлены с предыдущими №1/№2 SOURCE-отчётами и отмечены как SECONDARY_CROSSCHECK. Ни один локальный runtime не запускался.

Обозначения: [I] issue #192 https://github.com/dvikt33-ux/safe-bim-layer/issues/192 ; [N] docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md (research branch); [P] hourly/research-1-20261023T11Z-TRIAD-PIVOT.md; [M] priority_matrix_20261018.json; [C] PR74 pinned scripts/archicad_project_accelerator.py commit 5a3a9201; [S] pinned scripts/archicad_authored_native_plan.py; [G] https://help.graphisoft.com/AC/29/INT/GC.pdf ; [D] https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/ ; [Q] https://discourse.mcneel.com/t/model-object-component-update-problem/168818/5 ; [K] https://discourse.mcneel.com/t/content-cache-updated-guide/181883/1 ; [R1] hourly/research-1-20261024T0655Z-TRIAD-DUAL-SYNC-DOCUMENT-CACHE-GATES.md ; [R2] hourly/research-2-integration-2026-10-24T06Z-report.md.

| # | Проверка | Результат / доказательство |
|---:|---|---|
| 01 | Issue #192 — BUILD-01 требует новое здание | PASS [I], G0–G5 |
| 02 | Issue запрещает повтор старого CREATE | PASS [I] |
| 03 | NEXT фактически расположен в extension-ranking | PASS [N], fetch_file sha 6f074693360231c5cb42ada815984a6b0dd504c0 |
| 04 | TRIAD-PIVOT требует именно триаду, не каталог add-on | PASS [P], blob 896fa3af0953468ca58fca710f32cb926504f582 |
| 05 | Матрица объявляет count=61 | PASS [M], parsed |
| 06 | В матрице фактически 61 item | PASS [M], parsed |
| 07 | В матрице 61 уникальный ID | PASS [M], Set(ids) |
| 08 | GRASSHOPPER priority=40 и decision=ИССЛЕДОВАТЬ_ТОЧКУ_ПОДКЛЮЧЕНИЯ | PASS [M], parsed |
| 09 | TAPIR-EXISTING priority=93 и reuse | PASS [M], parsed |
| 10 | PR74 authored schemaVersion=apa-authored-project/1 | PASS [C] lines 263–277 |
| 11 | PR74 units обязаны быть meters | PASS [C] lines 274–277 |
| 12 | targetProjectPath должен совпасть с RUN.EXPECTED_PATH | PASS [C] line 278 |
| 13 | nativeComponents ограничен длиной 100 | PASS [C] lines 288–290 |
| 14 | nativeComponents allowlist = Columns/Doors/Windows/Walls/Roofs | PASS [C] lines 293–296 |
| 15 | CreateBeams отсутствует в authored allowlist | PASS [C] lines 293–296; не означает отсутствия в Tapir |
| 16 | Roof требует pivotLine, Basic и buildingMaterialId | PASS [C] lines 301–305 |
| 17 | Roof polygon margin=0.35m | PASS [C] lines 306–311 |
| 18 | Дополнительная Wall margin=0 | PASS [C] lines 306–311 |
| 19 | Column требует один item, storyIndex и XYZ | PASS [C] lines 312–321 |
| 20 | structuralFunctions в этом маршруте разрешены Wall/Slab/Roof, не Beam | PASS [C] lines 330–336 |
| 21 | authored intent mode=offline отвергается | PASS [C] lines 438–443 |
| 22 | guarded_project вызывается перед authored compilation | PASS [C] lines 444–449 |
| 23 | execute требует run_id и matching confirmPlanHash | PASS [C] lines 477–486 |
| 24 | authored plan создаёт один footprint slab/story | PASS [S] lines 72–106 |
| 25 | CreateSlabs.level задаётся абсолютной проектной Z | PASS [S] lines 105–111 |
| 26 | Официальный AC29 GH Beam создаёт нативные Beam из 3D curves | PASS [G] стр.26, PDF search result |
| 27 | 3D curves в GH Beam сегментируются | PASS [G] стр.26 |
| 28 | Beam Settings поддерживает Rectangular/Circular/Complex Profile | PASS [G] стр.26; также пример стр.73 |
| 29 | Rhino Query Synchronise=False даёт frozen copy до expire/Query | PASS [Q], разработчик McNeel 16.11.2023, Rhino8.1 |
| 30 | Content Cache Action=False не прекращает Pull при видимом Result | PASS [K], строки Action 120–125, Results 138–143, 17.05.2024 RC caveat |

**Дополнительные SOURCE-сверки без включения в число 30:** [D] AC29 add-on build3000/Windows/Rhino7–8/01.10.2025; [K] Push с ID заменяет, Bake без ID дублирует, Purge удаляет неиспользуемые definitions; [R1] GH connection port/definition; [R2] Graphisoft Synchronize=False→Null и Deconstruct Roof single-plane. Эти детали использованы в отчёте с указанной границей доказательств.

**Результат:** 30/30 SOURCE statements documented; 0 OFFLINE, 0 BUILD, INSTALLED NOT_VERIFIED, 0 LIVE, 0 ACCEPTED. SOURCE не равен runtime PASS. MODEL_MODE_NOT_VERIFIABLE.
