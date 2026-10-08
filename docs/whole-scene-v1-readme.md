# Whole-scene v1: one coherent 12-element BIM operation

**Implementation status (2026-10-09):** Candidate for guarded, bounded LOCAL test.
CI has executed the entire sequence with a simulated Tapir API, not a real
Archicad project. The main/deployed Mailbox watcher remains DRY-RUN ONLY.
No user PLN, model, original scripts or existing SQLite data was changed.

## One geometry source of truth

**4.0 × 3.0 m exterior dimensions; 3.0 m height**. At native story index 0
(first actual story floorId=1, elevation 0.0).

- 4 Basic Wall segments (axis lengths 3.8, 2.8, 3.8, 2.8 m).
  Reference line at the center of 0.20 m thickness. Therefore exterior faces
  enclose exactly 4.0 × 3.0 m; wall axes are inset by 0.1 m from each edge.
- 1 Slab with polygon vertices at the exterior 4 × 3 m footprint,
  thickness 0.2 m, Top reference plane at 0 elevation.
- 4 rectangular Columns, each 0.25 × 0.25 × 3.0 m and inside the
  rectangular shell, with centers inset by 0.35 m from the exterior edge.
- 1 hosted Door in south Wall: width 0.9, height 2.1, sill 0.0,
  center offset 1.4 m along its actual host reference segment.
- 2 hosted Windows in north Wall (east-to-west axis): 0.8 × 1.2 m,
  sill 0.9, center offsets 0.9 and 3.1 m. No overlaps or wall boundary violations.

**Derived quantities:** exterior footprint = 12.0 m², interior clear
rectangle without walls = 3.6 × 2.6 = 9.36 m² (columns not deducted);
outer perimeter = 14.0 m; exterior prism = 36.0 m³; opening rectangles =
3.81 m². These do NOT constitute a statutory gross/net area schedule,
structural design, or full compliance certificate.

\`scripts/archicad_scene_v1.py\` produces a schema-valid graph and all
measures. \`scripts/archicad_scene_run.py\` is a separate, **locally invoked**
native writer prototype, not connected to GitHub Mailbox.

## Dry-run before any live test

1. Work in the user-confirmed test PLN ONLY:
   \`C:\LocalAI\SafeBIM_Global_Library_Test_Projects\Тест MER .pln\`
   with project name \`Тест MER \` (trailing space), port 19723.
2. The script checks native \`GetProjectInfo\`, \`GetStories\` index 0
   / floorId 1, \`GetAddOnVersion\` == 1.5.10.
3. It inventories **ALL** existing elements (<= 50,000) and requests
   \`Get3DBoundingBoxes\` in groups of 100. ALL rows must be well-formed:
   a missing 3D bound **fails closed**, including for 2D annotations.
   This limitation can block a valid project; do not bypass it by skipping
   collision checks or blindly choosing a far-away origin.
4. A candidate \`--anchor-x / --anchor-y\` is in **meters** at the southwest
   outside corner. Spatial exclusion envelope includes 0.35m outside every
   scene edge and Z from -0.3m to +3.1m.
5. Preflight prints \`READY_FOR_EXPLICIT_TEST_RUN\`, sourcePlanHash,
   exact targets and checked-existing-element count. It creates **no journal
   and makes no writes**.

For the Windows runtime, use the isolated folder \`work\scene-v1\`. Do NOT
overwrite existing \`work\delivery\archicad_mailbox_wall_host.py\`,
the running watcher script, or local pinned bridge checkout. Download these
five reviewed repository files into the isolated folder:

- \`scripts/archicad_batch_contracts.py\`
- \`scripts/archicad_bim_graph.py\`
- \`scripts/archicad_scene_v1.py\`
- \`scripts/archicad_scene_run.py\`
- \`scripts/archicad_guarded_wall_probe.py\`

Use the already-installed Graphisoft Python environment with \`jsonschema>=4\`.
Pass the **existing** local \`work\mailbox-state\` directory as \`--data-dir\`;
only a NEW \`scene-v1-attempts.sqlite3\` file would be created **if an execute
run actually reaches its reserved-scene stage**.

## Live execution — explicit operator test only, not authorized deployment

\`--execute\` requires a **new** durable \`--scene-id\` and the exact
\`--confirm-plan-hash\` from a current matching-anchor preflight. It checks
project/version/story and a conservatively empty placement envelope again
before touching the model. It inserts a scene reservation before native writes,
and for **each** native step commits \`ATTEMPTED\`, resolved parameters,
operationHash, and **local exact-command/project approval derived from the
operator's explicit test-only --execute** to SQLite with FULL synchronization
before making the call. GUID creation and type-specific geometry readback
must PASS; child Window/Door creation additionally verifies parent Wall GUID
and geometry immediately before writing.

Never auto-retry a scene or step. Unknown outcomes can leave a **partially
created, UNSAVED model** requiring user inspection. No automatic save, delete,
rollback or undo. A successful run yields \`COMPLETE_UNSAVED\`, not proof
that a PLN file was saved. This scene writer has **not been live-tested**.

## Important remaining gates

- Production/primary PLN must NEVER be opened via this runner.
- The real Tapir 1.5.10 source schema is not publicly tagged in the reviewed
  upstream releases. Upstream 1.5.8→1.5.9→1.6.0 Create shapes are stable;
  this does not prove the installed implementation is bug-free.
- The candidate writer uses bounded native **CreateWalls, CreateSlabs,
  CreateColumns, CreateWindows, CreateDoors** only for this exact fixed scene;
  it does NOT add those commands to the deployed Mailbox allowlist.
- Any failed \`Get3DBoundingBoxes\` row blocks writes: explicitly review
  non-3D annotation filtering before attempting a real complete scene.
- First read-only preflight on real test PLN, then safety review and one
  explicit controlled run; no deployment/branch merge before this gate.
