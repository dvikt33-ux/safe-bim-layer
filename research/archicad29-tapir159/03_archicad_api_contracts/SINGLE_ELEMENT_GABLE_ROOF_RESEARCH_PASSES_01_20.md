# Single-element Gable Roof — deep research passes 01–20

Date: 2026-09-27

Goal: determine whether Safe BIM can create a **true native Archicad gable roof as ONE Multi-plane Roof element**, rather than two independent Single-plane Roof elements, and determine the safest integration path.

Baseline: Archicad 29 + Tapir Additional JSON Commands 1.5.9. No live Archicad write was performed during this research.

## Executive result

**YES — Archicad's native C++ API can represent a true gable as one `API_PolyRoofID` / Multi-plane Roof element.**

The blocker is not Archicad. The blocker is the current stock Tapir 1.5.9 JSON surface: it creates ordinary offset Multi-plane roofs but does not expose the per-pivot-edge `API_RoofSegmentData.angleType` needed to mark selected roof planes as `Gable`, and its current roof readback does not expose that edge data either.

The preferred technical direction is therefore to extend/fork Tapir 1.5.9 with a narrow, source-audited Multi-plane roof pivot-edge contract and matching readback, then certify that capability through Safe BIM. Two independent Single-plane roofs should remain only a fallback/probe tool, not the target representation for a simple gable.

---

## Pass 01 — confirm desired user-visible Archicad object exists

Graphisoft's user guide states that a Multi-plane Roof is a single element despite containing multiple planes and remains one element after editing individual planes.

Source:
https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-60.htm

Older/current Graphisoft gable instructions explicitly describe a gable created with the Multi-plane construction method and state that the created Gable roof is a single Multi-plane Roof element.

Source:
https://helpcenter.graphisoft.com/user-guide/76477/

Conclusion: the requested representation is native Archicad behavior, not a workaround.

## Pass 02 — identify the native element class

Graphisoft API `API_PolyRoofData` is the Multi-plane Roof payload inside `API_RoofType`. It contains global roof levels and the pivot polygon whose edges define the roof planes.

Source:
https://archicadapi.graphisoft.com/documentation/api_polyroofdata

Conclusion: the target is one `API_RoofID` with `roofClass = API_PolyRoofID`.

## Pass 03 — locate the missing native gable/sloped switch

Archicad 29 C++ API exposes:

`API_PolyRoofSegmentAngleTypeID`

with values:

- `APIPolyRoof_SegmentAngleTypeSloped`
- `APIPolyRoof_SegmentAngleTypeGable`

Source:
https://graphisoft.github.io/archicad-api-devkit/group___element.html

This enum is explicitly described as the type of a Multi-plane Roof segment.

Conclusion: a Gable roof is not fundamentally represented as two roof elements. Gable/sloped behavior exists as segment metadata inside the Multi-plane Roof.

## Pass 04 — identify per-segment data structure

Official AC29 DevKit documentation for `API_RoofSegmentData` shows the separately adjustable data of a roof segment, including:

- `angle`
- `eavesOverhang`
- `angleType`
- material/fill overrides

Official DevKit source snapshot:
https://github.com/GRAPHISOFT/archicad-api-devkit/blob/1aac6bf4665b25f08dff1a209ec04d7944a56b88/docs/struct_a_p_i___roof_segment_data.html

Conclusion: the native API supports an angle type at the individual roof-segment level.

## Pass 05 — locate per-pivot-edge storage

Official `API_PivotPolyEdgeData` contains:

- `levelEdgeData`
- `nLevelEdgeData`

where `levelEdgeData` is an array of `API_RoofSegmentData`.

Source:
https://github.com/GRAPHISOFT/archicad-api-devkit/blob/1aac6bf4665b25f08dff1a209ec04d7944a56b88/docs/struct_a_p_i___pivot_poly_edge_data.html

Conclusion: each pivot-polygon edge can carry per-roof-level segment behavior such as Sloped vs Gable.

## Pass 06 — confirm memo channel for those settings

Official `API_ElementMemo` contains `pivotPolyEdges`. Graphisoft describes it as Multi-plane-roof-specific data associated with pivot polygon edges, containing geometry such as angle/eaves overhang and segment attributes.

Source:
https://archicadapi.graphisoft.com/documentation/api_elementmemo

The data is available via `APIMemoMask_PivotPolygon`.

Conclusion: this is a first-class persistent roof memo, not a UI-only setting.

## Pass 07 — confirm create path accepts pivot edge data

Official `ACAPI_Element_Create` documentation says Multi-plane Roof creation requires pivot polygon coordinates/pends/arcs; `pivotPolyEdges` is optional.

Source:
https://archicadapi.graphisoft.com/documentation/acapi_element_create

