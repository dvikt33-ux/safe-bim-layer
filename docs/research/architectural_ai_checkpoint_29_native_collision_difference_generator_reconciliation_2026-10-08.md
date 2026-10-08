# Architectural AI checkpoint 29 — native collision engine and Difference Generator reconciliation

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first
Branch: feature/working-archicad-mvp
Builds on: checkpoints 20–28

## Executive conclusion

Two more infrastructure layers can shrink substantially:

1. generic clash/collision detection should use Archicad's native collision engine through existing Tapir `GetCollisions`;
2. missed-event/reconnect reconciliation should evaluate Archicad's Element Difference Generator before building any custom full-model snapshot-diff engine.

Current recommended synchronization stack:

`Tapir element notifications = hot incremental path`
-> `Difference Generator = reconnect / pre-release reconciliation candidate`
-> `facet re-read of changed GUIDs`
-> `full Model Dump = rare deep audit / geometry fallback, not routine synchronization`.

Difference Generator is promising but remains LIVE-VERIFY until exact AC29 cross-session behavior is measured.

## 1. Native collision engine already exists

Official API:
`ACAPI_Element_GetCollisions(group1, group2, resultPairs, settings)`.

Current Tapir wraps it as `GetCollisions`, registered since Tapir 1.2.2.

Tapir input:
- elementsGroup1;
- elementsGroup2;
- optional settings.

Settings:
- `volumeTolerance`;
- `performSurfaceCheck`;
- `surfaceTolerance`.

Tapir defaults:
- volumeTolerance = 0.001;
- performSurfaceCheck = false;
- surfaceTolerance = 0.001.

## 2. Collision result semantics

Each collision result is a pair of element GUIDs with:
- `hasBodyCollision`;
- `hasClearanceCollision`.

On pre-AC30 Tapir/SDK naming, clearance was historically misspelled `hasClearenceCollision`; AC30 SDK renamed it to `hasClearanceCollision`.

The API does not return:
- exact collision solid;
- exact intersection volume;
- exact intersection area;
- nearest distance;
- penetration vector.

It returns collision classification for the requested pair.

Therefore it is ideal for:
- broad clash candidate generation;
- discipline-to-discipline clash checks;
- fast invalidation/checking before expensive geometry;
- rules whose semantics are simply body/surface/clearance collision.

## 3. Collision threshold semantics

`volumeTolerance`: intersection-body volume greater than this value is considered a collision.

`performSurfaceCheck`: enables surface collision checking.

`surfaceTolerance`: intersection-body surface area greater than this value is considered a collision when surface checking is enabled.

These settings are semantic inputs and MUST enter ActionDigest/cache keys for any collision result.

Never reuse a collision result across different tolerance settings.

## 4. Building Materials participate in collision semantics

`API_BuildingMaterialType` contains:
`doNotParticipateInCollDet`.

Official API description:
the field specifies whether the Building Material participates in collision detection.

Current Tapir exposes this Building Material field as `collisionDetection`.

The MIT connector exposes the clearer positive name:
`participatesInCollisionDetection`
and maps it to the inverted native flag.

Consequence:
native clash behavior is partly attribute-dependent, not geometry-only.

Any collision cache/invalidation must include relevant Building Material collision-participation state.

## 5. Collision is not universal minimum-clearance checking

Do not overinterpret `hasClearanceCollision` as an arbitrary numeric nearest-distance solver.

The public result is only a boolean clearance-collision classification and the API documentation inspected in this pass does not expose a numeric clearance distance through this function.

For regulations such as:
- minimum corridor clearance;
- maintenance envelope distance;
- door swing clearance;
- fire separation distance;
- exact edge-to-opening distance,

the Rule Planner must first determine whether native collision/clearance semantics actually match the legal definition.

If not, use:
- native relations;
- 2D resolved primitives;
- bounding/envelope geometry;
- evaluated mesh only as last resort.

## 6. COLLISION-01

