# Live Safe BIM test summary — R0 to W7

Live validation target:
- Archicad 29
- Tapir Archicad Automation 1.5.9
- Sandbox: `C:\Users\Admin\Downloads\Test_House_WriteSandbox.pln`

## Current status

### R0 — identity
PASS. Exact project and Tapir 1.5.9 verified.

### R1 / R1.1 — geometry and wall details
PASS read-only. Basic and Composite wall semantics read successfully.

### R2 — composite inspection
PASS read-only. Composite `35A9ED6F-2F29-4400-B7DE-9C0DEA93A499` resolves to 0.287 m physical thickness from its skins.

### R3 — manual specimen zoo
PASS read-only. Native MultiPlane roofs, curtain walls, shells, railing, skylights and complex wall specimens detected. Detailed readback remains partial for some complex element types.

### W1 / W1B — creation zoo
PASS after correcting `PolyLine` element-type spelling in the verifier. 21 programmatically created specimens were found by exact element type and GUID.

### R4 — readback audit
21/21 expected GUIDs found. 19 element types supported by `GetDetailsOfElements`; Opening and Stair return `Not yet supported element type`. 40 automatic field comparisons passed and 2 Beam fields differed.

### W2 — beam semantics
PASS. `width`/`height` alone inherited a Profile beam and returned 0.10 x 0.10 m. `isWidthAndHeightLinked=false` alone did not fix it. Explicit trusted `buildingMaterialId` forced Basic beam semantics and returned the requested 0.20 x 0.30 m.

Safe BIM rule: rectangular Basic beams must use an explicit trusted `buildingMaterialId`; never rely on active Beam tool defaults.

### W3 — Composite wall thickness
PASS. Three walls using the same Composite were created with input `thickness` values 0.287, 0.500 and 0.100 m. All read back as Composite with the same `compositeId` and physical thickness 0.287 m.

Safe BIM rule: Composite physical thickness is owned by the Composite definition. Treat an input thickness as validation only; reject conflicts instead of treating it as an independent physical dimension.

### W4 — roof semantics
PASS with important divergence from schema expectation. `CreateRoofs` produced one native `MultiPlane` Roof GUID. A 0-degree single-plane roof was accepted live by Archicad 29 + Tapir 1.5.9 instead of being rejected.

Safe BIM rule: live behavior is authoritative; do not assume the JSON schema's positive-angle restriction describes runtime behavior in this environment.

### W5 / W5B — stories, multi-storey walls and windows
PASS. Walls created on stories 0/1/2 read back at the expected absolute Z values. A wall on story 1 with +0.25 m bottom offset read back at Z=4.75 m and bottomOffset=0.25 m. A wall created at absolute Z=4.5 without `floorIndex` was assigned story 1 by Archicad.

A single wall with home story 0 and height 11.2 m successfully hosted windows at sill heights 0.9, 5.4 and 9.1 m. Those windows read back with floor indices 0, 1 and 2 respectively while preserving the same owner-wall GUID.

### W6 — linked top-story wall
PARTIAL / SEMANTICS DIFFER. `ModifyWalls(relativeTopStory=3)` successfully wrote the story link, and existing/new windows preserved their owner relationship and read back on stories 0/1/2. However `GetDetailsOfElements` continued to report wall `height=3` after the link was set, not 11.2 m. Current stock Tapir readback does not independently expose the actual 3D wall bounds, so the geometric top remains unproven. A later custom C++ probe is required before Safe BIM relies on this linkage for geometric verification.

### W7 — arbitrary Morph geometry
PASS. Three non-box Morph bodies were created and read back exactly:
- asymmetric pyramid: 5 vertices / 5 faces;
- triangular wedge prism: 6 vertices / 5 faces;
- octahedron: 6 vertices / 8 faces.

The wedge was then modified by replacing its complete body. Its GUID stayed unchanged, the geometry changed, and the returned vertex set matched the requested new body exactly.

Safe BIM rule: arbitrary Morph geometry can be round-tripped through the stock Tapir `body` representation (`vertices` + `polygons`) for Create / Read / Modify. This is suitable for controlled custom geometry and later solid-element operators.

## Next live tests

- W8: wall trimming by Roof/Shell and arbitrary Morph subtraction against a wall; verify trim/SEO links and operator edits.
- W9: solid element operations across target/operator types, including link persistence and removal.
- W10: element reference/anchor changes (wall reference line, slab reference plane, beam/column anchors).
- W11: associative dimensions attached to walls; modify wall geometry and verify dimension association and measured value update.
- W12: cascade stress test combining wall, opening/window, associative dimension, story link and solid-element operation.

All write tests are sandbox-only. No SaveProject, OpenProject or DeleteElements is used unless a future test explicitly declares and gates it.