"Optional" explains why Tapir can create a generic hip roof without it. It does not mean per-edge customization is impossible; supplying `pivotPolyEdges` is the API path for that customization.

## Pass 08 — settle polygon indexing rules

Official `API_Polygon` rules:

- coordinate arrays are 1-based in use;
- the first array record is unused;
- closing coordinates are duplicated;
- an edge is traversed from coordinate `i` to `i+1`.

Source:
https://archicadapi.graphisoft.com/documentation/api_polygon

Official `ACAPI_Element_GetMemo` states the `pivotPolyEdges` array size is `(pivotPolygon.nCoords + 1)` and the first and last records are unused.

Source:
https://archicadapi.graphisoft.com/documentation/acapi_element_getmemo

Safety consequence: for a rectangle represented by four unique vertices plus the duplicated closing vertex (`nCoords = 5`), the real pivot edges correspond to indices 1..4; index 0 and the final record are not semantic edges.

## Pass 09 — check stock Tapir 1.5.9 create schema

Exact Tapir tag 1.5.9 `CreateRoofs` accepts:

- level / floorIndex
- thickness / structure
- polygon geometry
- optional `pivotLine` + `angle` for Single-plane roofs
- `eavesOverhang`
- `levels` for Multi-plane roofs

but no `pivotPolyEdges`, no per-edge `angleType`, and no `Gable`/`Sloped` roof-plane type field.

Exact source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp

Conclusion: stock Tapir 1.5.9 cannot describe the native per-edge gable setting through JSON.

## Pass 10 — inspect stock Tapir's Multi-plane memo builder

Tapir's `BuildRoofMemoFromGeometry` builds the pivot polygon and global roof geometry. It does not populate `memo.pivotPolyEdges`.

The exact 1.5.9 file contains no `pivotPolyEdges` handling in this builder.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp

Conclusion: there is no hidden gable capability behind an undocumented JSON field.

## Pass 11 — reconcile Tapir history

Tapir PR #482 fixed `CreateRoofs`. It explicitly notes that `pivotPolyEdges` are optional for the generic Multi-plane create and live-tested a rectangular Multi-plane payload as a **hip roof**.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/pull/482

Earlier PR #410 had identified missing pivot-edge setup as part of the roof crash/hang problem before #482 found a safe generic hip path.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/pull/410

Conclusion: current Tapir intentionally solved generic/hip creation, not the full per-edge Multi-plane plane-type surface.

## Pass 12 — audit stock Tapir roof readback

Tapir 1.5.9 `GetDetailsOfElements` returns useful Roof details. For a Multi-plane Roof its recorded fixture includes:

- `roofClass: MultiPlane`
- structure/thickness
- level + absolute zCoordinate
- eaves overhang
- global levels
- pivot polygon outline
- roof contour polygon
- holes

but no `pivotPolyEdges`, per-edge `angleType`, or per-edge `levelEdgeData`.

Exact fixture:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Test/ExpectedOutputs/roof_details.py.output

Conclusion: even if another route created the gable, stock Tapir 1.5.9 cannot strictly verify the two gabled ends by authoritative per-edge metadata.

## Pass 13 — find an independent implementation precedent

A separate Archicad connector implementation (Speckle-derived code in `Sid-Master-Repo`) already serializes/deserializes exactly these native structures. Its Roof model exposes:

- `roofPivotPolyEdges`
- `nLevelEdgeData`
- per-level `edgeLevelAngle`
- `eavesOverhang`
- `angleType`

Source model:
https://github.com/Mankirat-Sains/Sid-Master-Repo/blob/ef29a27c22fa1ab4379ce91d768396347512e052/Local%20Agent/Connector/Objects/Objects/BuiltElements/Archicad/ArchicadRoof.cs

This is corroborating implementation evidence, not the authority; Graphisoft's DevKit remains the authority.

## Pass 14 — inspect independent write implementation

That connector's `CreateRoof.cpp` builds one `API_PolyRoofID`, its pivot polygon and global levels, then accepts pivot-edge data and calls `CreateAllPivotPolyEdgeData` to populate `memo.pivotPolyEdges` before element creation.

Source:
https://github.com/Mankirat-Sains/Sid-Master-Repo/blob/ef29a27c22fa1ab4379ce91d768396347512e052/Local%20Agent/Connector/ConnectorArchicad/AddOn/Sources/AddOn/Commands/CreateRoof.cpp

Its mapper maps strings directly to the native enum:

- `Sloped` -> `APIPolyRoof_SegmentAngleTypeSloped`
- `Gable` -> `APIPolyRoof_SegmentAngleTypeGable`

