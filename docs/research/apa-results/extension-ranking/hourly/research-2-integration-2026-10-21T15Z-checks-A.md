# APA №2 — 2026-10-21T15Z — SOURCE 01–15
Объект: BUILD-01 (#192). Это проверки исходников/документов, не OFFLINE, BUILD, INSTALLED или LIVE.

| № | Источник (immutable SHA/commit) | Что действительно проверено |
|---:|---|---|
| 01 | issue #192, 2026-10-20T08:03:29Z | Шесть ворот G0–G5, запрет повторного CREATE и второго writer. |
| 02 | NEXT_RESEARCH_PRIORITIES.md, blob 6f074693360231c5cb42ada815984a6b0dd504c0 | P0 BUILD-01, SOURCE ≠ инженерная приёмка, правила публикации. |
| 03 | priority_matrix_20261018.json, blob 9cb5e6f2a59f80762cc77073eeb10404829af75a | Исходный рейтинг 61 — экспертный, не benchmark. |
| 04 | №1 research-1-20261020T13Z.md, blob fd89840ec5f5c4c357e4b01da7e5da7ff22c79f7 | G1 identity/preflight, необходимость проверки новой PLN. |
| 05 | №3 audit-2026-10-18-17-audit-A.md, blob 09e8c5244b2b1586be372dc549c1b83eca13ece5 | Контроль различия SOURCE/INSTALLED и неполного readback. |
| 06 | PROJECT_PLAN.json rev182, commit 049576378c961c5d7a9a62611f4091e3da70d309, blob c2ab2f9d606db1412c4031076103c267fc463f83 | Историческая ревизия 182, только чтение. |
| 07 | TAPIR_VERSION_COMPATIBILITY_AUDIT_20261018.md, blob 014e25f4ff7c555bb90c26a8d745b6894489f0bf | Происхождение локального Tapir 1.5.10 не подтверждено релизом. |
| 08 | CATALOG_20261018.md, blob 3712feda0700261a9c4b19e920abc057a8316dd1 | Готовые функции не равны установленным. |
| 09 | PR74 scripts/archicad_project_accelerator.py, blob 8e0ce2fbb5441009925f0d9199e180e8670a5eea | authored compile, exact target path, inventory_guids. |
| 10 | PR74 scripts/archicad_authored_native_plan.py, blob f57812f29c826bc48ce3c6ffd0f9b6a7dc628a7d | Slab level абсолютный Z, floorIndex; CreateSlabs без buildingMaterialId. |
| 11 | PR74 scripts/archicad_scene_run.py, blob ca91c1cfc41cee763c62d1f3a70337d74fbafd53 | SQLite intent-before-write, отдельные GUID/readback. |
| 12 | PR74 scripts/archicad_authored_geometry.py, blob 737d35a3ae3d61b601403f9b0af51b08974b26c7 | Проверка результирующей геометрии не доказывает полное покрытие крышей. |
| 13 | PR74 schemas/tapir-live-1.5.10/tapir-scene-live.json, blob e8ad53b6ea7c19dc34cbdcb723a79be995639cd7 | Зафиксированная provider schema ≠ фактический APX; CreateSlabs без structureType/buildingMaterialId. |
| 14 | PR126 scripts/archicad_dynamic_commands.py, blob a11d91b4205a8a31d56f531982cb89fbe7cc713f | execute_batch: только 6 CREATE семейств, 1–200 items, pre/post verify, GUID-count. |
| 15 | PR131 scripts/archicad_dynamic_commands.py, blob 67c2bce6c2ee67626d9eeb31b051ea0b56521a77 | Дальнейшая интеграция DynamicCommands, не доказательство runtime. |

Метод: чтение GitHub fetch_issue/fetch_blob/fetch_file по зафиксированным ref; blob SHA — Git SHA1 содержимого, не SHA256 установленного бинарника. Исследование не выполняло WRITE в Archicad.
