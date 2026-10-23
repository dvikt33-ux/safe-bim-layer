# Single-element Gable Roof — integration audit

Companion to `03_archicad_api_contracts/SINGLE_ELEMENT_GABLE_ROOF_RESEARCH_PASSES_01_20.md`.

No live Archicad write was performed.

## Problem restated

Safe BIM should create a normal Archicad **Gable Roof as one Multi-plane Roof element**, not two unrelated Single-plane Roof elements.

Source research establishes that Archicad supports this natively. The missing piece is the stock Tapir 1.5.9 JSON contract.

## Candidate integration paths

### A. Extend/fork Tapir 1.5.9 — RECOMMENDED

Scope:

1. Extend `CreateRoofs` Multi-plane input with typed per-pivot-edge settings.
2. Build `memo.pivotPolyEdges` + each edge's `levelEdgeData`.
3. Extend RoofDetails readback with the same authoritative per-edge data.
4. Add a fork/capability identity handshake.
5. Add examples, schema docs, offline tests and AC25–29 build checks where practical.

Advantages:

- one write backend remains Tapir;
- one native `API_PolyRoofID` returned as one GUID;
- fits existing Safe BIM transport/runtime;
- can potentially be proposed upstream;
- Tapir is MIT licensed.

Risks:

- C++ memory/memo handling must be exact;
- custom binary must not be confused with stock 1.5.9;
- AC29 live certification remains required;
- we become responsible for rebasing the small fork until/if upstream accepts it.

Integration verdict: **best path**.

### B. New dedicated Safe BIM C++ JSON command in a separate APX

Technically viable. It would call the same Graphisoft API directly.

Advantages:
- independent from Tapir internals;
- capability can be purpose-built.

Disadvantages:
- second C++ write backend and Add-On lifecycle;
- duplicated JSON/transport/version handling;
- more installation and maintenance burden;
- additional failure surface.

Verdict: use only if a Tapir fork proves operationally difficult.

### C. Create stock Tapir hip roof, then mutate edges

Not preferred.

`ACAPI_Element_ChangeMemo` cannot update `APIMemoMask_PivotPolygon`; official docs say it currently supports only `APIMemoMask_Polygon` and recommend `ACAPI_Element_Change` for broader changes.

A new C++ command could still use `ACAPI_Element_Change` with pivot memo, but this creates a two-write lifecycle:

`Create generic roof -> modify pivot edges`

That adds an intermediate wrong geometry state and another unknown-outcome boundary.

Verdict: possible fallback for experimentation, inferior to direct correct creation.

Source:
https://archicadapi.graphisoft.com/documentation/acapi_element_changememo

### D. Two Single-plane Roofs

Still useful as a controlled geometry probe or emergency fallback.

Verdict: **not the final simple-gable representation**.

### E. UI automation / Morph / Shell imitation

Rejected for production Safe BIM.

## Proposed native data model

Safe BIM should expose a semantic gable operation, not raw memo pointers:

```text
NativeGableRoofSpec
  floor_index
  absolute_level
  pivot_polygon
  ridge_axis / gable_edge_selection
  pitch
  levels
  thickness / structure / resource IDs
  overhang policy
```

The compiler derives low-level per-edge settings.

For a four-edge rectangular pivot polygon:

- two opposite pivot edges become `Sloped`;
- two opposite end edges become `Gable`;
- the exact edge indices are derived from the desired ridge axis and the frozen polygon order.

Raw edge indices should not normally be authored by AI/user prompts.

## Proposed Tapir JSON extension

Illustrative only; finalize after implementation audit:

```json
"pivotEdgeSettings": [
  {
    "edgeIndex": 1,
    "segments": [
      {
        "angleType": "Sloped",
        "angle": 0.4182243296,
        "eavesOverhang": 0.5
      }
    ]
  }
]
```

Validation rules:

- Multi-plane only (`pivotLine` absent).
- `edgeIndex` in valid pivot-edge range; reject first/last unused memo records.
- no duplicate edge index.
- `segments` count must satisfy the roof-level contract discovered/verified for AC29.
- `angleType` enum exactly `Sloped | Gable`.
- Sloped segment angle finite, positive and under supported roof-angle limits.
- no caller-provided native unique edge ID as ownership.
- no raw pointers/opaque blobs in JSON.

## Proposed readback extension

Current Tapir RoofDetails should gain authoritative edge state:

```json
"pivotEdgeSettings": [
  {
    "edgeIndex": 1,
    "segments": [
      {
        "angleType": "Gable",
        "angle": 0.0,
        "eavesOverhang": 0.5
      }
    ]
  }
]
```

