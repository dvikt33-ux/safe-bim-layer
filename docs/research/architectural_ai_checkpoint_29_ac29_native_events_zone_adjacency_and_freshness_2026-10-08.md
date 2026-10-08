# Architectural AI checkpoint 29 — AC29 native change capture, zone adjacency, freshness
Date: 2026-10-08
Status: DOCUMENTED / SOURCE_INSPECTED, NOT AC29_TESTED
Target: Archicad 29 ONLY
Branch: feature/working-archicad-mvp
Predecessors: checkpoint 28 (skill runtime / incremental dependency graph), matrices v1.7/v1.8.
Authoritative model: the SINGLE CURRENTLY OPEN Archicad 29 project. No automatic file switching or PLN save.

## Executive finding

The main unanswered issue for incremental BIM QA is NOT the choice of incr/Salsa. It is how the dependency graph learns accurately about manual edits, Undo/Redo, attributes and related zone boundaries WITHOUT doing a 105 MB full 3D dump per operation.

Graphisoft AC29 already provides:
1. Element observation / new-element notifications.
2. Project event notifications, including project database/story events.
3. API_Elem_Head::modiStamp (per-element change stamp).
4. API_ProjectInfo::modiStamp (project change stamp; treat as a hint scoped to project/session, not a universal transaction ID).
5. ACAPI::ZoneBoundaryQuery for native boundary relationships between Zones, adjacent Zones and their bounding elements.
6. Events for changes to attributes, classifications, property definitions and property groups (via the API event interface since AC28).

Therefore prioritize EVENT-01 + ZONE-GRAPH-01 + FRESH-01 BEFORE selecting the graph execution engine.

## Verified public API: native observation

- ACAPI_Element_AttachObserver(elemGuid, notifyFlags): explicitly attaches to existing monitored element; NOT automatic for all existing elements.
- ACAPI_Element_InstallElementObserver(callback): registers shared modification/deletion handler. Exact signature naming should be compiled against installed AC29 DevKit (older docs use ACAPI_Notify_InstallElementObserver).
- ACAPI_Element_CatchNewElement(elementType, callback): new elements by type; register every relevant type, not walls only.
- ACAPI_ProjectOperation_CatchProjectEvent(eventMask, callback): open, close, project database, floors, libraries, send/receive etc.
- API_NotifyElementType carries notifID, element header, database identifier.
- Notifications include BeginEvents/EndEvents and Undo/Redo variants. These events are NOT proof that all constraints are already recomputed.
- Graphisoft Notification Manager explains notifications are tied to Undo records; some operations clear Undo history. Observer notifications may be delivered more than once per operation.
- Graphisoft warns against modifying project database in undo/redo observer notifications.

Sources:
- https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___notify_element_type.html
- https://archicadapi.graphisoft.com/documentation/notification-manager
- https://archicadapi.graphisoft.com/documentation/acapi_element_attachobserver
- https://graphisoft.github.io/archicad-api-devkit/group___project_operation.html
- https://graphisoft.github.io/archicad-api-devkit/group___command.html
- https://helpcenter.graphisoft.com/user-guide/76377/

**Design rule**: notifications should enqueue invalidation records, NOT write BIM in callback or run expensive geometry analyses on UI thread. Perform readback and computation in a subsequent safe execution phase. ACAPI_CallUndoableCommand modifications belong to main thread (official AC29 command docs); transactions and readback must be separate gates.

## Native change stamps

AC29 API_Elem_Head has GUID, type, floorInd, layer, hotlinkGuid and UInt64 modiStamp.
API_ProjectInfo also exposes modiStamp (project scope).

Uses:
- detect changes cheaply through element headers, then materialize full geometry only for GUIDs needing it;
- compare state before and after writes;
- opportunistic reconciliation after missed notifications or app reconnection.

Do NOT assume:
- modiStamp is a monotonically increasing universal revision across reopening/copies;
- unchanged element modiStamp proves its computed shape is unchanged after building material, composite, profile, library, story-height, solid-element operations, external hotlink or property-definition changes;
- matching project modiStamp alone proves no stale cached dependencies.

Sources:
- https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___elem___head.html
- https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___project_info.html

## Native ZoneBoundaryQuery, a direct substitute for custom adjacency discovery

