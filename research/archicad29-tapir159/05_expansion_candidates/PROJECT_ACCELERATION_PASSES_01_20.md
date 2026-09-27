# Project acceleration research — passes 01–20

Goal: make Archicad projects as fast as practical while minimizing routine work and failure risk, without weakening Safe BIM's fail-closed mutation rules.

Baseline: Archicad 29 + Tapir Additional JSON Commands 1.5.9. Tapir tag `1.5.9` resolves to `d0dbb11b13942e014661e1402b07958b70cd9dba`.

No live Archicad writes were performed for this research.

## Pass 01 — separate AI planning from BIM execution

The fastest safe architecture is not “LLM controls Tapir directly”. It is:

`human intent -> optional AI planner -> typed ProjectRecipe -> deterministic compiler -> Safe BIM DAG -> Tapir -> exact-GUID receipts/readback`.

AI is skipped for already-known recipes/macros and is loaded on demand only for ambiguous/unstructured intent. This reduces latency, VRAM/RAM residency, tool-call variability and failure surface.

Related local-AI resource research is kept in `AI_RUNTIME_AND_DEV_ACCELERATION.md` and `../06_integration_audits/AI_RESOURCE_EFFICIENT_ARCHITECTURE.md`.

## Pass 02 — Project Recipe DAG instead of one-off scripts

Use a reusable dependency graph:

1. project/version/identity preflight;
2. story + library + attribute + favorite preflight;
3. primary structure;
4. dependent openings/objects;
5. SEO/trims;
6. zones + classifications/properties;
7. sections/elevations/interior elevations;
8. dimensions/labels/text;
9. views/layouts/drawings;
10. QA/collisions;
11. publisher/export;
12. final audit.

Every write node remains resumable and receipt-bound. This gives repeatability without making one giant unsafe transaction.

## Pass 03 — project flavor/template profile

Tapir 1.5.9 supports Favorites, libraries, attributes, properties/classifications, views and documentation settings. A project profile can declare canonical:

- favorite names;
- libraries;
- layers/attributes/profiles;
- story policy;
- text/label/dimension styles;
- view settings;
- master layouts/publisher expectations;
- classification/property conventions.

This removes repeated parameter entry. Geometry remains explicit. Prefer applying a favorite at element creation through `favoriteName`; explicit payload fields then override the favorite.

Source: `ElementCreationCommands.cpp` 1.5.9. `CreateElementsCommandBase` snapshots/restores tool defaults and reloads defaults per item.

https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp

## Pass 04 — 1.5.9 favorite handling fixes a real batch-default hazard

Tapir 1.5.9 explicitly reloads fresh tool defaults before each create item. Upstream comments say this was live-confirmed necessary: without it, a first wall with `arcAngle` or beam with `slantAngle` could leak that setting into the next item.

Safe BIM should therefore update its pinned schema/contracts to 1.5.9 before certifying new builders. This is reliability, not just functionality.

## Pass 05 — repeated building assemblies should be hotlink modules

1.5.9 provides:

- `CreateHotlinkNodes`;
- `CreateHotlinkInstances`;
- `ChangeHotlinkInstances`;
- `GetHotlinks`;
- `SaveAsModuleFile`.

A reusable module catalog can represent apartment types, bathrooms, facade bays, service cores, room pods and repeated site elements. One exact hotlink instance can replace hundreds of element-by-element writes.

The node layer has a useful idempotency hint: registration text says a node already pointing at the same file is returned rather than duplicated. Instance placement is still a mutation and needs an exact instance receipt.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Examples/hotlink_instances.py

## Pass 06 — never batch physical creates merely to save HTTP calls

`CreateElementsCommandBase::Execute` processes an array inside an undoable command and returns per-item GUID/error results only when the command response comes back. Items can individually fail while later items continue.

If transport is lost after dispatch, a multi-item batch can leave an unknown subset applied with no durable per-item receipt available to the caller.

Therefore production Safe BIM keeps **one physical mutation item per dispatch**. Throughput is improved elsewhere, not by sacrificing reconciliation.

## Pass 07 — batch read-back, not writes

`GetDetailsOfElements` accepts multiple exact element IDs and an optional `fields` selector. Tapir 1.5.9 registration explicitly states that `fields` avoids computing unrequested expensive fields such as `floorPlanPolygons`.

Optimization:

1. dispatch one write;
2. persist exact returned GUID immediately;
3. repeat independent writes in the same DAG layer;
4. issue one/more multi-GUID read-only detail requests containing only verifier-required fields;
5. verify every durable receipt separately.

