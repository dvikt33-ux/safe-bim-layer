# Architectural AI checkpoint 33 — native global semantic event bridge for precise invalidation

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first
Branch: feature/working-archicad-mvp
Builds on: checkpoints 20–32

## Executive conclusion

Tapir element notifications do not need to carry the whole invalidation problem.

Archicad has a second, first-party notification layer for non-element/global semantic objects:
- Attributes and Attribute Folders;
- Classification Systems and Items;
- Property Groups and Definitions;
- project/view lifecycle changes;
- attribute replacement;
- other UI/environment events as needed.

These event handlers have existed since Archicad 26 and are available in AC29.

Recommended synchronization architecture:

`element mutations -> Tapir element notifications`
+
`global semantic definitions -> tiny native GlobalSemanticEventBridge`
+
`project/view lifecycle -> project/view event callbacks`
+
`reconnect/restart safety -> Difference Generator reconciliation`
-> `facet-level Project Compiler invalidation`.

This is substantially more precise than periodic full-project rereads.

## 1. Generic object-event contract

`API_IObjectEventHandler` provides:
- OnCreated(HashSet<API_Guid>);
- OnModified(HashSet<API_Guid>);
- OnDeleted(HashSet<API_Guid>).

The callback receives GUID sets, not just an undifferentiated 'something changed' flag.

This is a good fit for dependency-graph invalidation keyed by semantic object identity.

## 2. Register/unregister lifecycle

Official API:
- `ACAPI_Notification_RegisterEventHandler(GS::Owner<API_IEventHandler>, out handlerId)`;
- `ACAPI_Notification_UnregisterEventHandler(handlerId)`.

Registration transfers ownership through `GS::Owner` and automatically keeps the Add-On loaded while event handlers are registered.

The returned handler GUID is used for explicit unregistration.

Graphisoft's own example registers a ClassificationSystem event handler directly from Add-On Initialize.

## 3. Attribute events

`API_IAttributeEventHandler` inherits object-event Created/Modified/Deleted semantics.

Use for semantic dependencies such as:
- Building Materials;
- Composites;
- Profiles;
- Surfaces;
- Layers;
- Layer Combinations where represented through the relevant attribute/configuration path;
- Pens/Fills/Line Types where report/document behavior depends on them.

Attribute event payload gives changed object GUIDs.

Do not respond by rereading all attributes.

Map attribute GUID -> dependent element/rule/report facets.

## 4. Attribute replacement needs its dedicated callback

Archicad also exposes:
`ACAPI_Notification_CatchAttributeReplacement(APIAttributeReplacementHandlerProc*)`.

It specifically reports the case where attributes are deleted and replaced by other attributes.

`APIAttributeReplacementHandlerProc` receives `API_AttributeReplaceIndexTable`, mapping old/deleted attribute indices to replacement indices by attribute type.

This should be registered alongside generic Attribute events.

Why it matters:
- a referenced material/profile/surface may silently migrate to another attribute;
- GUID/index-dependent caches can become wrong even if only listening for simple delete/create;
- recipe/favorite verification fingerprints may change.

## 5. Classification events

Dedicated handlers:
- API_IClassificationSystemEventHandler;
- API_IClassificationItemEventHandler.

Both inherit Created/Modified/Deleted GUID-set events.

Invalidate:
- classification applicability;
- Rule IR selectors using classification;
- property availability that depends on classification;
- IFC classification projection;
- schedule/filter/Graphic Override criteria dependent on classification;
- recipe validity envelopes.

Element assignment changes themselves remain element-level changes and should also be caught by element notifications/readback.

## 6. Property definition events

Dedicated handlers:
- API_IPropertyGroupEventHandler;
- API_IPropertyDefinitionEventHandler.

Again, Created/Modified/Deleted GUID-set semantics.

These are critical because a Property Definition can change without any element GUID changing, while the meaning/evaluation of many element values changes.

Invalidate:
- cached property schemas;
- Property Expression dependency graph;
- schedule column bindings;
- Rule IR inputs referencing property definitions;
- IFC property mappings/projections;
- Graphic Override/status schema where applicable.

