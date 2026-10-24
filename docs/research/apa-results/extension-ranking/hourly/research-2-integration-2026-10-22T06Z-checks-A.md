# APA №2 — 2026-10-22T06Z — SOURCE-проверки 01–15
Только фактически полученные в текущем цикле GitHub-файлы; blob SHA-1 приведён из fetch_file. Локальный APX не опрашивался. Отдельный issue #192 прочитан ранее в этом цикле. Все ссылки указывают на repo dvikt33-ux/safe-bim-layer; исследовательская ветка research/apa-extension-ranking-hub-20261018, исходный PR162 head f7c37b84b76c040c417ccd58a5543326e50f673a.

01. **Issue #192** — https://github.com/dvikt33-ux/safe-bim-layer/issues/192 — G0–G5, новый двухэтажный PLN, запрет повторения 21-element demo. SOURCE.
02. **NEXT_RESEARCH_PRIORITIES.md** — blob 6f074693360231c5cb42ada815984a6b0dd504c0 — исполнитель BUILD-01, исследователь №2 только интеграция, №3 владелец NEXT.
03. **candidates.json** — blob 87ee1c0b66233bf713e273b8b7cd00eff3a422f9 — исходная матрица кандидатов; не benchmark.
04. **priority_matrix_20261018.json** — blob 9cb5e6f2a59f80762cc77073eeb10404829af75a — приоритеты исторического обзора, не доказательство INSTALLED.
05. **research-1-20261022T04Z-BUILD01-A.md** — blob c6f4da211600377701f9804a1c3d8579c7d0e7d8 — G0: GetProjectInfo не имеет dirty/readOnly; GetStories не гарантирует height последнего этажа.
06. **research-1-20261022T0459Z-BUILD01-A.md** — blob 0ecf0ff2b52b8d00e663a0c488715694114d73ff — build проверять через официальный GetProductInfo.
07. **research-2-consolidated-2026-10-22.md** — blob 343309b09996892a3a9957208f0e51bcac31e6ab — девять ранее выявленных маршрутов, без LIVE.
08. **audit-2026-10-20-18-A.md** — blob 5aa388a4c2a8e0b14ddb92c5063181ee87488c6f — аудит №3 отмечает несинхронность канонического диспетчера BUILD-01; историческая ревизия не текущий runtime.
09. **PR162 scripts/archicad_project_accelerator.py** — blob 439f6d26ce097cdfdfc33a2b5a245352073151f2 — nativeComponents/roof adapter, read allowlist; отдельный beam adapter не включён.
10. **PR162 scripts/archicad_scene_run.py** — blob 484c600a205192d5737e124f8d47c8583e07a9f3 — preflight не проверяет allowed_writes; execute может отказать UNSUPPORTED_WRITE_RECIPE; GetAllElements({}) scope.
11. **PR162 scripts/archicad_dynamic_commands.py** — blob c05017ee3d082feebea96d804dbd6a3bd26680e7 — пакетные команды/группы уже в одном дереве.
12. **PR162 scripts/archicad_bim_graph.py** — blob 87fc7476c9079a189c8b8e31ae3c6beaf6712dd3 — CreateBeams распознаётся BIM Graph.
13. **PR162 scripts/archicad_authored_native_plan.py** — blob a9d8cb844a862ea92aed955fae999ddcc418eb86 — nativeStoryBindings и сверка с GetStories.
14. **PR162 scripts/archicad_connected_components.py** — blob c5a99f59a90369ff622807574677cf11ca0a2225 — готовый адаптер beams; требуется минимальная интеграция, не второй writer.
15. **PR162 scripts/archicad_runtime_version_probe.py** — blob c76e394b8ea1c9128ad3e34e93f3ebf09d3b543a — НОВОЕ: возвращает READ_ONLY_VERSION_CHECK даже при buildMatchesUserScreenshot=false/null, не сверяет Tapir с 1.5.10 и не проверяет APX SHA/command registration. Не трактовать status как G0 PASS.

Примечание: SHA файлов — Git blob SHA-1, не SHA256 локального APX.