ACAPI::ZoneBoundaryQuery exists since AC27:
- create query;
- call query.Modify with Modifier::Update(processControl) to update BOUNDARY QUERY cache;
- get zone boundaries by exact GUID.

ACAPI::ZoneBoundary has:
- GetElemId() => connected boundary element GUID;
- GetNeighbouringZoneId() => other Zone GUID, APINULLGuid when external;
- IsExternal();
- GetPolygon();
- GetBody();
- GetArea() => *boundary surface polygon area*, NOT room floor area.

Modifier::Update works on Floor Plan or 3D Model windows only.
Sources:
- https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_zone_boundary_query.html
- https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_zone_boundary_query_1_1_modifier.html
- https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_zone_boundary.html

Native result supports a bipartite adjacency index:
Zone GUID <-- boundary relation --> boundary-element GUID <-- boundary relation --> Zone GUID.

Retain domain logic for doors/open passage reachability, circulation, functional adjacency, accessibility, fire compartments, intended wet stacks, geometry reliability, construction module and egress. Boundary adjacency alone is neither occupancy accessibility nor passable adjacency. Additional geometrical impact must include OLD AND NEW extents: simply looking at the post-edit zone graph can miss newly crossed zones or broken/disconnected boundaries.

**Important distinction:** ZoneBoundaryQuery.Modifier.Update does NOT prove recalculation of Zone areas. AC29 manual says Design > Update Zones may be necessary after modifications. Explicit automatic Zone update from native add-on remains NOT_VERIFIED; the public docs above do not establish that a programmatic update is available. A stale, manual, locked or invalid Zone is NOT_VERIFIED or BLOCKED, not PASS.
Source:
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/150_UserInterfaceToolSettings/150_UserInterfaceToolSettings-8.htm
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-136.htm

## Synchronization architecture, HOT/WARM/COLD

BOOTSTRAP (one time after startup/project change or unreliable epoch):
- identify ONLY currently open project; no switching or saving;
- extract 5,296-element source fixture if available, plus stable GUID/type/story/header/modiStamp and reverse dependencies;
- register observer on all relevant existing element types/elements; install catch-new callbacks;
- build native zone-boundary index; store evidence of failed queries;
- issue baseline epoch and stamp vectors.

HOT manual edit:
1. Native callback records GUID / event kind / database; no geometry computation or external blocking calls here.
2. Debounce/group duplicate Begin/End and copies/undo/redo by event batch.
3. Increment pending revision; invalidate OLD impacted cone IMMEDIATELY, including previously cached zone links.
4. Schedule selected-guid readback after command completion, read current header/modiStamp, attributes and geometry as required.
5. For zone boundaries, recompute/refresh native boundary cache in allowed view and match OLD plus NEW adjacency sets.
6. Recompute only affected authoritative calculations; early cutoff only after verified equality and complete dependency provenance.
7. Publish PASS only when source revision, computed revision, normative source version and readback revision are coherent.
8. If update is unverified, publish UNKNOWN/NOT_VERIFIED; never retain stale PASS.

WARM:
- batch edits; zone/egress/structural/member constraints; recover exact old/new zone adjacency; selective normalizing from model.
- attribute/profile/material/priority/classification/story changes can trigger broad invalidation for their dependent consumers.

COLD:
- full resync after open/reload/missing events/undo-reset/hotlink/library merge/provider interruption;
- audit of all required graph edges and quantities;
- full model dump only as fallback/baseline, not per wall drag.

### Status contract
VALIDATED: at exactly known project/model/semantic/rule revisions after successful readback
DIRTY: an event or unexpected stamp invalidated existing check
RECOMPUTING: queued
FAIL: tested requirement violated
UNKNOWN: applicability/source/geometry uncertain
NOT_VERIFIED: no adequate accepted evidence
BLOCKED: operation unsafe/incomplete, preserve user control

No stale PASS is permitted. A GUI Graphic Override is ONLY a visualization projection, not the source of truth.

### Suggested minimal event envelope

~~~yaml
event_id: synthetic_runtime_sequence
project_epoch: uuid_for_open_project_session
command_batch_id: optional
origin: human_or_agent_or_external_or_unknown
element_guid: guid
element_type: Wall
database_id: optional
event_kind: create_modify_delete_undo_redo_project_change
element_modi_stamp_before: optional
element_modi_stamp_after: optional
project_modi_stamp: optional
dirty_domains: [adjacency, quantities, norms]
source: AC29_native
status: PENDING_READBACK
~~~