On crash, unverified receipts are still exact-GUID-reconcilable. Dependent writes must wait until the parent is verified.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp

## Pass 08 — cache read-mostly project state, invalidate instead of polling

Cache within one project identity:

- story map;
- attribute IDs;
- favorite names;
- library-part catalog;
- classification/property definition IDs;
- view/layout navigator IDs;
- read-only element details required by the current job.

Tapir element notifications can invalidate element caches. The implementation sends callbacks with a 100 ms timeout (`SetTimeout(100)`), so notification delivery is intentionally non-durable. Notifications are only dirty hints; they never prove ownership or APPLIED/NOT_APPLIED.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NotificationCommands.cpp

## Pass 09 — use cheap spatial checks before expensive geometry

Tapir exposes `Get3DBoundingBoxes`, `GetCollisions`, relations and connected-element queries. A fast QA ladder is:

1. bbox sanity/placement;
2. targeted collision groups;
3. exact type-specific geometry only for candidates;
4. expensive floor-plan polygons only where needed.

Never use collision/bbox equality as ownership proof; use it for QA and planner feedback.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp

## Pass 10 — use relations instead of rediscovering topology geometrically

1.5.9 provides `GetRelationsOfElements`, `GetConnectedElements`, `GetSubelementsOfHierarchicalElements` and `GetZoneBoundaries`.

This is faster and more robust than repeatedly searching by coordinates for:

- wall/beam connections;
- hosted windows/doors;
- hierarchical stair/curtain-wall/railing children;
- zone boundary/neighbour data;
- roof/shell connected zones.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp

## Pass 11 — zone automation can remove substantial room-program routine

`CreateZones` supports both reference-position/automatic geometry and manual polygon geometry with arcs and holes. Tapir also provides `UpdateZones`, `GetZoneBoundaries` and room images.

For projects with repeated room programs, Safe BIM can generate zones, names, numbers, categories and stamps from a schedule/recipe, then validate adjacency/areas.

Batch zone-boundary reads: Tapir registration notes that recalculation is expensive and should be done for a list in one call rather than one zone per call.

`UpdateZones` remains a project-wide recalculation operation and must be an explicit DAG node.

## Pass 12 — documentation should be generated from the verified model

1.5.9 provides enough primitives for a model-to-document pipeline:

- Section / Interior Elevation / Detail / Worksheet creation;
- associative dimensions;
- associative section dimensions;
- wall thickness dimensions;
- Text/Label creation and modification;
- autotext key discovery;
- layouts/master layouts;
- drawings and drawing updates/links;
- view map folders/views/settings.

This can eliminate a large share of manual sheet setup. Documentation nodes should run only after referenced geometry is verified.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/DocumentCreationCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp

## Pass 13 — Design Options are the correct home for alternatives, not a rollback mechanism

Archicad 29 Tapir 1.5.9 exposes native Design Option reads and writes: options, sets, combinations, active options and moving exact elements between option/main model.

This enables a fast variant workflow:

`recipe variants -> separate design options -> user review -> approved option selection/promote workflow`.

Design Option membership is metadata/lifecycle organization, **not** transactional rollback. Safe BIM still needs exact receipts for every mutation.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/DesignOptionCommands.cpp

## Pass 14 — use ScriptUI for approvals directly inside Archicad

Tapir 1.5.9 exposes `ShowScriptUI` + `GetScriptUIResult`. HTML UI can submit a result back to the add-on.

Best use in Safe BIM:

- room-program forms;
- variant selection;
- confirmation of proposed dimensions/placements;
- capability warnings;
- WAITING_USER resume controls.

The UI never writes the model itself. It returns a typed decision that the deterministic runtime validates.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ScriptUICommands.cpp

## Pass 15 — point picking can remove coordinate-entry routine, but must be isolated

`GetPointFromUser` is new in 1.5.9. It asks the designer to click in Archicad and returns the point.

Critical upstream warning: while Archicad waits for the click/Escape, **every other JSON command queues behind it**.

Therefore it is a deliberate WAITING_USER operation only. Never invoke it from a background agent or prefetch path.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ApplicationCommands.cpp

## Pass 16 — Favorites + explicit geometry should be the default creation style

Favorites are especially valuable for settings with large parameter surfaces: windows, doors, stairs, objects, profiles/material settings and documentation styles.

Policy:

