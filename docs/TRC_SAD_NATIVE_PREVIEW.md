# TRC-SAD APA native plan preview (v1, 13 Oct 2026)

This is an **offline plan compiler**, stacked over PR #70 native BIM-documentation
adapter. It reuses archicad_building_shell.wall(), archicad_bim_graph.compile_graph()
and the pinned installed Tapir schema. No transport, local project connection,
second executor, unreviewed API write, project switch or SaveProject.

## Scope, units, status

- One fixed 184.8 x 142.8 m hexagonal footprint, cut front corners 42 x 21 m.
- The same eight-vertex 42 x 50.4 m bounding atrium on levels 2 and 3.
- Aboveground slabs: 25,507.44 / 23,602.32 / 23,602.32 square metres.
- Total aboveground preliminary geometric slab area: 72,712.08 m2.
- Building levels: basement -4.5, first 0, second +6.3, third +12.6 m.
- Basement footprint and 75,000 m2 target reconciliation remain UNRESOLVED.
- Unverified placeholders for core positioning, circulation and room zoning.
- Third-floor cinema (front left, 60% of wing), bowling/e-sports (rear left, 40% of wing), continuous
  dining area behind the atrium and right rear, quiet zone/right front.
- Exterior Walls use basic reference lines offset 0.15 m inward from the
  approved outer boundary. A 25.2 m opening at the front is a conceptual
  entrance/curtain wall gap; **no** large door object is invented.
- Upper floor slab polygons are split into 4 nonoverlapping regions; no
  unsupported native Slab-hole parameters are fabricated.
- Does **not** draw door swings, real stairs, room partitions, protected
  corridors or official occupancy/egress diagrams.
- All reserved program-area values are computed from their rectangular
  outlines. These are not finalized usable room areas.

## Execution

Read-only geometric preparation:

    python scripts/trc_sad_plan.py --output out/trc-preview.json

Prepare a graph **only if** an external actual GetStories readback supplies
the correctly verified actual native floor indices and exact level values:

    python scripts/trc_sad_plan.py --stories actual-stories.json --output out/trc-graph-preview.json

Contents of actual-stories.json (EXAMPLE ONLY, not verified in any live PLN):

    {
      "1": {"nativeIndex": 0, "elevation": 0.0},
      "2": {"nativeIndex": 1, "elevation": 6.3},
      "3": {"nativeIndex": 2, "elevation": 12.6}
    }

The second mode validates an offline CreateWalls/CreateSlabs DAG against APA's
existing BIM Graph, but returns liveWriteAuthorized=false and nativeWrites=0.
Never hand this preview to a native writer without a separately reviewed and
authorized execution bridge with live project identity, exact materials,
project-specific story mappings, collisions, opening and structural preflight.

## Feature gap

Existing SceneWriter supports Walls/Slabs/Columns and typed library Objects.
A selected GDL Object needs a live library-part identity check. PR #70 supports
actual native views and BIM-data package refresh in limited live tests.

Separate native Fill/Zone/2D symbols, labels, room stamps and dimensions are
**not** qualified through this writer. Do NOT mislabel the polygon preview as
a native Fill or Zone. Implement and audit one additive, scoped native adapter
through the same journal/SceneWriter, then repeat live readback in an isolated
explicitly approved test PLN. Do not enable native Stair or egress semantics
by name alone.

Current status: OFFLINE_PREVIEW_ONLY; normative/engineering/live PLN acceptance
NOT_VERIFIED. No main, APA core, parent PRs, PLN or APX changes.

## User-selected Archicad port 19727 — read-only binding

The port discovery observed candidate TRC ... GP.pln at 19727 under
C:\LocalAI\SafeBIM_Global_Library_Test_Projects. Port 19724 is a different
Tatarstan test PLN and is excluded.

Actual floor levels reported for the TRC candidate are 0 / +3 / +6 metres.
The concept requires basement -4.5, first 0, second +6.3, third +12.6.
These are NOT equivalent; never fake the mapping or edit the original PLN.

From C:\LocalAI\TRC_SAD_Preview after git pull --ff-only, with Archicad open:

    python scripts/trc_sad_port_probe.py --port 19727 --output trc-sad-port19727-readonly.json

The CLI reads GetProjectInfo, GetAddOnVersion, GetStories and rechecks
GetProjectInfo using existing UTF-8 Tapir transport. It refuses any other
port, directory or inconsistent PLN identity. Evidence contains exact path,
actual levels, differences, and liveWriteAuthorized=false; nativeWrites=0.
The expected blocked story-elevation mismatch returns process exit code 2
by design, while preserving the evidence JSON. It does not change the
SceneWriter default port, any material or story, or existing saved PLN.

