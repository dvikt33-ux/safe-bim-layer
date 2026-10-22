# APA №2 — BUILD-01, 19Z, SOURCE 15–30

14 успешных GitHub `fetch_file` с immutable PR head (номера указаны ниже), плюс 2 чтения первоисточников. SHA — Git blob SHA-1, не SHA256 локального APX. SOURCE_ONLY.

15. PR162 schemas/tapir-live-1.5.10/tapir-scene-live.json — `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`: provider snapshot; not loaded APX.
16. PR162 archicad-addon/Sources/ModelDumpCommands.cpp — `c47f12b894dec28d2251b9a18d06678e73603808`: GetModelDumpV1 source, registration pending.
17. PR162 examples/accelerator/model-first-building.json — `e192fbb31bc872d751c41aa7132f0a4981755051`: historical fixture, not new BUILD-01.
18. PR162 scripts/archicad_batch_contracts.py — `4afbe545360f919209f086f2d3cd13e573d13393`: batch type names not writer authorization.
19. PR74 scripts/archicad_project_accelerator.py — `8e0ce2fbb5441009925f0d9199e180e8670a5eea`: compiler; no Beam in basic whitelist.
20. PR74 scripts/archicad_scene_run.py — `ca91c1cfc41cee763c62d1f3a70337d74fbafd53`: one GUID per step; GetAllElements({}).
21. PR74 docs/APA_MODEL_FIRST_BUILDING.md — `55c5e64186e7013ecec83349de005e28f60fcff5`: 21-element demo historical only.
22. PR126 scripts/archicad_dynamic_commands.py — `a11d91b4205a8a31d56f531982cb89fbe7cc713f`: execute_batch 1–200, one SceneWriter call.
23. PR131 scripts/archicad_strategy_discovery.py — `f6725d94fb6d90d56d98d6edb2a6ed1c375bcfee`: Slab Favorite; openings verified host.
24. PR149 scripts/apa_ac29_existing_create_verifiers.py — `fff474a2213cb8adfc9306c1e344e8afe60949ea`: scoped material/BREP verifier.
25. PR149 scripts/apa_ac29_dynamic_native_verifiers.py — `8516ebef2c6804bc83dc79724bfb234591e14aa9`: bounded registry, not generic writer.
26. PR150 scripts/release_apa_ac29_six_verifiers.py — `d1647e3e4d0e4f8b907084117ef68b02807311f7`: release guard expects 298 GUID, local upgrade unproved.
27. PR159 scripts/apa_ac29_group_acceptance_mailbox.py — `efd9f0f20fd63e54a4efa3963c63429090a485a0`: isolated scratch test; not SceneWriter production.
28. PR160 docs/research/apa-results/ap2-local-native-massops-gate-20261018.md — `114b90a465395819d8ef0994d3ae8ec06a6eac0e`: PDF anchors not hosted opening placement.
29. Upstream Tapir LICENSE (main): MIT, copyright Enzyme APD, прочитано напрямую; https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/LICENSE . Лицензия APA отдельно NOT_VERIFIED.
30. weltmaister/archicad-agent-skills README (main): готовые методические skill-файлы по Tapir; https://github.com/weltmaister/archicad-agent-skills . Это справочник и не заменяет существующий APA compiler/writer; совместимость с installed 1.5.10 не проверена.

Сводный источник: PR162 `f7c37b84b76c040c417ccd58a5543326e50f673a`; PR74 `5a3a9201a715a5528c93bed4a5318e2acb32eea7`; PR126 `f12aeba017ecd34a13989998f0b7700f6a0107d2`; PR131 `75ae71dc60176225bb71928fb805e5adcc688b2e`; PR149 `4c119428e9b1c24bd00774c91a6f33cbf26f0369`; PR150 `8fbb311fc2f25fb8b2b6ff432e74d4e31b4c93fc`; PR159 `f13b1dcd70e9cb63f795e09fd25ada299e56f017`; PR160 `e8cbbf97335d454b7d253061319bcf354a4eaf99`.
