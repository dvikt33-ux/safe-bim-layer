# APA №2 — BUILD-01 · 20.10.2026 23Z · SOURCE 01–15

Только чтение; G0–G5 не пройдены. Источники закреплены на SHA веток PR.

01. Issue #192: новая двухэтажная PLN, G0–G5, без второго writer. https://github.com/dvikt33-ux/safe-bim-layer/issues/192
02. NEXT: BUILD-01 P0, №2 — интеграция. https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md
03. Матрица: 61 кандидат, priority_formula 12*need+7*(5-effort)+confidence. https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json
04. Исторический PROJECT_PLAN rev182, текущий канон rev197; оба только чтение.
05. PR74 authored: strict schemaVersion, units=meters, exact brief.targetProjectPath.
06. PR74 authored run_project: только preflight/execute + callable transport; offline отвергается.
07. PR74 bind_authorized_saved_copy: exact PLN path/stem/SHA256/authorizationRef.
08. PR74 guarded_project: project identity, actStory, floorId, level, version.
09. PR74 model-first пример: 10 Walls, 2 Slabs, 6 Windows, 2 Doors, 1 Roof — исторический fixture, не новый BUILD-01.
10. PR74 SceneWriter: Slab Create→typed readback→Modify→readback, SQLite BASIC_MODIFY_ATTEMPTED.
11. PR74 authored native plan: 2.4–4.5 m, explicit story bindings, 1e-5 level tolerance.
12. PR131 host batch: ownerWallId GUID, story, straight host, overlap, library qualification.
13. PR149 ModifySlabs verifier: material-only, exactly 3 fields, story0.
14. PR149 CreateBeams verifier: Basic horizontal story0; не универсален.
15. PR126 bulk: 1–200 typed items, 6 команд, Roof не включён.

Первичные SHA: PR74 5a3a9201a715a5528c93bed4a5318e2acb32eea7; PR131 75ae71dc60176225bb71928fb805e5adcc688b2e; PR149 4c119428e9b1c24bd00774c91a6f33cbf26f0369; PR126 f12aeba017ecd34a13989998f0b7700f6a0107d2.