Native Fill/Zone/annotation adapters and live BIM operations remain separate
work and require accepted contracts and an explicit isolated-test authorization.


## Rapid native 2D floor-plan drafting (no 3D)

Priority: editable 2D Archicad plans, not a new BIM building. The scoped
scripts/trc_sad_draw_2d.py uses the EXISTING APA Tapir UTF-8 transport;
this is not a second general model-writing engine. It only uses
CreateHatches, CreatePolylines and CreateTexts after GetProjectInfo,
GetAddOnVersion and GetStories project guards; it never calls
CreateWalls, CreateSlabs, SetStories, OpenProject or SaveProject.

Observed target: C:\LocalAI\SafeBIM_Global_Library_Test_Projects\ТРЦ с GP.pln
on port 19727, Tapir 1.5.10, with native floors 0/1/2 at +0/+3/+6m.
These floors act only as 2D drawing storage. Titles distinguish
proposed design elevations 0/+6.3/+12.6 from actual native ones.
Basement -4.5m is NOT created and its footprint remains unresolved.

From PowerShell in C:\LocalAI\TRC_SAD_Preview:

    git pull --ff-only
    python scripts/trc_sad_draw_2d.py --port 19727 --floor all
    python scripts/trc_sad_draw_2d.py --port 19727 --floor all --draw

Without --draw, the command prepares and reports the intended 2D operations
without touching Archicad. With --draw it writes native 2D elements on
the open PLN, but does NOT save the PLN. One-shot attempt evidence is written
before the first mutation to trc-sad-2d-19727-attempt.jsonl. If execution
fails or times out, never run --draw again blindly; inspect the log and
current Archicad 2D elements. A second attempt using the same evidence
file is explicitly refused. There is no automatic deletion or rollback.

Native content on each story: building outline, atrium, public gallery
and circulation guide lines; labelled native 2D Hatch areas, and 6 reserved
vertical-core rectangles. Hatches exclude reserve core overlaps, especially
the rear lift/stair within the foodcourt footprint. The user-requested
cinema/bowling swap is applied: left FRONT = cinema (60% of left wing),
left REAR = bowling/e-sports (40%). Foodcourt spans right/rear and behind
the atrium; quiet functions on right progress from rest to cowork to library.

This is a 2D concept drawing, not verified door/egress/MEP, kitchen or
cinema layouts; program labels and provisional square metre reservations
do not imply code approval or physical partitioned rooms. No true BIM Zone,
Stair, Wall, Slab or 3D element is created.

## Measured planning grid — 2D only (after successful existing floor sketches)

The user confirmed native 2D drawing SUCCESS_UNSAVED at port 19727:
27 native Hatches, 51 native Polylines and 46 native Texts. No 3D or
SaveProject. The next priority is coordinate AXES and DIMENSION CHAINS, not
another 3D shell or modification of floor heights.

The file `scripts/trc_sad_grid_2d.py` adds 23 numerical axes 1..23
(X=0..184.8m) and 18 Cyrillic letter axes А..Ф (Y=0..142.8m), on a
confirmed exact 8.4m module. Every second axis indicates a tentative
16.8m planning span, NOT a verified structural support/column grid.
Native 2D primitives are CreatePolylines, CreateCircles and CreateTexts;
no Hatches or previously created plans are recreated. Dimensions in mm
are drawn as non-associative 2D chains with witness/tick markers: 22 x 8400
in X, 17 x 8400 in Y, and overall 184800 x 142800. The atrium bounding
rectangle reads 42000 x 50400. All values are computed from the same
coordinated geometry manifest, not manually inserted arbitrary room areas.

PowerShell from C:\LocalAI\TRC_SAD_Preview, with the same PLN still open:

    git pull --ff-only
    python scripts/trc_sad_grid_2d.py --floor all
    python scripts/trc_sad_grid_2d.py --port 19727 --floor all --draw

The first invocation is strictly offline. The second intentionally adds
native 2D grid lines, markers and dimensions to EXISTING floors 0/1/2 in
`ТРЦ с GP.pln` at port 19727 WITHOUT saving. Other ports/PLN filenames,
Tapir revisions or story mappings are rejected. One-shot attempt record
`trc-sad-grid-19727-attempt.jsonl` prevents blind retries. If there is a
partial failure, inspect in Archicad before rerunning; never repeat the
original `trc_sad_draw_2d.py --draw` operation, which already completed.

