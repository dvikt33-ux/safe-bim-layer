# APA №2 · 2026-10-21 00Z · SOURCE 1–15

Новый BUILD-01, Archicad29 build5101 / Windows11 / Tapir1.5.10. Эти SOURCE-проверки выполнены чтением указанных GitHub исходников/схем, не через установленный APX. Никаких model writes, установки или изменения исходников.

**01. [G0]** Issue #192 requires new 2-storey scratch, 6 gates, independent readback; historical 21-element fixture is not BUILD-01.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/issues/192
Вывод/критерий: SOURCE; no native execution.

**02. [G0]** NEXT ranks BUILD-01 P0; researcher #2 is integration, not builder or auditor.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md
Вывод/критерий: Do not edit NEXT.

**03. [G0]** 61-item ranking JSON has count=61; existing Graphisoft API and Tapir ranked for reuse, not new engines.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json
Вывод/критерий: Reuse; no installs.

**04. [G0]** PROJECT_PLAN rev182 has 91 keyed tasks; rev197 has 104; neither registers BUILD-01; Issue is not execution lease.
Источник: https://api.github.com/repos/dvikt33-ux/safe-bim-layer/git/blobs/c2ab2f9d606db1412c4031076103c267fc463f83
Вывод/критерий: Only coordination may update canonical plan.

**05. [G0]** PR74/97/126/131/149/150/159/162/175 are draft open and unmerged as fetched 21 Oct 2026; source ≠ installed.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/74
Вывод/критерий: INSTALLED_NOT_VERIFIED.

**06. [G0]** PR74 guarded_project(api) without required_story hardcodes active story index=0, floorId=1, level=0.0.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py#L139-L164
Вывод/критерий: NEW BLOCKER: new scratch G1 preflight may reject legitimate other binding; minimal adapter must thread verified required_story.

**07. [G0]** bind_authorized_saved_copy validates absolute PLN, stem/name, authorizationRef, SHA256 of file; not a blanket permission.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py#L49-L79
Вывод/критерий: Reuse binding after explicit authorization; no PLN writes.

**08. [G0]** GetProjectInfo v0.1.0 offers isUntitled/isTeamwork/path/name; missing exact path fails existing guard.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/schemas/tapir-live-1.5.10/tapir-scene-live.json#L1-L110
Вывод/критерий: Fail closed on absent projectPath.

**09. [G0]** GetStories v1.1.5 yields firstStory,lastStory,actStory,skipNullFloor,stories; story floorId must come from runtime.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/schemas/tapir-live-1.5.10/tapir-scene-live.json#L423-L461
Вывод/критерий: Pin index/floorId/name/level, not guessed 0/1.

**10. [G0]** GetAddOnVersion v0.1.0 returns version string, not installed APX SHA.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/schemas/tapir-live-1.5.10/tapir-scene-live.json#L1-L45
Вывод/критерий: Separate read-only Windows APX Get-FileHash needed.

**11. [G0]** PR97 GetAPARuntimeInfoV1 exposes buildIdentity/sourceRevision/sdkMajor=29/nativeModelWrites=0, not binary SHA.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/8f134001ca0e3250eda587db61ac01dbd6357326/archicad-addon/Sources/NativeGridCommands.cpp#L1-L22
Вывод/критерий: Use only if registered in runtime; then match APX hash.

**12. [G0]** PR74 export_schema calls GenerateDocumentation, checks project and inventory before/after; creates evidence files on disk.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L585-L612
Вывод/критерий: Do not execute for schema inspection in this research cycle.

**13. [G1]** PR74 authored run_project accepts preflight/execute plus callable transport, not mode=offline.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L428-L459
Вывод/критерий: NOT_FOUND autonomous authored-offline entrypoint; existing preflight adapter only.

**14. [G1]** PR74 requires schemaVersion=apa-authored-project/1, units=meters, brief.targetProjectPath=RUN.EXPECTED_PATH.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L262-L282
Вывод/критерий: Reuse compiler; exact scratch target.

**15. [G1]** Native plan checks storyHeights 2.4–4.5m and level+height match; nativeStoryBindings equality required.
Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py#L24-L75
Вывод/критерий: STOP on changed story mapping.

**Уровень доказательности: SOURCE_ONLY; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0.**
