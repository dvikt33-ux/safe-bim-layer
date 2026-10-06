# Closed Loop migration bundle 1 — Window / Door / Slab / Zone

Status: **MIGRATION SPEC — NO NEW BIM RESEARCH**

Purpose: move already-proven BIM capabilities into the current Closed Loop after Stage 4 is VERIFIED. This bundle deliberately reuses old payload/read-back contracts instead of researching Tapir schemas again.

## Global migration rules

For every capability:

1. Input is a typed request, never arbitrary Tapir JSON from the planner.
2. Planner prediction is not factual state.
3. Observe a fresh model state before planning.
4. Check project/model fingerprint immediately before physical write.
5. Persist mutationAttemptId/checkpoint before dispatch.
6. Dispatch exactly once per attempt.
7. Returned GUID alone is insufficient.
8. Perform factual read-back and capability-specific audit.
9. UNKNOWN_OUTCOME follows Stage 4 reconciliation; no blind retry.
10. Produce an Audit Pack.
11. Preserve source/host element invariants.
12. One minimal live regression is enough for migration if the old live recipe still works unchanged.

## M1-WINDOW — native hosted Window

### Proven sources

- `archicad-capability-registry/tests/smoke/native_window_door_continuous_wall.py`
- `feature/working-archicad-mvp/scripts/archicad_write_cycles/hosted_window_cycle.py`
- `feature/working-archicad-mvp/scripts/archicad_executor.py`
- W1/R4 live capability audit.

Canonical live smoke facts:
- host Wall remains one Wall;
- Window type read-back = `Window`;
- Morph fallback = 0;
- host relationship preserved;
- size/offset/sill exercised live.

### Typed request

```json
{
  "action": "create_window",
  "hostWallGuid": "GUID",
  "centerOffset": 2.0,
  "sillHeight": 0.9,
  "width": 1.2,
  "height": 1.4,
  "favoriteName": "optional explicit verified favorite"
}
```

Required validations:
- host GUID exists in current factual dump;
- host type = Wall;
- straight/simple-host restrictions only where required by the migrated verifier;
- opening interval lies inside host;
- opening prism has no disallowed collisions;
- dimensions are positive and within explicit policy limits;
- favorite, if specified, exists.

### Native write

Use existing recipe:
`CreateWindows.windowsData[0]`
with:
- `ownerWallId.guid`
- `centerOffset`
- `sillHeight`
- `width`
- `height`
- optional `favoriteName`.

### Acceptance

PASS requires:
- exactly one new GUID;
- exact native type = Window;
- `relationships.hostGuid == requested hostWallGuid`;
- same home story as host where applicable;
- center offset read-back matches request within tolerance;
- physical Window body exists;
- host body remains closed;
- host outer envelope unchanged;
- host aperture topology changes as expected;
- host surface/material set not unintentionally changed;
- no foreign element additions in the controlled mutation scope.

Do not weaken this to “CreateWindows returned success”.

## M1-DOOR — native hosted Door

### Proven sources

- `archicad-capability-registry/tests/smoke/native_window_door_continuous_wall.py`
- `arena/fix-house-offline-audit-f7d38af:safe_bim_layer.py::insert_door`
- W1/R4 live capability audit.

### Typed request

```json
{
  "action": "create_door",
  "hostWallGuid": "GUID",
  "centerOffset": 6.0,
  "sillHeight": 0.0,
  "width": 1.0,
  "height": 2.1,
  "favoriteName": "optional explicit verified favorite"
}
```

### Native write

Use existing recipe:
`CreateDoors.doorsData[0]`
with the same owner/offset/sill/width/height structure as Window.

### Acceptance

PASS requires:
- exactly one new GUID;
- exact native type = Door;
- requested host GUID matches read-back owner/host;
- host Wall remains a single Wall;
- no Morph fallback;
- requested dimensions/position are factual where supported by read-back;
- no unexpected host/material/story mutation.

If current stock read-back cannot prove a dimension field, that field must be marked `NOT_VERIFIED`, not silently PASS.

## M1-SLAB — Basic Slab

### Proven sources