AC29 live fixture:
1. wall vs wall body collision;
2. touching-but-no-volume pair;
3. surface-only intersection with performSurfaceCheck off/on;
4. vary volumeTolerance;
5. vary surfaceTolerance;
6. composite/material where one Building Material does not participate;
7. MEP route/equipment pair;
8. hierarchical element/subelement pair;
9. Generic Opening/host interaction;
10. batch performance on representative groups.

Record:
- returned pair;
- body flag;
- clearance flag;
- tolerance sensitivity;
- Building Material participation behavior;
- runtime.

Acceptance:
generic collision engine stays deleted from roadmap.

## 7. Element Difference Generator is a first-party project/state diff primitive

Official API group description:
functions to get elements which differ between two projects or project states.

Core functions:
- `ACAPI_DifferenceGenerator_GetState`;
- `ACAPI_DifferenceGenerator_GenerateDifference`.

Result `API_ElemDifference` contains:
- `newElements` GUID set;
- `modifiedElements` GUID set;
- `deletedElements` GUID set;
- `isEnvironmentChanged`.

## 8. Environment change is already a useful conservative signal

`isEnvironmentChanged` becomes true when any of these change:
- View or View settings;
- Project Information or Preferences;
- Property Definitions;
- Geographic Location.

This is extremely useful for cache invalidation because some outputs/rules can become stale without a model-element GUID change.

Do not treat `isEnvironmentChanged=false` as proof that every possible project-global dependency is unchanged; validate coverage empirically.

## 9. Three difference algorithms are distinct

`API_ElemDifferenceGeneratorTypeID` provides:

### ModificationStampBased (`MSBD`)
SDK header explicitly says:
- modification-stamp based;
- operates only with file.

Graphisoft migration documentation maps this mode to the former Project Compare API.

### 3DModelBased (`3DMB`)
SDK describes it as 3D-model-based.

Graphisoft migration documentation maps it to the former Model Compare API.

### ContextBased (`CBSD`)
SDK description:
project-context based; difference takes account of connections between elements.

This is especially interesting for SBIM because a changed element may invalidate connected/dependent elements even when their own raw settings did not change.

Do not collapse the three algorithms into one generic revision hash.

## 10. Difference state storage modes

`API_ElemDifferenceGeneratorStateType` supports:
- `APIDiffState_InFile`;
- `APIDiffState_InMemory`;
- `APIDiffState_CurrentProject`.

SDK header states:
- InFile: difference-generator state will be saved in a file;
- InMemory: state will be saved in memory;
- CurrentProject: current project is used for difference generation.

`API_ElemDifferenceGeneratorState` contains:
- stateType;
- stateHdl for InMemory;
- fileLocation for InFile;
- viewGuid.

## 11. ContextBased view handling

For `APIDiff_ContextBased`, `viewGuid` can be supplied so that the difference represents changes of used elements rather than changes caused solely by View settings.

This can be useful for:
- dependency-aware invalidation;
- documentation dirty-state;
- view-specific pre-release reconciliation.

Exact scope must be live-tested.

## 12. No current open wrapper found

Search in this pass found no DifferenceGenerator wrapper in:
- current Tapir;
- davidharutyunyan/archicad-mcp-connector;
- alesdev88/Archicad-MCP;
- SzamosiMate/tapir-archicad-MCP.

Therefore this is a legitimate candidate for a SMALL custom native bridge.

Crucially, it is not a custom diff engine: it is only exposing two Graphisoft APIs.

## 13. Proposed recovery/reconciliation architecture

### Hot path
`Tapir element notification`
-> revision accumulator
-> invalidate semantic facets
-> re-read only necessary data
-> rerun dependent rules/actions.

### Reconnect/restart path
`saved Difference Generator baseline`
vs
`current project state`
-> new/modified/deleted GUID sets
-> environmentChanged flag
-> conservative facet re-read
-> compare with event accumulator
-> repair missed invalidation.

