# Flat Roof + Parapet Research — passes 01–15

Scope: Archicad 29 + Tapir Additional JSON Commands 1.5.9. Research only; no product code, no live write authorization.

## Result

A flat-roof assembly should not be modeled as a single invented object. Use native Archicad elements with a recipe-level assembly:

1. `FlatRoofSloped`: one native Single-plane Roof with a small positive design fall, optionally Composite.
2. `FlatSlabRoof`: one native Slab when a truly horizontal structural body is required.
3. Parapet: native Wall segments around the perimeter.
4. Optional convenience group: after every physical element has its own verified receipt/GUID, group roof/slab + parapet walls with Tapir `CreateGroups`.

This keeps native editability, schedules and element semantics. A group is only an editing/selection convenience; it is not ownership evidence and does not replace per-element receipts.

## Passes

### 01 — Native flat-roof modeling convention
Graphisoft guidance for a conventional flat roof is to use the Roof tool with Single-plane geometry and a small fall. A parapet is a Wall. This matches the desired editable BIM model better than Morph-only geometry.

### 02 — Tapir Single-plane Roof contract
Tapir 1.5.9 selects Single-plane Roof when `pivotLine` is present. `angle` is radians. The roof rises on the left side of the pivot-line direction. Current JSON schema requires `angle > 0` (`exclusiveMinimum: 0.0`).

### 03 — Exact zero-degree roof
The Archicad C++ `API_PlaneRoofData.angle` field itself is documented simply as roof-plane angle; the API documentation does not establish the Tapir JSON schema's `>0` rule as an Archicad limitation. Therefore exact 0° remains `LIVE_PROBE_REQUIRED`; do not patch schema or claim support without AC29 verification.

### 04 — Slab fallback
A Slab is the clean native solution for a truly horizontal body. It is not identical to Roof semantics (notably hosted roof/skylight behavior), so the recipe must choose intentionally instead of silently substituting.

### 05 — Constant-thickness sloping build-up
Graphisoft's flat-top-roof modeling guidance says a constant-thickness sloping structure is naturally represented by a Single-plane Roof and can be composite.

### 06 — Variable fall / flat soffit
For a flat underside with a sloped top, Graphisoft guidance uses Mesh / combinations of Slab and Roof. This should be a later recipe, not conflated with the ordinary constant-thickness flat roof.

### 07 — Parapet element type
Parapet is modeled as Wall. This allows Basic, Composite or Profile structures and normal wall editing.

### 08 — Parapet placement
Safe BIM must compute wall reference-line offset from the desired exterior/interior face alignment. It must not assume centerline unless the recipe explicitly asks for it.

### 09 — Parapet vertical contract
Parapet bottom and top must use StoryResolver and exact wall vertical semantics. No inheritance of roof level semantics.

### 10 — Composite parapet
A parapet may reference a verified Composite attribute. The composite's exact skin definition is authoritative; element `thickness` is only a compatibility/consistency value when Tapir requires it.

### 11 — Grouping
Tapir 1.5.9 `CreateGroups` calls Archicad grouping API and returns a group GUID. Grouping must be a final, independent step after all member elements have verified receipts. If grouping fails, the physical elements remain valid and individually owned.

### 12 — Parapet cap
A parapet cap should be modeled later as a separate native Slab/Roof/Profile/Object recipe depending on required geometry; do not hide it inside Wall dimensions.

### 13 — Drainage/falls
Simple single-direction fall: Single-plane Roof. Complex point drainage / tapered build-up: separate advanced recipe using Mesh/Morph/roof planes only after dedicated geometry certification.

### 14 — Verification
For `FlatRoofSloped`, verify exact roof GUID, class=SinglePlane, floor, level/z, angle, pivotLine, polygon outline, structureType, and exact `compositeId` when Composite. For parapet walls verify exact GUIDs, endpoints, vertical extents, structure type and exact composite/building-material reference.

### 15 — Production gate
No new flat-roof/parapet recipe enters `OPERATIONS` until its independent audit is explicit. Existing fail-closed rules remain unchanged.

## Proposed read-only reference specimens in Test_House

- `FLAT_ROOF_BASIC_REF`: Single-plane Roof, known small pitch, known footprint, Basic structure.
- `FLAT_ROOF_COMPOSITE_REF`: same concept using any known Composite roof.
- `PARAPET_REF`: one or more Wall segments at a known height and thickness/composite.

First probe should only read these elements and their attributes. No automated write is required to learn the contracts.

## Sources

- Graphisoft Archicad 29 Help, Create a Single-plane Roof: https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-61.htm
- Graphisoft Community, How to Create a Flat Top Roof: https://community.graphisoft.com/t5/Modeling/How-to-Create-a-Flat-Top-Roof/ta-p/303418
- Graphisoft Community, basic flat roof with parapet: https://community.graphisoft.com/t5/Modeling/How-to-draw-a-basic-flat-roof-with-a-parapet/td-p/224630
- Archicad 29 C++ API, API_PlaneRoofData / API_ShellBaseType.
- Tapir 1.5.9 exact sources: ExtendedElementCommands.cpp, ElementGroupingCommands.cpp.
