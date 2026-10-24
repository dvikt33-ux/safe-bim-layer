# APA №2 — BUILD-01, 19Z, SOURCE 01–14

Все 14 файлов реально прочитаны из PR162 head `f7c37b84b76c040c417ccd58a5543326e50f673a`; SHA — Git blob SHA-1. Имена ниже расположены в `scripts/`. Только SOURCE, без локальных тестов.

01. `archicad_project_accelerator.py` — `439f6d26ce097cdfdfc33a2b5a245352073151f2`: Prepare + GetModelDumpV1 read allowlist.
02. `archicad_authored_native_plan.py` — `a9d8cb844a862ea92aed955fae999ddcc418eb86`: story bindings + CreateSlabs.
03. `archicad_authored_extension.py` — `edeaf3a875aad63da405ff844a3d5dfb2f2b4e49`: ModifySlabs/host extension.
04. `archicad_scene_run.py` — `484c600a205192d5737e124f8d47c8583e07a9f3`: single GUID and limited allowed writes.
05. `archicad_dynamic_commands.py` — `c05017ee3d082feebea96d804dbd6a3bd26680e7`: existing writer delegation.
06. `archicad_bim_graph.py` — `87fc7476c9079a189c8b8e31ae3c6beaf6712dd3`: Beam graph ≠ writer permission.
07. `archicad_runtime_version_probe.py` — `c76e394b8ea1c9128ad3e34e93f3ebf09d3b543a`: version check ≠ G0 PASS.
08. `archicad_connected_components.py` — `c5a99f59a90369ff622807574677cf11ca0a2225`: typed Beam adapter.
09. `archicad_native_material_selection.py` — `f66a1b34fe28191cc3ada97e2dc8e2a317eebc40`: library/material lookup.
10. `archicad_selected_library_part.py` — `ac05fbe1f6c85aef44618e0f5a278a5d15bfceb1`: Object ≠ Door/Window inventory.
11. `archicad_native_spatial_structure.py` — `78ec60e89f018ef400bb80ab187fdb1cbe926244`: GetStories; SetStories WRITE.
12. `apa_ac29_group_strategy.py` — `153bc1e353f3a0dd363a7bbcc23cb6d692b5ff3e`: reuse group commands.
13. `apa_ac29_live_group_autoselect_readonly.py` — `48ed87cb6830158f12bb2e4d61e9dadebbb04dc9`: read-only selector.
14. `archicad_native_roof_editing.py` — `91daaf8af881df5ba0cbddc09721bc92a54879c9`: bounded Roof editing.

Примечание: наличие исходного файла не доказывает его установку в Archicad 29. G0 BLOCKED.
