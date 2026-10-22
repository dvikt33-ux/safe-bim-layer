# APA №2 — SOURCE 16–30, 2026-10-22 23Z

Прямые чтения PR, точных файлов и pinned схемы. Не подменять SOURCE статусом INSTALLED.

16. **PR151** — In-place six-verifier updater; local deployment unconfirmed, cannot claim INSTALLED. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/151

17. **PR154** — PDFVectors source parsing, secondary to BUILD-01. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/154

18. **PR159** — Group acceptance harness source; bounded scratch only, not full building. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/159

19. **PR160** — PDF→native massops preflight, hosted openings require real Wall GUID. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/160

20. **PR162** — Group-first uses existing DynamicCommands/BIM Graph/SceneWriter; new route SOURCE pending acceptance. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/162

21. **PR190** — Read-only group intent registration qualified in narrow scope; not complete inventory. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/190

22. **PR191** — Standalone Basic Slab copy only floor0, no holes/dependents; not general two-floor slab create. Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/191

23. **PR74 SceneWriter** — lines 852–919: CreateSlabs GUID → intermediate read → SQLite BASIC_MODIFY_ATTEMPTED → ModifySlabs → typed readback; no floor0 guard here. blob source confirmed. Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-model-first-building-20261013/scripts/archicad_scene_run.py

24. **PR74 authored native plan** — lines 63–70 material GUID resolved from project; lines 105–112 CreateSlabs without material fields, level absolute, floorIndex native. Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-model-first-building-20261013/scripts/archicad_authored_native_plan.py

25. **PR74 accelerator** — lines 458–563 SceneWriter/SQLite/whole-assembly typed material/story readback; 2-storey intent, no new BUILD-01 run. Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-model-first-building-20261013/scripts/archicad_project_accelerator.py

26. **PR126 DynamicCommands** — execute_batch packs 1–200; probe_runtime calls API.IsAddOnCommandAvailable per selected command. Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-native-bulk-writer-20261016/scripts/archicad_dynamic_commands.py

27. **PR162 DynamicCommands** — same branch has execute_batch and group routing; #162 also contains PR74 authored plan and slab MODIFY SceneWriter. Single candidate branch, not installed proof. Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-automatic-group-routing-20261018/scripts/archicad_dynamic_commands.py

28. **Pinned Tapir 1.5.10 schema** — 262 commands; CreateSlabs has favoriteName but no structureType/buildingMaterialId; ModifySlabs has both; GetAllElements accepts databases; GetModelDumpV1 absent. Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-automatic-group-routing-20261018/schemas/tapir-live-1.5.10/tapir-scene-live.json

29. **Historical PROJECT_PLAN rev182** — immutable commit 0495763, blob c2ab2f9d, revision182, 91 tasks. Only READ. Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/049576378c961c5d7a9a62611f4091e3da70d309/docs/research/apa-results/control/PROJECT_PLAN.json

30. **Tapir upstream license** — MIT; repository source license does not establish identity/licensing of local APX or Graphisoft SDK. Источник: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/LICENSE
