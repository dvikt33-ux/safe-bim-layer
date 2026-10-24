# APA №2 — 23.10.2026 12Z — 31 SOURCE assertions

**BUILD-01 contribution:** official GH native Design is a writer independent from APA SceneWriter/SQLite. Strict single-writer and arbitrary symmetric three-way native writes cannot both be claimed. No universal GH-to-PR74 typed handoff identified.

31 distinct source assertions below; not 31 different documents, runs, or tested functions. AC29 guide was examined through official indexed excerpts; full 22.8MB PDF page audit NOT_DONE. Code pinned at f7c37b84b76c040c417ccd58a5543326e50f673a.

- S01 — G0–G5 requires new scratch, new task, native Save/Open; historical prototype insufficient. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/issues/192
- S02 — AC29 Live Connection build3000 supports Rhino7/8 and Windows, dated 2025-10-01. SOURCE: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
- S03 — AC30 also has build3000: build number alone cannot select add-on. SOURCE: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
- S04 — Graphisoft excludes Archicad Start Edition. SOURCE: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
- S05 — GH Design/Document components write AC native elements when Synchronize TRUE. SOURCE: https://help.graphisoft.com/AC/29/INT/GC.pdf
- S06 — Synchronize FALSE yields Null; this is not proof of undo or deletion. SOURCE: https://help.graphisoft.com/AC/29/INT/GC.pdf
- S07 — Deconstruct extracts AC reference geometry and Settings. SOURCE: https://help.graphisoft.com/AC/29/INT/GC.pdf
- S08 — Deconstruct supports manually placed AC elements via Set one/multiple Element. SOURCE: https://help.graphisoft.com/AC/29/INT/GC.pdf
- S09 — AC changes require documented Send Changes action to refresh GH reference. SOURCE: https://help.graphisoft.com/AC/29/INT/GC.pdf
- S10 — Deconstruct Roof supports SinglePlane, not MultiPlane Roof. SOURCE: https://help.graphisoft.com/AC/29/INT/GC.pdf
- S11 — Roof Parameter also excludes MultiPlane Roof. SOURCE: https://help.graphisoft.com/AC/29/INT/GC.pdf
- S12 — Wall Parameter connects to Door/Window Design host. SOURCE: https://help.graphisoft.com/AC/29/INT/GC.pdf
- S13 — Extract Settings is AC to GH read, not an in-place reverse write guarantee. SOURCE: https://help.graphisoft.com/AC/29/INT/GC.pdf
- S14 — Rhino8 Grasshopper is built-in visual algorithm editor. SOURCE: https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm
- S15 — Rhino8 -Grasshopper Solver Disable/Enable controls GH solver, not AC commit. SOURCE: https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm
- S16 — Rhino8 GrasshopperPlayer executes .gh/.ghx definitions without opening GH UI. SOURCE: https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm
- S17 — Rhino8 evaluation is 90 days; saving/plugins stop afterward without license. SOURCE: https://www.rhino3d.com/download/
- S18 — Rhino.Inside official framework does not document ready AC29 connector. SOURCE: https://www.rhino3d.com/features/rhino-inside/
- S19 — PR162 SceneWriter ALLOWED_WRITES include Walls/Slabs/Columns/Windows/Doors/Objects. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py
- S20 — PR162 Beams/Roofs require opt-in typed adapter. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py
- S21 — PR162 run_project connects roof adapter but not beam adapter. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py
- S22 — PR162 roof adapter requires SinglePlane Basic and exact material GUID. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_connected_components.py
- S23 — Pinned Tapir CreateRoofs defaults MultiPlane unless pivotLine supplied. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json
- S24 — Pinned Tapir CreateSlabs lacks structureType/buildingMaterialId; ModifySlabs has both. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json
- S25 — Pinned Tapir Door/Window requires ownerWallId and centerOffset; accepts favoriteName/libraryPartName. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json
- S26 — Pinned Tapir GetFavoritesByType and GetAvailableLibraryParts are read-only discovery. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json
- S27 — Pinned Tapir catalog lacks GetModelDumpV1; installed APX contract unknown. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json
- S28 — PR162 SceneWriter hosted opening requires $createdGuid of generated wall. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py
- S29 — PR162 verify_readback checks native type/floor but does not establish GH provenance/GDL identity. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py
- S30 — PR74 two-story fixture contains literal buildingMaterialId GUID and nativeGeometryAudit/nativeRoofJunctions=true. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/examples/accelerator/model-first-building.json
- S31 — Priority matrix 20261018 contains 61 entries; Grasshopper historical priority 40 before triad pivot. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json

**Status:** SOURCE_ONLY; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED all 0 for this new triad BUILD-01.
