# APA №2 — BUILD-01 — SOURCE 01–14 · 2026-10-20T19Z

Все проверки — фактическое чтение первоисточников; никакого локального AC29/PLN/APX и модельных WRITE. Формат: барьер → точный источник → контракт/вердикт.

01. **G0 — Issue #192 требует новое двухэтажное здание, а не повтор исторического прототипа.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/issues/192). G0–G5, новый scratch, второй brief; никакого нового LIVE без разрешения.

02. **G0 — NEXT закрепляет P0 и раздельную ответственность №1/№2/№3.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md). Исследователь №2 приносит adapters; NEXT не редактировать.

03. **G0 — Матрица кандидатов имеет 61 позицию.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json). count=61; 0–100 в новой матрице — оценка полезности, не benchmark.

04. **G0 — Исторический PROJECT_PLAN rev182 не является текущим dispatch.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/control/PROJECT_PLAN.json). revision=182; canonical_branch отдельно указан, mutation запрещена.

05. **G0 — Аудитор №3 за 18Z требует реальный runtime receipt.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md). G0 BLOCKED, issue без комментариев/receipt; SOURCE ≠ INSTALLED.

06. **G0 — PR74 SceneWriter содержит жёсткий порт/путь/версию.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py#L19-L27). PORT=19723, EXPECTED_TAPIR=1.5.10 — константы, не runtime evidence.

07. **G0 — PR74 умеет привязывать только явно разрешённую копию.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py#L37-L90). bind_authorized_saved_copy требует absolute PLN, name=stem, saved_sha256, authorizationRef; неизвестная копия STOP.

08. **G0 — PR74 guard проверяет identity tuple.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py#L135-L167). GetProjectInfo, GetStories, GetAddOnVersion; имя без пути/этажей недостаточно.

09. **G0 — PR97 GetAPARuntimeInfoV1 существует в SOURCE.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/8f134001ca0e3250eda587db61ac01dbd6357326/archicad-addon/Sources/NativeGridCommands.cpp). Выдаёт buildIdentity/sourceRevision/sdkMajor=29/nativeModelWrites=0, но не SHA APX и не INSTALLED.

10. **G0 — PR97 builder выдаёт BUILD_NOT_INSTALLED receipt.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/8f134001ca0e3250eda587db61ac01dbd6357326/archicad-addon/Examples/build_model_dump.py). BUILD_PASS_BINARY_IDENTITY_VERIFIED_NOT_INSTALLED содержит APX SHA256; не равен installed APX.

11. **G0 — PR150 bridge привязан к BDD и hash списка модулей.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/8fbb311fc2f25fb8b2b6ff432e74d4e31b4c93fc/scripts/apa_ac29_autonomous_job_bridge.py). ROOT=C:\LocalAI\APA_AC29_Stable, WORKING=BDD; нельзя автоматически переадресовать на новый scratch.

12. **G1 — PR74 authored compiler валидирует exact brief и target.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L262-L290). apa-authored-project/1, units=meters, brief.targetProjectPath == EXPECTED_PATH.

13. **G1 — PR74 authored offline не допускает transport-free.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L428-L459). mode=preflight/execute и callable transport; offline для authored отвергается, read-only preflight не моделирует LIVE.

14. **G1 — PR74 проверяет этажи и native materials.** [Источник](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py#L24-L73). storyHeights 2.4–4.5 m; adjacent level tolerance 1e-5; nativeStoryBindings и material GUID должны совпасть.

**Итог:** 14 SOURCE; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0/0/0/0/0. MODEL_MODE_NOT_VERIFIABLE.
