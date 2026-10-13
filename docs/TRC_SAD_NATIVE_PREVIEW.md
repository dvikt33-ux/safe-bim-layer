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
- Third-floor cinema (rear left), bowling/e-sports (front left), continuous
  dining area behind the atrium and right rear, quiet zone/right front.
- Exterior Walls use basic reference lines offset 0.15 m inward from the
  approved outer boundary. A 25.2 m opening at the front is a conceptual
  entrance/c Curtain Wall gap; **no** large door object is invented.
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