No guarantee a single event is authoritative. Reconciliation must be possible without it.

## Concurrency & undo-safe acceptance

- The model is committed by Archicad, not by the graph. Never write from a forbidden notification callback.
- A grouped operation can change several elements; avoid publishing transient PASS during the event batch.
- If the user manually edits while an agent plans a write, detect base revision mismatch -> REPLAN_REQUIRED.
- If a write fails midway, use native undoable command where supported and verify final state. API errors, undo success and rollback validity all require independent readback; don't assert universal AC29 atomicity without tests.
- No automatic repair of manually edited model in observer callback.
- A replayed, duplicate or out-of-order callback cannot revalidate stale result.
- Test creates/modifies/deletes, undo/redo, copy, group, hotlink, library, attribute, profile, story height, reopen, manual zones, invalid zones, locked zones, changing window/type and host wall.
- ZoneBoundaryQuery may depend on current view: do NOT silently switch user view to satisfy an automatic check; postpone if not supported and mark not verified.

## Experiments

EVENT-01, sandbox fixture:
1. Register observers for existing all-relevant BIM element types; count successes/errors.
2. Move Wall, create Window, delete Door, move Object, duplicate Slab, change Roof; record event IDs and affected GUIDs.
3. Undo/Redo each; verify post-commit final GUID/state and no modifications in callback.
4. Change story height, hotlink, library, profiles/materials and properties; note which changes fire which events.
5. Close/reopen; ensure reconnect and reconciliation; deliberately drop event to exercise fallback.
6. In concurrent user-edit vs agent planning, detect source revision mismatch and disallow stale action.

ZONE-GRAPH-01:
1. Two adjacent automatically created zones separated by one observed Wall; get connected wall GUID and neighboring zone GUID.
2. Add/delete a door; distinguish geometric adjacency from passability.
3. Move partition so one zone is no longer bounded; after native boundary query refresh capture errors and mark stale quantities.
4. Verify GetArea is vertical boundary SURFACE area, not floor zone area.
5. Verify manual Zones, locked Zones and invalid polygons; no false PASS.
6. Check unsupported current view (Section): defer without switching UI.

FRESH-01:
1. Baseline headers/modiStamps, project stamp and explicit cached dependency keys.
2. Change only one wall; quantify number of full geometry reads relative to baseline.
3. Change shared building material/profile (and therefore evaluated surfaces) without editing element GUID directly; ensure dependencies become dirty even if headers don't.
4. Change rule version only: invalidate affected rule computations without BIM write.
5. Force missing callback/restart/Undo queue reset -> broad scan and trustworthy final results.
6. Verify no stale result ever receives PASS, no omission of mandatory dependencies.

INC-01 extension:
Before comparing incr vs Salsa, measure latency budget by stage:
- event delivery / enqueue;
- native selective readback;
- adjacency query refresh;
- geometry and applicable rule solving;
- incremental graph propagation;
- GUI projection.
If native data collection dominates, microbenchmark differences between graph libraries are not a worthwhile engineering priority.

## Consequences for MVP

P0: EVENT-01 (event capture + post-operation readback), FRESH-01 (revision/dirty safety).
P0: ZONE-GRAPH-01 (native adjacency instead of custom search).
P1: INC-01 (baseline vs incr, Salsa only if integration cost justified).
P1: Zone area refresh capability discovery; keep zones NOT_VERIFIED when unavailable.
P2: Attribute/property/classification and hotlink broader invalidation.
LATER: reliable background workflows and expensive multi-agent infrastructure.

Do not implement a second 3D model database, custom room-adjacency geometry from scratch or permanent polling full 105 MB dumps until these native capabilities fail actual tests.

## Evidence maturity

- Native observer, stamps, ZoneBoundaryQuery, its constraints: DOCUMENTED in official AC29 API.
- Scenario examples / proposed architecture: DESIGN ONLY.
- Whether our native add-on receives complete expected notifications, supported Zone update invocation, actual cost on current 5,296-element PLN: NOT AC29_TESTED.
- No data was written into the user's active PLN or tested on their machine in this research pass.
