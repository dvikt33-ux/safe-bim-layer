# Next controlled probes — research backlog

These probes are **not authorized by this file**. Each live write still requires explicit user approval and the exact probe implementation must pass offline audit first.

Global rules for every write probe:

- exact project identity/path checked immediately before dispatch;
- one physical mutating item maximum;
- durable dispatch-start marker before call;
- exact returned GUID persisted immediately;
- exact GUID readback only;
- no search/adoption;
- no blind retry after any possible dispatch;
- mismatch/readback error/transport uncertainty -> STOP / UNKNOWN_OUTCOME;
- preserve raw request/response/readback as evidence fixture;
- no automatic cleanup write after an uncertain probe.

## Probe A — Arc Wall orientation

Prerequisite: update offline contract to Tapir 1.5.9 and independently re-audit.

Purpose: determine which `arcAngle` sign places the D->E quarter-circle on the intended side while preserving the already-proven wall vertical contract.

Readback: exact GUID + floorIndex + beg/end + arcAngle + absolute zCoordinate + bottomOffset + height + thickness/structure.

Do not attempt opposite sign automatically after mismatch.

## Probe B — flat Mesh Z semantics

Prerequisite: fix current builder so base plane and per-vertex Z are not double-counted.

Candidate target for flat ground at absolute -0.500 on story elevation 0.000:

- floorIndex = 0;
- level/base plane offset = -0.500;
- outline vertex `meshPolyZ` contribution = 0.000.

Readback must capture Mesh level and returned polygon vertex Z values sufficient to reconstruct absolute vertex Z.

## Probe C — Morph box body

Prerequisite: replace fake echo verifier with real Tapir 1.5.9 origin/axes/body verifier and confirm porch XY separately.

Create one small cuboid at sacrificial coordinates. Verify exact GUID, origin, transform axes and local body bounding box. Ownership never comes from body similarity.

## Probe D — single-plane Roof positive side

Prerequisite: strict 1.5.9 RoofDetails verifier.

Create one small single-plane roof with known pivot line and angle. Read exact pivotLine, angle, level/class and polygon details. Purpose is to establish which side of directed pivot line rises for positive angle.

No second roof automatically on mismatch.

## Probe E — Hotlink instance

Prerequisite: immutable/versioned test `.mod`, exact hotlink node preflight and dedicated verifier.

Place one instance at a unique origin/rotation. Verify exact instance GUID + hotlinkNodeId + origin + rotation + mirroring/flags. This certifies the strongest repeated-assembly acceleration path.

## Probe F — SEO relation

Prerequisite: relation receipt/reconciliation implementation.

Use two disposable exact GUID elements. Create one defined SEO link. Reread exact operator/target relation and operation/flags. Never infer from visual result.

## Probe G — Trim relation

Prerequisite: relation verifier.

Create one exact trim relationship between disposable elements, then verify through `GetElementTrims` or corresponding relation output.

## Probe H — generated GDL object

Prerequisite: fixed deterministic `LP_XMLConverter` wrapper, source-controlled HSF sample with stable Main GUID, successful offline compile, library preflight.

Load/add the generated library, resolve expected Main GUID to current part name, place one Object, read exact element GUID + libpart details + dimensions/parameters. This is the gate for generic generated parametric content.

## Performance-only read probes

These are read-only and can be performed separately when user authorizes interaction with live Archicad:

- filtered `GetDetailsOfElements` batch timings: 1, 4, 8, 16, 32, 64 GUIDs;
- fields-only verifier subset vs full details/floorPlanPolygons;
- story/resource/favorite/library inventory timing;
- bbox/collision timing for representative target groups.

## Recommended order

1. Arc Wall
2. Mesh
3. Morph
4. single-plane Roof
5. Hotlink instance
6. SEO
7. Trim
8. generated GDL Object

The order balances maturity and project-productivity payoff. Hotlink may be moved earlier once its offline operation wrapper exists because its payoff for repeated assemblies is very high.