The exact returned `angle` for Gable is deliberately not specified here; it must be copied from native readback, not normalized by assumption.

Implementation source:
`ACAPI_Element_GetMemo(roofGuid, ..., APIMemoMask_PivotPolygon)`.

## Safe BIM receipt/verifier design

Ownership:

- only exact GUID returned by the create response;
- never model search/adoption.

Strict semantic checks:

1. element exists at exact receipt GUID;
2. type = Roof;
3. `roofClass = MultiPlane`;
4. correct floor index;
5. correct relative roof level + absolute zCoordinate contract;
6. pivot polygon topology/order matches compiled recipe;
7. global levels match;
8. edge-settings readback contains expected valid edge set;
9. exactly expected gable/sloped edge pattern;
10. expected Sloped pitch values;
11. expected overhang policy;
12. structure/thickness/resource IDs required by the recipe.

Optional additional geometry QA:

- use native `ACAPI_Element_Decompose` in a read-only command to enumerate resulting roof planes;
- verify the expected number/orientation of sloped planes and ridge relationship.

Decomposition does not change ownership and must not be used to locate/adopt other elements.

## Runtime risk class

Target Safe BIM class after certification: `W1 EXACT_LOCAL`.

Reason: one requested physical create produces one native Roof GUID.

The payload is geometry-complex, so promotion still requires stronger tests than a simple wall create.

## Unknown-outcome behavior

Same Safe BIM rule:

- dispatch begun + timeout/lost response -> UNKNOWN_OUTCOME;
- no blind retry;
- if exact create GUID was durably received, reconcile by that GUID;
- if no GUID exists after possible write, the system cannot infer ownership from a similar gable roof and must STOP/manual-reconcile.

Do not create two alternatives and pick whichever visually looks correct.

## Fork/version identity audit

Tapir 1.5.9 `GetAddOnVersion` returns only compile-time `ADDON_VERSION` = `1.5.9`.

A Safe BIM fork with additional gable semantics must therefore expose an additional deterministic identity.

Preferred:

```json
GetSafeBIMTapirCapabilities -> {
  "baseTapirVersion": "1.5.9",
  "safeBimExtensionVersion": "1",
  "capabilities": ["polyroofPivotEdgeSettingsV1"]
}
```

Safe BIM gate for this operation must require the capability ID, not merely `version == 1.5.9`.

Generic stock Tapir operations may continue to use the normal 1.5.9 gate if desired.

## Build feasibility

Tapir is MIT licensed, so modification and redistribution are permitted subject to retaining the license notice.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/LICENSE

Tapir already builds against Archicad DevKits via CMake/Visual Studio and has an AC25–AC29 build matrix in the repository workflows. AC29 is therefore an existing supported build target rather than a new toolchain.

## Remaining evidence required before code can be production-enabled

### Source/offline

- implement exact schema and allocation rules;
- explicit disposal on every error path;
- unit tests for polygon/edge indexing and malformed segment arrays;
- readback schema fixture including Gable and Sloped edges;
- capability handshake test;
- root Tapir compile/build checks.

### One controlled read-only fixture pass before create probe (preferred)

Manually make one small rectangular Gable Multi-plane Roof in a disposable PLN, then use a temporary read-only build/command to dump:

- pivot polygon coordinates;
- `pivotPolyEdges` valid records;
- `nLevelEdgeData`;
- every segment's `angle`, `eavesOverhang`, `angleType`;
- global `levelNum/levelData`;
- contour polygon.

This closes the remaining AC29 semantics without creating anything through our new command.

### Controlled write probe after independent audit

One disposable rectangular gable roof only:

- expected one `CreateRoofs` request item;
- expected exactly one returned Roof GUID;
- immediately read exact GUID;
- assert MultiPlane + per-edge Gable/Sloped contract;
- optional decompose QA;
- no retry on uncertainty;
- delete only as a separately approved cleanup operation, never automatically after an ambiguous write.

## Final integration verdict

`SINGLE NATIVE GABLE ROOF: FEASIBLE`

`STOCK TAPIR 1.5.9: INSUFFICIENT`

`TAPIR 1.5.9 NARROW FORK/EXTENSION: RECOMMENDED`

`SAFE FOR LIVE IMPLEMENTATION NOW: NO — source/offline implementation + independent audit first`

`TWO SINGLE-PLANE ROOFS AS FINAL DESIGN: NOT REQUIRED`