Element property-value edits continue to use element notifications/readback.

## 7. Visibility notifications are separate project events

Project notifications include:
- APINotify_PropertyVisibilityChanged;
- APINotify_ClassificationVisibilityChanged.

These events indicate UI/visibility configuration changes, not definition creation/modification itself.

Usually they should invalidate:
- documentation/report presentation;
- UI projection;
- export/display policies if they depend on visibility settings.

They should NOT automatically invalidate legal Rule Results unless visibility is itself part of a rule's scope.

## 8. Project lifecycle events useful for reconciliation

`ACAPI_ProjectOperation_CatchProjectEvent` can subscribe to project/application events including:
- New / NewAndReset;
- Open;
- PreSave / Save / TempSave;
- Close / Quit;
- SendChanges / ReceiveChanges in Teamwork;
- ChangeProjectDB;
- ChangeWindow;
- ChangeFloor;
- ChangeLibrary;
- AllInputFinished;
- UnitChanged;
- SideviewCreated / SideviewRebuilt;
- PropertyVisibilityChanged;
- ClassificationVisibilityChanged;
- ShowIn3DChanged.

High-value SBIM uses:
- Open / AllInputFinished -> establish project identity + run reconciliation;
- ReceiveChanges -> conservative reconciliation/dirty mark;
- UnitChanged -> invalidate display/unit-dependent derived values, not SI canonical facts;
- ChangeLibrary -> invalidate library/GDL-dependent recipe/default facts;
- SideviewRebuilt -> documentation freshness event;
- Save -> optional evidence checkpoint, never heavy recomputation;
- Close -> flush local queue/state.

## 9. Navigator View events

`ACAPI_Notification_CatchViewEvent` can observe Navigator item:
- Inserted;
- Modified;
- Deleted.

This should participate in:
- saved-view dependency fingerprints;
- report View/Publisher dirty state;
- Design Option/Renovation/Graphic Override view-context changes when expressed through View modifications.

Do not treat every View change as a model compliance change.

Route it to documentation/view-context facets.

## 10. View 3D settings handler

AC29 DevKit also includes `API_IView3DSettingsEventHandler` / `NotifyView3DSettingsEvent`.

Graphisoft documentation warns that:
- 3D projection/filter/cut/window settings may trigger events;
- navigation can trigger frequent camera-setting changes;
- complex work inside these callbacks can significantly slow Archicad.

Therefore:
- never query/export/solve from callback;
- only enqueue a compact view-context invalidation token;
- ignore pure camera/navigation changes unless a downstream artifact actually depends on them.

## 11. Notification callback safety rule

Graphisoft's Notification Manager documentation explicitly warns:
- notifications arrive in the background without user interaction;
- incorrect callback behavior can block Archicad;
- do not perform time-consuming operations;
- do not make globally disruptive changes from callbacks.

Mandatory SBIM architecture:

`native callback`
-> append fixed-size event record to in-process queue/ring buffer
-> return immediately
-> deferred dispatcher outside callback
-> coalesce events
-> update ProjectRevision/facet dirty sets
-> selectively re-read authoritative state
-> run Project Compiler tasks.

No network call, LLM call, geometry dump, solver invocation or GitHub/HTTP work is allowed in notification callbacks.

## 12. Proposed event record

Minimal native-to-compiler message:

`{`
` event_seq,`
` project_epoch,`
` event_kind,`
` object_kind,`
` operation: created|modified|deleted|replaced|project_event|view_event,`
` guids[],`
` replacement_pairs[]?,`
` native_event_code?,`
` timestamp_monotonic`
`}`.

Do not embed full object payload.

The deferred consumer rereads only what it needs.

## 13. Event coalescing

Within one short debounce/transaction window:
- repeated modifications of same object GUID collapse;
- create+modify => create;
- create+delete before observation may cancel;
- delete dominates later stale reads;
- attribute replacement remains explicit old->new mapping;
- global project events remain ordered barriers.

Undo/redo and Teamwork receive behavior must be live-tested before stronger assumptions.