Source:
https://github.com/Mankirat-Sains/Sid-Master-Repo/blob/ef29a27c22fa1ab4379ce91d768396347512e052/Local%20Agent/Connector/ConnectorArchicad/AddOn/Sources/AddOn/TypeNameTables.cpp

Conclusion: the intended native API path is implementable in ordinary Add-On code; it is not merely theoretical.

## Pass 15 — inspect independent memory construction

The precedent allocates one `API_PivotPolyEdgeData` array, then for each configured pivot edge allocates `levelEdgeData` as `nLevelEdgeData * sizeof(API_RoofSegmentData)` and fills the per-level segment entries.

Each segment can receive:

- angle
- eavesOverhang
- angleType
- materials/fill data

Sources:
- `Utility.cpp` in the same repository
- Graphisoft `API_PivotPolyEdgeData` / `API_RoofSegmentData` documentation

Safety correction for our implementation: follow Graphisoft's documented valid-edge indexing, not blindly copy the third-party loop boundaries. The API explicitly says the first and last `pivotPolyEdges` array records are unused.

## Pass 16 — inspect independent readback implementation

The same connector reads `memo.pivotPolyEdges` back from an existing Multi-plane Roof and serializes every per-edge/per-level `API_RoofSegmentData`, including `angleType`.

Source:
https://github.com/Mankirat-Sains/Sid-Master-Repo/blob/ef29a27c22fa1ab4379ce91d768396347512e052/Local%20Agent/Connector/ConnectorArchicad/AddOn/Sources/AddOn/Commands/GetRoofData.cpp

Conclusion: a strict Safe BIM readback contract can be implemented using native authoritative state.

## Pass 17 — geometry verification beyond metadata

Graphisoft documents `ACAPI_Element_Decompose` as the API for enumerating the planes of a Multi-plane Roof.

Sources:
- https://archicadapi.graphisoft.com/documentation/api_polyroofdata
- https://archicadapi.graphisoft.com/documentation/element-manager

This creates a useful **read-only verification layer**: keep ownership bound to the one returned Multi-plane Roof GUID, but optionally decompose it in memory to check generated roof-plane geometry/ridge shape. Decomposition is QA evidence, not ownership evidence and must never cause adoption of other model elements.

## Pass 18 — evaluate alternative workarounds

### Two Single-plane roofs

Technically workable and currently more directly exposed by stock Tapir, but not acceptable as the preferred simple-gable representation because it creates two independent Archicad Roof elements.

Status: fallback/probe only.

### Morph/Shell imitation

Rejected as primary solution. It loses native Multi-plane Roof semantics and is unnecessary because native API support exists.

### UI automation of Custom Plane Settings

Rejected for Safe BIM production. It is modal/UI-state dependent and difficult to reconcile safely after timeout/crash.

### Favorite-only workaround

Not trusted as the solution. Current `CreateRoofs` rebuilds its own pivot memo and stock JSON does not expose edge settings; a Favorite does not give us a strict per-edge input/readback contract.

### Separate foreign connector

Possible, but increases dependency surface. The useful part is the demonstrated native implementation pattern, not adopting another whole connector.

## Pass 19 — integration strategy audit

### Preferred: narrow Tapir fork/extension

Extend the existing `CreateRoofs` / RoofDetails path rather than adding another unrelated write backend.

Candidate JSON contract (name subject to implementation review):

```json
{
  "roofsData": [{
    "level": 3.0,
    "floorIndex": 0,
    "polygonCoordinates": ["...pivot polygon..."],
    "levels": [{"levelHeight": 0.0, "levelAngle": 0.4182243296}],
    "pivotEdgeSettings": [
      {"edgeIndex": 1, "segments": [{"angleType": "Sloped", "angle": 0.4182243296}]},
      {"edgeIndex": 2, "segments": [{"angleType": "Gable"}]},
      {"edgeIndex": 3, "segments": [{"angleType": "Sloped", "angle": 0.4182243296}]},
      {"edgeIndex": 4, "segments": [{"angleType": "Gable"}]}
    ]
  }]
}
```

This example shows the data model only. **Which rectangle edges are the two gable ends depends on the compiled pivot-polygon order and desired ridge direction.** Safe BIM must compute and freeze that mapping, not assume edge numbers globally.

Before physical creation:

- validate edge index is a real pivot edge;
- validate no duplicate edge definitions;
- validate segment count against roof level semantics;
- restrict `angleType` to `Sloped|Gable`;
- require finite/valid pitch values for Sloped entries;
- allocate/zero memo safely;
- never accept caller-supplied `pivotEdgeUnId` as identity.

### Matching readback extension

RoofDetails should return edge-specific state, for example:

