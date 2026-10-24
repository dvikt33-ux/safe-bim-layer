# APA №2 — 23.10.2026 12Z — two independent counteraudits

## Counteraudit A: direction and single writer
Hypothesis: Graphisoft GH Live Connection plus APA provides universal symmetric triad synchronization.
Falsification 1: GH Design with Synchronize TRUE writes AC directly; APA SceneWriter uses its own SQLite journal. Therefore a GH write to an APA-owned object is NOT journaled by SceneWriter. Single-writer invariant fails if both are used on same scope.
Falsification 2: AC -> GH Deconstruct/Extract Settings is a read path, with documented Send Changes action; it does not update arbitrary Rhino edits back into the same AC GUID.
Falsification 3: GH Synchronize FALSE and Rhino Solver Disable are not rollback/commit of a distributed transaction. Rhino.Inside framework is not a verified AC29 connector.
Verdict A: FULL_AUTO_TRIAD_BIDIRECTIONAL = NOT_FOUND. Strict profile GH read/preview + APA sole writer is safe in principle but universal automatic GH->PR74 typed handoff is NOT_FOUND. Minimal future adapter only inside existing compiler if separately approved. No new writer/router/synchronizer created.

## Counteraudit B: native fidelity, runtime and licensing
Hypothesis: official add-on removes G0-G5 blockers.
Falsification 1: official GH AC29 build3000 does not prove local installation on AC29 build5101 or APX binary/schema SHA. Provider != installed contract.
Falsification 2: pinned Tapir CreateSlabs lacks material/structureType; ModifySlabs requires second mutation and explicit approval. GH writes bypass APA journal.
Falsification 3: pinned CreateRoofs default MultiPlane but PR162 Roof adapter readback expects SinglePlane Basic; GH Deconstruct MultiPlane unsupported.
Falsification 4: hosted Door/Window requires actual ownerWallId; GDL part identity not verified by current readback. GetModelDumpV1 absent pinned, installed native BREP capability unverified.
Falsification 5: Rhino8 evaluation is not permanently free: after 90 days saving/plugins stop without license.
Verdict B: G0 BLOCKED, G1 NOT_RUN, G2 SOURCE_ONLY, G3 NOT_AUTHORIZED, G4/G5 NOT_RUN. New OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0. Historical matrix 61 read directly; Grasshopper priority=40 predates triad pivot. Historical PROJECT_PLAN revision182 read-only. Fresh auditor #3 for 2026-10-23 NOT_FOUND in research branch tree; no fabricated independent #3 audit.

Official sources: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ ; https://help.graphisoft.com/AC/29/INT/GC.pdf ; https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm ; https://www.rhino3d.com/download/ ; https://www.rhino3d.com/features/rhino-inside/
Immutable code: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_connected_components.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json