- preflight that favorite exists;
- apply at creation using `favoriteName` where supported;
- explicitly provide critical geometry/placement fields;
- verify the critical post-state;
- never infer ownership from favorite/name alone.

Applying favorites to existing hierarchical elements needs element-type-specific caution because some memos contain geometry.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/FavoritesCommands.cpp

## Pass 17 — profiles/attributes can become reusable construction-system presets

Tapir exposes attribute creation/modification and `CreateProfiles`; 1.5.9 registration describes profile creation/overwrite as copying existing profile geometry and settings.

For common wall/column/beam systems, use a curated attribute/profile catalog rather than regenerate complex section geometry for every project.

Attribute writes are project-global semantic state. They require a separate safe operation class and post-readback by GUID/name/content, not an invisible helper inside geometry creation.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AttributeCommands.cpp

## Pass 18 — SEO and trims replace fragile manual boolean modeling

Tapir 1.5.9 exposes:

- `GetSolidElementOperations`;
- `CreateSolidElementOperations`;
- `RemoveSolidElementOperations`;
- `TrimElements`;
- `GetElementTrims`;
- `RemoveElementTrims`.

These are strong candidates for roof-wall trimming, terrain cuts and boolean relationships because they operate on exact GUID relationships and provide relation read-back.

Use relation-level receipts: operator GUID + target GUID + operation type (or trim relation) + reread. Never adopt a relationship by spatial similarity.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/SolidElementOperationCommands.cpp

## Pass 19 — group exact elements into higher-level assemblies

Tapir group commands return a group GUID and provide reverse reads (`GetGroupsOfElements`, `GetElementsOfGroups`).

This can provide a lightweight assembly layer for generated furniture/annotation/model clusters when a hotlink module would be excessive.

Groups are not ownership; membership should be verified by exact element GUID set. Global Suspend Groups mode is UI/project state and should not be toggled implicitly.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementGroupingCommands.cpp

## Pass 20 — separate model build, QA and publication phases

The final high-throughput pipeline should not continuously publish/rebuild/save after every element.

Recommended phases:

- MODEL: mutations + required exact readback;
- QA: targeted collisions/relations/zones/properties;
- DOCS: views/sections/dimensions/layouts;
- PUBLISH: drawing update + publisher/export;
- CHECKPOINT: explicit project save at selected durable phase boundaries.

`SaveProject` calls `ACAPI_ProjectOperation_Save`; publisher commands are external-output side effects. Treat both as explicit project-global nodes, not hidden per-element helpers.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp

# Audit after passes 01–20

## Highest-value acceleration mechanisms

1. **Recipe DAG** — removes repeated reasoning/script authoring while keeping dependency/safety structure explicit.
2. **Project profile + Favorites** — removes repeated settings work.
3. **Hotlink module catalog** — biggest multiplier for repeated assemblies.
4. **Batched filtered read-back** — reduces JSON/API overhead without batching writes.
5. **Read cache + event invalidation** — eliminates repeated scans/polling.
6. **Relations/bboxes/collisions** — cheaper QA than recomputing geometry externally.
7. **Model-to-document pipeline** — large reduction in sheet/document routine.
8. **ScriptUI + deliberate point-pick WAITING_USER steps** — less coordinate/form entry.
9. **Design Option sandbox** — faster human comparison of alternatives.
10. **On-demand AI + recipe cache** — AI used where it adds value, not kept running for deterministic work.

## Safety principles that acceleration must not violate

- one physical mutating item per transport dispatch;
- exact returned GUID persisted before continuing;
- no blind retry after possible dispatch;
- no geometry search/adoption as ownership;
- dependent writes wait for parent verification;
- read batching is allowed because it is read-only;
- global/project operations are separate high-risk capabilities;
- interactive commands never run in the background;
- AI never owns APPLIED/NOT_APPLIED/DONE or retry policy.

## Gaps requiring follow-up passes

1. Measure filtered multi-GUID readback speed and define optimal batch size.
2. Audit exact hotlink instance read-back fields/reconciliation.
3. Audit trim/SEO timeout and duplicate-relationship behavior.
4. Define a safe canonical Project Profile manifest schema.
5. Define recipe/DAG versioning and migration.
6. Determine which documentation creates return strong exact IDs and which are replace/global operations.
7. Define cache invalidation coverage for element vs project-global changes.
8. Benchmark local AI cold-start/wake/unload against deterministic recipe latency.
9. Audit whether project save checkpoints should be automatic after phases or user policy controlled.
10. Design final capability tiers and certification gates before implementation.