### Pre-release path
run a fresh reconciliation before publish/release gate.

### Rare audit path
use Model Dump/deep 3D snapshot only when:
- Difference Generator behavior is insufficient;
- geometry provenance is being audited;
- rule needs evaluated topology;
- integrity discrepancy is detected.

## 14. Difference Generator does not eliminate revision semantics

Even if DIFF-01 passes, custom responsibilities remain:
- project identity;
- monotonic internal revision;
- event ordering/grouping;
- stale-plan rejection;
- idempotency;
- semantic facet invalidation;
- rule/action dependency graph;
- ActionDigest;
- recovery consistency checks.

Difference Generator only reduces the need for expensive custom full-state comparison.

## 15. DIFF-01 — live semantic coverage matrix

Create baseline and test each difference algorithm against one controlled edit at a time:

Element edits:
- move geometry;
- change dimensions/thickness;
- change surface/material;
- change Building Material/composite/profile;
- change custom property value;
- change classification;
- change home story;
- add/delete element;
- modify hosted opening;
- change hierarchical subelement;
- change Design Option membership;
- change Renovation status.

Global/context edits:
- View settings;
- layer combination;
- Graphic Override combination;
- Renovation Filter;
- Project Info;
- Project Preferences;
- Property Definition;
- Geo Location;
- story settings;
- attribute-only change;
- Structural Analytical generation context.

For each algorithm record:
- new GUIDs;
- modified GUIDs;
- deleted GUIDs;
- environmentChanged;
- runtime;
- false positive/negative;
- whether connected/dependent elements are expanded by ContextBased.

## 16. DIFF-PERSIST-01 — cross-session recovery

Test file-backed state explicitly:
1. create InFile baseline at known path;
2. close Archicad;
3. reopen same PLN;
4. edit one element;
5. compare baseline file vs CurrentProject;
6. restart Add-On only and repeat;
7. restart machine/process if practical;
8. verify baseline file portability/stability;
9. test project mismatch behavior;
10. test baseline against Save As / copied PLN.

Do not rely on cross-session behavior in production until this passes.

## 17. DIFF-CONTEXT-01 — dependency amplification

Create simple connected fixtures:
- joined walls;
- wall + hosted opening;
- slab + wall relation;
- roof trim relation;
- MEP connected route;
- Structural Analytical connected members.

Change only one upstream element.

Compare:
- ModificationStampBased;
- 3DModelBased;
- ContextBased.

Measure whether ContextBased reports only edited GUID or also dependent/connected elements whose effective result changed.

This directly informs semantic invalidation radius.

## 18. DIFF-PERF-01

Benchmark on the existing approximately 5,296-element project:
- state capture time;
- state size in memory/file;
- diff after one edit;
- diff after 100 edits;
- context-based diff;
- 3D-model-based diff.

Compare against:
- Tapir notification latency;
- 12.85 s / 104.93 MB full Model Dump baseline.

Target:
reconciliation should be dramatically cheaper than routine full Model Dump.

## 19. Roadmap changes

STOP / DO NOT BUILD:
- generic collision/clash engine;
- routine deep-mesh clash detection;
- custom full-project diff engine before DIFF tests;
- periodic 104 MB Model Dump solely to learn what changed.

KEEP / SMALL GAP:
- thin DifferenceGenerator command wrapper if live tests justify it;
- event consumer + revision semantics;
- facet-level reread/invalidation;
- deep Model Dump only for residual topology/provenance.

## Strategic conclusion

The emerging AC29 synchronization/QA substrate is now almost entirely native:

`notifications` = immediate change signal
`Difference Generator` = reconciliation candidate
`GetCollisions` = native clash classification
`native quantities/relations` = cheap semantic readback
`Highlight/Graphic Override` = native visual QA
`Issues/BCF` = working findings
`Model Dump` = deep fallback only.

This is a much smaller and safer custom kernel than the earlier snapshot/geometry-heavy architecture.