```json
"pivotEdgeSettings": [
  {
    "edgeIndex": 1,
    "segments": [
      {"angleType": "Sloped", "angle": 0.4182243296, "eavesOverhang": 0.5}
    ]
  }
]
```

Readback source must be `ACAPI_Element_GetMemo(... APIMemoMask_PivotPolygon ...)` / `memo.pivotPolyEdges`.

## Pass 20 — Safe BIM safety + versioning audit

A custom Tapir binary must **not pretend to be indistinguishable from stock Tapir 1.5.9**.

Current stock command `GetAddOnVersion` simply returns the compile-time `ADDON_VERSION` from `AddOnVersion.hpp`, which is `1.5.9` on the tag.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ApplicationCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnVersion.hpp

Therefore the fork needs an auditable capability identity. Preferred options:

1. add a read-only command such as `GetSafeBIMTapirCapabilities` returning a stable capability/build identifier; or
2. intentionally use a distinct version/build string and update Safe BIM's compatibility gate to require it.

Do not merely patch `CreateRoofs` while leaving Safe BIM satisfied by the generic stock `1.5.9` handshake; that would allow a stock binary without gable support through the same gate.

---

# Intermediate audit after passes 01–10

### Closed

- A one-element gable exists natively in Archicad.
- Native API class is `API_PolyRoofID`.
- Native per-edge `Sloped/Gable` state exists.
- The relevant state lives in `memo.pivotPolyEdges[].levelEdgeData[].angleType`.
- Stock Tapir 1.5.9 does not expose this field.

### Remaining at that stage

- prove practical write/read precedent;
- define Safe BIM verifier;
- determine version/fork identity;
- decide whether decomposition should be part of strict verification;
- empirically verify exact edge/segment behavior on AC29.

# Pre-final audit after passes 11–18

### Closed

- An independent Archicad connector demonstrates both write and read mapping of `pivotPolyEdges` and `angleType`.
- Stock Tapir history confirms current create path deliberately stops at generic Multi-plane/hip behavior.
- Stock Tapir readback is insufficient to prove gabled ends.
- Native decomposition can provide additional read-only geometric QA.
- No UI automation, Morph substitution, or two-roof workaround is technically necessary for the final product.

### Still empirical

1. AC29 live fixture: exact `pivotPolyEdges` produced by a manually created rectangular Gable Roof.
2. Exact expected `nLevelEdgeData` for the simple one-level roof (strong expectation: one segment per pivot edge for one roof level, but certify from live/native readback rather than assumption).
3. Value of `angle` stored by Archicad on a segment whose `angleType=Gable` and whether it is ignored/normalized.
4. Resulting contour/overhang behavior for Gable edges when global roof uses offset overhang.
5. Whether a newly-created roof accepts the minimal per-edge fields or requires additional initialized segment attributes on AC29.
6. Best verifier threshold: metadata-only vs metadata + `ACAPI_Element_Decompose` geometry check.

# Final research verdict

## Can we have one real two-sided gable Roof element?

**Yes. This is the correct native Archicad model.**

## Why did Safe BIM previously choose two Single-plane Roofs?

Because **stock Tapir 1.5.9 exposes single-plane pivotLine/angle and generic Multi-plane levels, but not the native per-pivot-edge Sloped/Gable control required to construct and verify a true gable through JSON.** It was a limitation of the backend surface, not Archicad's roof model.

## Best solution

Build a narrow, auditable Tapir extension/fork that:

1. adds per-pivot-edge roof segment data to `CreateRoofs`;
2. adds the same data to RoofDetails readback;
3. gives the custom binary an explicit Safe BIM capability/build identity;
4. keeps one physical create item per dispatch;
5. returns one Roof GUID;
6. verifies exactly that same GUID after creation;
7. checks `roofClass=MultiPlane`, pivot polygon, levels, and per-edge `angleType` state;
8. optionally uses native decomposition for geometric QA;
9. remains production-disabled until a controlled AC29 live probe + independent audit pass.

## Target capability

`create_native_gable_roof_v1`

Risk class: `W1 EXACT_LOCAL` at the Safe BIM layer **only if** the Tapir extension performs one element creation and returns exactly one GUID. The underlying memo is complex, so this capability still deserves a dedicated geometry verifier and controlled live certification.

## What not to do

- do not settle for two independent roofs as the final simple-gable implementation;
- do not automate UI pet palettes;
- do not adopt a roof by geometric similarity;
- do not expose raw `pivotPolyEdges` directly to an LLM without typed compiler validation;
- do not enable production merely because source research says the API supports it.

Next recommended step: implement an **offline Tapir gable-roof extension prototype** against AC29 DevKit, with schema + pure payload/memo construction tests first, then independent code audit, then one disposable live gable creation/readback probe.