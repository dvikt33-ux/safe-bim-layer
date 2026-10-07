# Archicad Reference Model Protocol

Status: draft acceptance protocol for Safe BIM training fixtures.

## Objective

Build one small fragment correctly by hand in Archicad, read it back through the same interfaces used
by Safe BIM, sanitize the result, and keep it as a canonical fixture for generator comparison.

This protocol does **not** treat visual similarity as sufficient evidence. The fixture records BIM
semantics, host relationships, geometry, story placement, and the relationships between walls, roof,
openings, and structural members.

## Reference fragment

The smallest recommended fragment contains:

1. two connected Wall elements forming a corner;
2. one native Window hosted by one Wall;
3. one native Door if door hosting is in scope for the test;
4. a second-story relationship where appropriate;
5. one normal gable Wall;
6. two correctly formed pitched Roof planes;
7. a correct wall-to-roof result;
8. three or four Beam rafters derived from the accepted roof geometry.

## Manual build requirements

The human reference fragment must itself satisfy
`docs/SAFE_BIM_ARCHICAD_MODELING_STANDARD.md` before capture.

Do not use:

- Morph as Window or Door;
- stepped Wall fragments for a gable;
- wall splitting merely to create a window opening;
- unresolved overlapping roof solids;
- approximate rafters unrelated to the actual roof planes.

## Capture sequence

```text
MANUAL MODEL COMPLETE
-> visual inspection
-> element-type inventory
-> host-relationship read-back
-> geometry/details read-back
-> story/elevation read-back
-> 3D bounds/read-back where available
-> sanitize identifiers
-> serialize canonical fixture
-> generator comparison
```

Capture the following fields where the active Archicad/Tapir transport exposes them:

- element type;
- relative construction role (`wall_a`, `wall_b`, `window_1`, `roof_left`, `rafter_1`, etc.);
- GUID only in raw local evidence, never as the canonical identity;
- host relationship;
- story / floor index;
- base and top elevations;
- wall geometry and thickness;
- Window/Door details and host;
- roof plane geometry, pitch and 3D bounds;
- Beam/rafter endpoints, orientation and 3D bounds;
- connected-element evidence;
- Safe BIM trace properties if present.

## Sanitization

Canonical fixtures MUST NOT contain machine-specific paths, credentials, personal data, production
project names, or identifiers that are not required to express geometry/semantics.

Replace raw GUID-based identity with stable fixture roles, for example:

```json
{
  "role": "window_1",
  "type": "Window",
  "hostRole": "wall_a"
}
```

A separate local evidence file may retain GUIDs for one validation run, but that file must not become
the reusable canonical fixture.

## Canonical comparison

Generator output is compared to the reference fixture by meaning, not by GUID equality.

At minimum compare:

- element-type counts by required role;
- Wall continuity / fragmentation;
- Window and Door host relationships;
- roof plane count and intended adjacencies;
- wall-top relationship to roof;
- rafter endpoint / plane consistency;
- story assignment;
- absence of duplicate generated roles.

Geometry comparisons SHOULD use tolerances rather than exact floating-point string equality.
Tolerance values must be explicit in the test fixture or QA configuration.

## Acceptance

The canonical fixture may be promoted to a reusable Safe BIM pattern only when:

1. the manual fragment passes all applicable blocker rules;
2. read-back is complete enough to distinguish correct BIM semantics from mere visual similarity;
3. sanitization is complete;
4. the comparison procedure can fail on at least one deliberately broken fixture;
5. the generated fragment can be checked after save/restart when persistence is relevant.

If a required relationship is not observable through the current transport, record it as
`NOT_VERIFIED` or `BLOCKED_BY_TRANSPORT`; do not infer it silently.