Grid circles/text are native editable symbols, while the dimensions are
**plain 2D drawn annotations**, not native associative Dimension elements.
This is appropriate for immediate schematic setting-out; subsequent
structural and normative design must verify real grids/column locations.

No native 3D Walls, Columns, Slabs, Roofs, Zones, or Story edits are executed.


## Retraction of prior 2D drawings — IMPORTANT (Oct 13)

The user explicitly rejected the previously scripted 2D approximation of a
native Archicad grid and asked to remove all our generated drawings without
losing ANY unrelated UNSAVED work. The old two CLI writers now reject
the --draw flag. Do NOT close the unsaved original PLN or use repeated Undo.

Caution: the existing model is LOCAL. GitHub commits DO NOT remove native
elements from the user's open Archicad instance. The existing user-confirmed
floor pass created 27 Hatches + 51 Polylines + 46 Texts at port 19727;
the additional grid attempt may or may not have been executed. Distinguish
those groups by source journals.

### Safe cleanup procedure

1. In Archicad, SAVE AS:
   C:\LocalAI\SafeBIM_Global_Library_Test_Projects\ТРЦ с GP - BEFORE_CLEANUP.pln
   This preserves ALL current unsaved edits, including the unwanted drawings,
   without overwriting the originally saved PLN.
2. While that copied project is still open, SAVE AS again:
   C:\LocalAI\SafeBIM_Global_Library_Test_Projects\ТРЦ с GP - CLEANUP_WORKING.pln
   This leaves the immutable before-cleanup backup on disk.
3. In C:\LocalAI\TRC_SAD_Preview run git pull --ff-only and from that same
   directory run: python scripts/trc_sad_cleanup.py
   By default this reads the immutable first copy and active second copy
   identities, native inventory, all actual authoring GUIDs from:
   trc-sad-2d-19727-attempt.jsonl and (if it exists)
   trc-sad-grid-19727-attempt.jsonl. It checks native element types/stories,
   verifies the original journals are complete and outputs
   trc-sad-cleanup-preflight.json with an approval hash.
   No native writes in preflight.
4. ONLY after reviewing exact GUID counts and success, execute:
   python scripts/trc_sad_cleanup.py --execute --approve-hash HASH_FROM_PREFLIGHT
   This deletes only source-journal GUIDs after exact live project checks
   and expected native type/stories. It creates local
   trc-sad-cleanup-attempt.jsonl BEFORE any native delete, verifies after
   each batch; never auto-retries or saves. Partial outcome requires
   manual inspection, never blind rerun.

This new cleanup has syntax/static CI checks but has NOT yet been demonstrated
on the actual local Archicad PLN. Never claim the deletion is finished until
the exact native response and inventory verification are received. Do NOT
destroy either PLN backup or original.

### Correct NATIVE editable Archicad 29 Grid System

ONLY Design > Grid System in Archicad 29, with native Grid Elements and
associated optional Grid dimensions. The native Grid System is documented
at https://help.graphisoft.com/AC/29/INT/_AC29_Help/070_Documentation/070_Documentation-59.htm .
No substitute lines, circles, texts or DXF imitation. The bundled Tapir
1.5.10 schema does not expose creation of actual Grid Elements, so APA must
NOT pretend the prior script creates one.

The new grid is a structural CONCEPT, not a verified engineering model:
data/trc_sad_structural_grid_v2.json

Direction X, 10 axes 1..10, nine bays (metres):
20, 20, 20, 20, 20, 20, 20, 22.4, 22.4 (184.8 total).

Direction Y, 8 axes А,Б,В,Г,Д,Е,Ж,И, seven bays (metres):
18, 18, 18, 22.2, 22.2, 22.2, 22.2 (142.8 total).

36m interstory long-span option: 0..36m in Y (two x18m bays),
subject to engineering analysis of supporting system and load transfer.
60m roof-only long-span option: X=60..120m, three x20m bays,
covering central atrium region, subject to roof-truss verification.
No unsupported claims of structural member sizing or grid intersection columns.

In native Grid System Settings:
- Enter axis counts and separate consecutive distances above.
- Disable automatic Column/Beam/Object placement.
- Enable segment and overall associative grid dimension settings.
- Place once and verify genuinely editable native Grid Elements.
- Do NOT write until the rejected original 2D elements have been safely removed.
