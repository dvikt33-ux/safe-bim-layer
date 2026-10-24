# APA №2 — BUILD-01: SOURCE-проверки 01–15 · 2026-10-20 18Z

01. G0: [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) требует новое двухэтажное здание, G0–G5, один SceneWriter, независимый BREP. SOURCE, не LIVE.
02. G0: [NEXT](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md) назначает P0 BUILD-01, запрещает main/PLN/APX и новый writer.
03. G0: [матрица 61](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json) содержит count=61; рейтинги need/effort не заменяют проверку runtime.
04. G0: [PROJECT_PLAN rev182](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/control/PROJECT_PLAN.json) содержит 91 задачу и не содержит BUILD-01.
05. G0: [PROJECT_PLAN rev197](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/PROJECT_PLAN.json) содержит 104 задачи, BUILD-01/#192 отсутствует. До execution lease нужен отдельный управленческий допуск.
06. G0: [PR74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) open draft, merged=false; исторический LIVE 21 элемента не доказывает новый BUILD-01.
07. G2: [PR126](https://github.com/dvikt33-ux/safe-bim-layer/pull/126) open draft, merged=false; пакетное создание нельзя считать установленным.
08. G2: [PR149](https://github.com/dvikt33-ux/safe-bim-layer/pull/149) open draft, merged=false; 6 verifier contracts не равны универсальной сборке.
09. G3: [PR162](https://github.com/dvikt33-ux/safe-bim-layer/pull/162) open draft, merged=false; native group commands требуют отдельной регистрации.
10. G0: [PR150](https://github.com/dvikt33-ux/safe-bim-layer/pull/150) source CI и read-only baseline 298 GUID, но in-place deployment not run.
11. G4: [PR175](https://github.com/dvikt33-ux/safe-bim-layer/pull/175) snapshot source/offline pass, installed/live not verified.
12. G0: [PR74 SceneWriter](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py#L139-L165) guard требует exact projectPath/name, actStory/floorId/level, GetAddOnVersion=1.5.10; это не APX SHA.
13. G0: [PR74 bind](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py#L37-L79) имеет bind_authorized_saved_copy с SHA256 и authorizationRef; reuse, не новый writer.
14. G1: [PR74 run_project](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L428-L459) authored требует preflight/execute и callable transport; mode=offline отвергается.
15. G1/G2: [PR74 compiler](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L262-L321) проверяет targetProjectPath и nativeComponents whitelist; CreateBeams отсутствует.

Новых OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0. Источники только чтение.