## 14. Event coverage is still not mathematically complete

Do NOT claim the native event bridge removes reconciliation.

Potential gaps that still require live verification include:
- Story definition/height edits;
- arbitrary project preferences not covered by explicit project event;
- Design Option set/combination definition changes;
- Renovation Filter definition changes;
- Structural Analytical generation-rule changes;
- SAF/IFC translator edits;
- external files/hotlink content changes;
- changes missed while Add-On/process was unavailable.

Therefore Difference Generator and conservative project-context fingerprints remain necessary.

## 15. No existing open wrapper found

Search found no wrapper for these generic event-handler classes in:
- current Tapir;
- davidharutyunyan/archicad-mcp-connector;
- alesdev88/Archicad-MCP;
- SzamosiMate/tapir-archicad-MCP.

This is a legitimate SMALL native bridge.

It should not become a new event framework; only expose Graphisoft events to the existing Project Compiler event queue.

## 16. EVENT-GLOBAL-01

AC29 scratch test:
1. register Attribute handler;
2. register Classification System/Item handlers;
3. register Property Group/Definition handlers;
4. create/rename/modify/delete one of each;
5. record callback operation + GUID set;
6. perform undo/redo;
7. save/reopen;
8. verify handler registration lifecycle;
9. ensure callback remains fast/no reentrancy issues.

Acceptance:
definition-level invalidation uses exact GUID events rather than polling.

## 17. EVENT-ATTRIBUTE-REPLACE-01

1. create two disposable attributes;
2. reference first from model elements;
3. delete first and replace with second through Archicad;
4. capture replacement table;
5. verify dependent elements/favorites/rules can be marked dirty without a full scan;
6. undo/redo;
7. test multiple attribute types.

## 18. EVENT-PROJECT-01

Capture exact sequence for:
- project open;
- AllInputFinished;
- save;
- library change;
- units change;
- Teamwork receive if available;
- view insert/modify/delete;
- floor switch;
- Show Selection in 3D / Show All.

Classify each as:
- identity barrier;
- semantic invalidation;
- documentation-only invalidation;
- UI-only event;
- reconciliation trigger.

## 19. EVENT-COVERAGE-01

Systematically mutate global settings that can affect planned Rule/Action families:
- Stories;
- Renovation Filters;
- Design Options;
- Layer Combinations;
- Graphic Overrides;
- Property Definitions;
- Classifications;
- Attributes;
- Geo Location;
- Project Preferences;
- Structural generation context;
- Hotlinks;
- IFC/SAF translator configuration.

For each, record which event channel fires:
- Tapir element notification;
- global object handler;
- project event;
- view event;
- Difference Generator environmentChanged;
- none.

Anything with no reliable event becomes a conservative reconciliation fingerprint input.

## 20. Revised synchronization hierarchy

### Tier 1 — exact immediate events
- Tapir element notification;
- global object event handlers;
- attribute replacement callback.

### Tier 2 — project/view barriers
- Open / ReceiveChanges / Library / Units / Navigator View events.

### Tier 3 — reconciliation
- Difference Generator ContextBased / 3DModelBased as appropriate.

### Tier 4 — deep audit
- selective/native quantities/relations;
- Model Dump evaluated topology where needed.

## 21. Roadmap changes

STOP / DEFER:
- polling all Property Definitions;
- polling all Classifications;
- polling all Attributes after every model change;
- treating every non-element change as full-project dirty;
- periodic deep Model Dump as a synchronization mechanism.

KEEP / SMALL NATIVE BRIDGE:
- GlobalSemanticEventBridge;
- event queue/coalescer;
- facet dependency index;
- Difference Generator reconciliation;
- explicit coverage tests for event gaps.

## Strategic conclusion

The AC29 model can be synchronized with a layered native event strategy instead of brute-force snapshots:

`exact element events`
+ `exact semantic-definition events`
+ `project/view barriers`
+ `native reconciliation`
-> `targeted facet reads`.

This is likely the biggest remaining reduction in runtime cost and synchronization uncertainty before the live MVP tests.