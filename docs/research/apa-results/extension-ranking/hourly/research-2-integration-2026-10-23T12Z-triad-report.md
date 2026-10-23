# APA №2 — 23.10.2026 12Z — BUILD-01 triad integration SOURCE report

## G2 P0 concrete result (100/100): official GH native writer conflicts with APA single-writer
Graphisoft Grasshopper–Archicad 29 Live Connection build3000 (Rhino8/Windows) can create native AC elements directly. Existing PR74/PR162 SceneWriter writes via its own SQLite journal. Therefore automatic GH native edits on the same APA-owned objects bypass that journal. No ready-made, proven universal automatic three-way native sync with shared GUID/ownership/rollback and no new writer was identified.

**Safe Profile A — strict single writer (recommended for BUILD-01):** Rhino8/GH compute geometry and parametric previews; AC->GH via Deconstruct/Extract Settings/Send Changes; GH Design Synchronize FALSE for APA-owned objects; native WRITE only existing PR74 typed DAG -> BIM Graph -> SceneWriter/SQLite -> Tapir. Arbitrary GH output -> PR74 typed compiler automatic handoff is NOT_FOUND; no code or new adapter created.
**Profile B — partitioned native ownership:** GH Design may write only GH-owned isolated objects, APA must never mutate those objects without explicit reconciliation. This creates a second physical writer, so it does NOT satisfy literal strict P0 and is not the baseline.

## Version/licensing and direction
- Official Graphisoft AC29 GH Live Connection build3000 for Rhino7/8, Windows 16.8MB, released 2025-10-01. AC30 also uses build3000: do not confuse editions. Installed AC29 build5101 compatibility not runtime-proven. https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
- GH Design/Document + Synchronize TRUE -> AC native create/update. AC Parameter -> Deconstruct -> Extract Settings -> GH read; after AC edit, documented Send Changes. MultiPlane Roof Deconstruct unsupported. https://help.graphisoft.com/AC/29/INT/GC.pdf
- Rhino8 built-in Grasshopper, GrasshopperPlayer, Solver Disable/Enable: useful existing tools, not atomic cross-app transaction. https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm
- Add-on download is official; Rhino8/Archicad require valid underlying licenses. Rhino8 evaluation 90 days; plugins/saving stop thereafter. https://www.rhino3d.com/download/
- Rhino.Inside is an SDK framework, not an identified ready-to-use AC29 connector. https://www.rhino3d.com/features/rhino-inside/

## Native G0-G5 reproducible plan — not executed
G0 READ only: exact AC29 build, active PLN/port, GetProjectInfo/GetStories/GetAddOnVersion, loaded Tapir1.5.10 APX SHA/registered commands, GH add-on installed binary/version, scratch identity. Provider release != runtime contract.
G1 PR74 one structured new two-story brief -> typed DAG/story bindings/host GUID references/material IDs/plan hash; only genuine OFFLINE run can earn OFFLINE_PASS.
G2 Walls/Slabs/Columns/Doors/Windows supported in SceneWriter; Roof adapter wired; Beam adapter exists but run_project wires roof only. Slab CREATE lacks buildingMaterialId/structureType, requires separate ModifySlabs approval/readback. MultiPlane reverse route and actual Door/Window GDL identity readback NOT_FOUND.
G3 only after owner-approved new scratch PLN/port/plan hash: one writer, journal before write, no blind retry after UNKNOWN; GH Synchronize FALSE for APA-owned native elements.
G4 GuardedSave -> GUI close -> reopen -> independent native GUID/type/floor/host/material/BREP; GetModelDumpV1 not in pinned 262, installed native BREP capability unknown. GH preview is not BREP acceptance.
G5 second different structured brief and different scratch PLN; only then evaluate repeatability.

## Direct research record
31 checked SOURCE assertions (not 31 independent test runs); 9 operation scenarios; 2 counteraudits. Read issue #192, NEXT_RESEARCH_PRIORITIES.md, TRIAD-PIVOT 11Z, researcher #1 12Z, researcher #2 11Z, matrix 61 (61 actual items), PROJECT_PLAN rev182 header. Fresh #3 23 Oct absent in research branch tree (NOT_FOUND). PR162 code immutable commit f7c37b84b76c040c417ccd58a5543326e50f673a. Official 22.8MB GC PDF not fully page-audited; indexed official excerpts used.

**Evidence levels:** SOURCE=31 assertions; OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0 for new triad BUILD-01. G0 BLOCKED; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. No main/NEXT/code/PLN/APX modifications, no installations, no LIVE, no PR merge. 06Z remains PARTIAL_NOT_ACCEPTED. MODEL_MODE_NOT_VERIFIABLE.