- `archicad-capability-registry/tests/smoke/basic_slab_favorite.py`
- `feature/working-archicad-mvp/scripts/archicad_write_cycles/hosted_slab_cycle.py`
- `feature/working-archicad-mvp/scripts/archicad_executor.py`
- old house primitive `create_basic_slab`.

Canonical live smoke:
- Favorite `Перекрытие - Общее Железобетонное`;
- native type = Slab;
- structureType = Basic;
- thickness = 0.22 m;
- reference plane = Top;
- 6x4 m outline;
- target absolute Z +3.00 m;
- home story index 1;
- read-back level 0.0 (story-relative).

### Typed request

```json
{
  "action": "create_slab",
  "floorIndex": 1,
  "referenceLevelAbsoluteZ": 3.0,
  "thickness": 0.22,
  "referencePlaneLocation": "Top",
  "polygonXY": [
    {"x":0,"y":0},
    {"x":6,"y":0},
    {"x":6,"y":4},
    {"x":0,"y":4}
  ],
  "favoriteName": "Перекрытие - Общее Железобетонное"
}
```

### Migration rule

Prefer the proven Basic Favorite workflow. Do not invent unsupported `buildingMaterialId` inside `CreateSlabs`.

If a later `ModifySlabs` step is retained from the Working MVP for material inheritance, it must remain a separately checkpointed/verified mutation and must not turn an uncertain first create into a blind multi-write transaction.

### Acceptance

PASS requires:
- one new Slab GUID;
- type = Slab;
- Basic structure where that is the requested contract;
- thickness matches;
- polygon/outline matches requested geometry within tolerance;
- absolute reference elevation = story elevation + story-relative slab level;
- face/material bindings match the explicit migrated contract;
- no extra Slab created;
- no unsupported schema field used.

## M1-ZONE — native Zone

### Evidence status

Live capability evidence exists:
- W1 created a Zone;
- R4 found exact type presence;
- detailed read-back supported;
- summary explicitly records Zone create/presence/read-back PASS.

However, unlike Window/Door/Slab, this revision did **not** locate a dedicated canonical Zone smoke script containing the original W1 request payload.

### Migration policy

Therefore Zone is **not to be re-invented casually**.

Before implementing M1-ZONE:
1. search retained W1 raw artifacts/local evidence for the exact `CreateZones` payload;
2. if found, freeze it as the canonical migration recipe;
3. if not found, inspect the pinned Tapir command schema and build one isolated smoke test;
4. that isolated schema reconstruction is allowed only because the original request recipe is missing, while the capability itself is already live-proven.

### Minimum typed request

The modern request must explicitly encode at least:
- floor/home story;
- polygon/boundary;
- Zone identifier/name/category data required by the actual pinned schema;
- reference elevation/height only when present in the pinned schema and required by the planning contract;
- provenance linking the Zone to a Planning Engine spaceId.

### Acceptance

PASS requires:
- exactly one new GUID;
- exact type = Zone;
- read-back floor/story matches;
- read-back polygon/boundary matches intended room geometry when supported;
- stable link to the originating planning `spaceId` is retained in the Closed Loop evidence even if Archicad itself does not store that ID natively;
- area must be derived from factual read-back geometry or a trusted Zone field, not planner prediction;
- no automatic PASS solely from command success.

## Migration execution order

After Stage 4 VERIFIED:

1. Window + Door in one shared host-wall migration stage.
2. Slab.
3. Zone.
4. Only then combine them in a room/house assembly.

Rationale:
- Window and Door share host semantics and already have one canonical live smoke.
- Slab has an independent canonical Favorite workflow.
- Zone has live capability evidence but weaker recipe preservation and should be isolated once before house assembly.

## Bundle completion gate

`MIGRATION_BUNDLE_1_VERIFIED` requires:
- modern typed operation exists for all four capabilities;
- each migrated operation has one current live regression;
- old live recipe/evidence is cited in the Audit Pack;
- no capability was reimplemented with a weaker acceptance contract;
- no blind retry;
- no planner prediction used as read-back;
- Window/Door preserve host Wall semantics;
- Slab preserves Basic/elevation/polygon semantics;
- Zone has a frozen canonical create/read-back recipe;
- all four are executable through the same modern Closed Loop state machine.
