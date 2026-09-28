# ARENA LIVE TEST PLAN — executable experiments for every UNRESOLVED_LIVE_REQUIRED item

Date: 2026-09-28. Companion to `ARENA_FULL_SYSTEM_AUDIT_20260928.md`. Arena has **not** run any of these; each experiment is specified so that a single live session can grade it.

## 0. Global rules (apply to every LT)

- Target: sandbox `Test_House_WriteSandbox.pln` only. Preflight for every session: `GetAddOnVersion == "1.5.9"` (record exact string), `GetProjectInfo.projectPath` equals the sandbox path, `GetCurrentWindowType`. If any differs → stop.
- All created elements go to layer `SAFEBIM_TEMP` (create once with `CreateLayers` if absent; morphs get the layer via `SetDetailsOfElements` because `CreateMorphs` has no `layerIndex`).
- Payloads below are the `addOnCommandParameters` of `API.ExecuteAddOnCommand` with `commandNamespace:"TapirCommand"`. `BM` = trusted Building Material GUID `922C639B-9875-48DF-A3FC-E0A8AC5F2839`. Coordinates in metres; use a free area of the sandbox (suggested origin x=200, y=200) so nothing touches the house.
- Evidence: write every request/response pair to `audit/live-tests/<date>/raw/<LT-id>/NNN-{req,res}.json` and a `MANIFEST.sha256`; the summary must cite file names. Screenshots optional; never the only evidence.
- Persistence policy: default **do not `SaveProject`**; close without saving at session end (or reopen from the pristine copy). Exceptions are marked per test. Cleanup = `DeleteElements` of every GUID recorded during the test, then `GetElementsByType` to prove absence. If cleanup fails → record `CLEANUP_FAILED`, do not save.
- Never run LT-F3 (crash test) before all other tests of the session are recorded.
- Timing tests (LT-G*): 30 repetitions, interleaved A/B, report median and p95 with raw timings committed.

Helper payloads used repeatedly:

```json
// PROBE(x,y,z,dx,dy,dz): closed morph box for collision probing
{"morphsData":[{"basePoint":{"x":X,"y":Y,"z":Z},"size":{"x":DX,"y":DY,"z":DZ},"buildingMaterialId":{"guid":"BM"}}]}
// COLL(A,B)
{"elementsGroup1":[{"elementId":{"guid":"A"}}],"elementsGroup2":[{"elementId":{"guid":"B"}}],"settings":{"volumeTolerance":0.000001,"performSurfaceCheck":false}}
// EXISTS(type, dbGuid)
{"elementType":"TYPE","databases":[{"databaseId":{"guid":"DB"}}]}
```

---

## LT-A1 — Environment handshake (prerequisite for every session)

- Action: `GetAddOnVersion`, `GetProjectInfo`, `GetCurrentWindowType`, `GetStories`, `GetLayers`.
- Proof: version string, path, window type recorded. Grade: environment LIVE_CONFIRMED for this session only.
- Failure: version ≠ 1.5.9 → all STATIC references in the audit must be re-based; stop.

## LT-A2 — Partial batch commit in `CreateWalls`

- Setup: none. Action: one `CreateWalls` call with three items; item 2 uses `buildingMaterialId` `{"guid":"00000000-0000-0000-0000-000000000001"}` (non-existent); items 1 and 3 valid (`begCoordinate`/`endCoordinate` (200,200)→(203,200) and (200,202)→(203,202), `zCoordinate` 0, `height` 1, `thickness` 0.2, `structureType:"Basic"`, `buildingMaterialId` BM, `floorIndex` 0; array key `wallsData`).
- Proof: response `elements[]` has 2 ids + 1 error; `GetElementsByType Wall` count increased by exactly 2; `GetDetailsOfElements` of the two ids returns walls.
- Interpretation: 2 walls exist → partial commit LIVE_CONFIRMED (matches STATIC). 0 walls → CONTRADICTED (re-read source). 3 walls → the invalid GUID was silently defaulted (new finding: dependency not fail-closed in Tapir → Safe BIM preflight is mandatory).
- Cleanup: delete both GUIDs. Grade after: LIVE_CONFIRMED for batch semantics.

## LT-B1 — `ModifyMorphs(body)` closedness: status flag vs geometry

- Setup: create morph M1 with an explicit closed cube body (8 vertices, 6 quads, outward winding) at (200,210,0), size 1 m, BM. Readback `GetDetailsOfElements` → expect `bodyType:"Solid"`, `isClosed:true` (W7 baseline).
- Action 1: `ModifyMorphs` with the identical body translated +0.5 m in x. Readback → record `isClosed`, `bodyType`, vertex/polygon counts.
- Action 2: `GetCollisions` M1 vs PROBE P1 placed fully inside M1's new position (0.2 m cube at its centre). Action 3: read built-in Volume of M1 (see LT-C2 for property discovery). Action 4: `ModifyMorphs` transformation-only (`xAxis/yAxis/zAxis` identity + `basePoint` shift) on a fresh M2 → readback `isClosed`.
- Interpretation: (`isClosed:false` AND collision found AND volume ≈ 1 m³) → the flag is stale status only; geometry intact → policy "functional verification, keep delete/recreate for SEO operators" (INFERRED→LIVE_CONFIRMED). (`isClosed:false` AND no collision / volume 0) → body really open after Change → `ModifyMorphs(body)` must be banned outright. Action 4 false → transformation-only modify also unsafe (new finding).
- Cleanup: delete M1, M2, P1. Grade: LIVE_CONFIRMED root-cause class (not the Archicad internal cause).

## LT-B2 — Does `GetCollisions` distinguish Solid from Surface bodies?

- Setup: M3 = closed cube (Solid); M4 = same vertices but only 5 faces (open box, `bodyType:"Surface"`); P2 probe inside each.
- Action: COLL(M3,P2a), COLL(M4,P2b).
- Interpretation: M3 collides, M4 does not → volume collision requires a closed solid → `GetCollisions` is a valid functional closedness test (LIVE_CONFIRMED). Both collide → `GetCollisions` does surface/volume mixing; rely on volume property instead.
- Cleanup: delete all.

## LT-B3 — Morph edge type via `ACAPI_Element_ChangeMorphEdgeType` (PREREQ: Tapir PR build)

- Action: `CreateMorphs` body with `edgeDefault:"SoftHidden"`; readback `edgeDefault`; visual check in 3D (shading smooth) optional.
- Interpretation: readback `SoftHidden` → CONTRADICTION of the Tapir comment confirmed live. Readback `HardVisible` → API call ineffective in AC29; escalate to Graphisoft.
- Grade: LIVE_CONFIRMED either way. Cleanup: delete.

## LT-B4 — Re-read the W1 morph

- Action: `GetDetailsOfElements` on `B23F010E-…` (full GUID from W1 notes) if it still exists in the sandbox; record `bodyType`, `isClosed`, polygon count, winding (compute signed volume from vertices/polygons offline).
- Interpretation: negative signed volume or non-manifold edges → W1 body was mis-wound (explains Surface/false); else new unknown.

## LT-C1 — Is `GetCollisions` computed on SEO-evaluated bodies?

- Setup: wall W (basic, BM, (200,220)→(204,220), thickness 0.3, height 3, floor 0). Operator morph O = PROBE(201.5,219.7,1.0,1.0,0.6,1.0) (passes fully through the wall). Probe P3 = PROBE(201.8,219.9,1.3,0.3,0.2,0.3) (entirely inside O ∩ W).
- Action: COLL(W,O) → expect collision (preflight). COLL(W,P3) → expect collision (pre-cut). `CreateSolidElementLinks{"solidLinks":[{"targetId":{"guid":W},"operatorId":{"guid":O},"operation":"Subtraction"}]}` (array key is `solidLinks` in the 1.5.9 schema). `RebuildView{"regenerate":true}`. COLL(W,P3) again; COLL(W,O) again.
- Interpretation: post-cut COLL(W,P3) = **no collision** → `GetCollisions` uses evaluated geometry → rung 3 of the verifier is valid (LIVE_CONFIRMED). Still collides → `GetCollisions` works on raw bodies; rung 3 downgraded to preflight only; `EvaluateElements3D` PR becomes P0.
- Cleanup: `RemoveSolidElementLinks`, delete W, O, P3. Grade: LIVE_CONFIRMED.

## LT-C2 — Do built-in quantity properties reflect SEO cuts?

- Setup: same W and O as LT-C1 (before linking).
- Action: `GetAllProperties` → find built-in definitions whose name contains "Volume" (record GUID + `propertyType` StaticBuiltIn/DynamicBuiltIn, e.g. net/gross volume). `GetPropertyValuesOfElements{elements:[W], properties:[…]}` → V0. Link Subtraction, `RebuildView`, read again → V1.
- Interpretation: V1 ≈ V0 − 0.3·0.6·1.0 (= 0.18 m³ minus nothing outside; adjust for exact overlap) → quantities are evaluated → rung 4 valid. V1 == V0 → not evaluated; check whether a "net volume" variant differs. Record which property GUID/name works (this becomes the canonical Safe BIM quantity source).
- Cleanup as LT-C1.

## LT-C3 — `TrimElements` evaluated proof

- Setup: wall W2 (height 4) and a single-plane roof R (`pivotLine` along the wall, `angle` 0.5 rad, `level` 2.5, polygon covering the wall). Probe P4 above the roof plane but inside the untrimmed wall volume.
- Action: COLL(W2,P4) → collision. `TrimElements{"elements":[{"elementId":{"guid":W2}}],"trimmingElement":{"guid":R},"trimType":"KeepInside"}` (`trimmingElement` is a bare `ElementId`). `RebuildView`. COLL(W2,P4) → expect none. `GetElementTrims` lists the pair.
- Cleanup: `RemoveElementTrims`, delete all.

## LT-C4 — Native Opening evaluated proof (stock rectangular) and shape test (post-PR)

- Setup: wall W3 (200,230)→(204,230), thickness 0.3, height 3. `CreateOpenings{"openingsData":[{"ownerElementId":{"guid":W3},"basePoint":{"x":202,"y":230,"z":1.0},"width":0.8,"height":1.2}]}` (field names per 1.5.9 schema).
- Proof: returned GUID listed by `GetElementsByType Opening` (floor plan DB); COLL(W3, PROBE inside the hole 0.2 m cube at (202,229.9,1.5)) → none; COLL(W3, PROBE at the jamb (202.6,229.9,1.5)) → collision.
- Post-PR variant: 32-gon circular polygon of diameter 0.8; probe at the rectangle corner (202.35,229.9,1.95) — collision means the polygon shape was honoured (circle), no collision means extents-only (Tapir comment right).
- Cleanup: delete opening then wall. Grade: LIVE_CONFIRMED.

## LT-C5 — Destructive Morph boolean (PREREQ: Tapir PR `CreateMorphSolidOperations`)

- Action: two overlapping closed morphs; subtract; expect operands deleted and result GUIDs returned; readback result `isClosed`, volume via LT-C2 property; lineage record written.

## LT-E1 — Is per-write `ChangeWindow` necessary? (also a G benchmark)

- Setup: `ChangeWindow{"windowType":"FloorPlan","storyIndex":0}`.
- Action A: `CreateWalls{"wallsData":[{"begCoordinate":{"x":200,"y":240},"endCoordinate":{"x":203,"y":240},"floorIndex":2,"zCoordinate":8.2,"height":3,"thickness":0.2,"structureType":"Basic","buildingMaterialId":{"guid":"BM"}}]}` while story 0 is displayed (1.5.9 wall fields: `begCoordinate`, `endCoordinate`, `floorIndex`, `zCoordinate`, `height`, `thickness`, `offset`, `arcAngle`, `referenceLineLocation`, `structureType`, `buildingMaterialId|compositeId|profileId`, `favoriteName`). Readback: `floorIndex`, `bottomOffset`/absolute z fields (per W5 semantics). Action B: same via the Arena runtime path (with `ChangeWindow` to story 2 first). 30× each interleaved; record per-call time.
- Interpretation: A readback correct → per-write window switch is unnecessary for walls (LIVE_CONFIRMED) → remove from `ensure_active_story` for element types proven here (repeat for Slab, Column, Object, Morph, and Window/Door which are expected to work because Tapir switches the DB internally). A wrong story/z → the switch stays (document why).
- Cleanup: delete all.

## LT-E2 — Element creation while a non-floor-plan window is in front

- Setup: `ChangeWindow{"windowType":"3DModel"}`; then (second run) `ChangeWindow` to a Section database (create one with `CreateSections` if none; record its `databaseId` via `GetDatabaseIdFromNavigatorItemId`).
- Action: `CreateWalls` (floorIndex 0) and `CreateDoors` into an existing sandbox wall. Then `GetElementsByType{"elementType":"Wall","databases":[{"databaseId":{"guid":FLOORPLAN_DB}}]}` and the same for the section DB.
- Interpretation: success + listed in the floor plan DB → background creation is safe for these types from these windows (LIVE_CONFIRMED). `APIERR_BADDATABASE` → must switch DB; listed in the section DB → **wrong-database write** (critical: forbid creation unless current DB is floor plan).
- Cleanup: delete; `ChangeWindow` back to FloorPlan story 0.

## LT-E3 — Ghost GUID reproduction and the stock existence check

- Setup: section database S with at least one wall cut (use LT-E2's section). Stay on the floor plan (current DB = floor plan).
- Action 1: `GetSectionElements{"databases":[{"databaseId":{"guid":S}}]}` → pick a `sectionElementId` for a wall. Action 2: `CreateAssociativeDimensionsOnSection{"dimensionsData":[{"sectionElementId":{"guid":SE},"referencePoint":{"x":0,"y":-1},"preset":"WallCompositeFaces","direction":{"x":1,"y":0}}]}` **without** changing window. Record the returned GUID G1. Action 3: `GetElementsByType{"elementType":"Dimension","databases":[{"databaseId":{"guid":S}}]}` and the same for FLOORPLAN_DB.
- Action 4: `ChangeWindow{"windowType":"Section","databaseId":{"guid":S}}`, repeat Action 2 → G2, repeat Action 3.
- Interpretation: G1 returned but absent from S (present in floor plan or nowhere) → ghost mechanism LIVE_CONFIRMED; G2 present in S → the check works. G1 already correct → Tapir handles the DB; ghost risk downgraded to INFERRED-historical.
- Cleanup: delete G1/G2 (from their actual DB via `ChangeWindow` if needed); back to floor plan.

## LT-E4 — Read-only database access without window change

- Action: from the floor plan, `GetSectionElements{"databases":[S]}` and `GetElementsByType{"elementType":"Wall","databases":[S]}`; then `GetCurrentWindowType` → must still be FloorPlan.
- Grade: LIVE_CONFIRMED for stock read-side dual context.

## LT-F3 — `Get3DBoundingBoxes` on an undisplayed Slab (CRASH TEST — optional, last)

- Preconditions: all other evidence of the session already written to disk; sandbox not needed afterwards; the user accepts an Archicad relaunch.
- Setup: slab SL on story 0 (create via `CreateSlabs`, 2×2 m at (200,250)). `ChangeWindow{"windowType":"FloorPlan","storyIndex":1}` (slab not shown on story 1 unless "show on stories" includes it — record its story visibility setting).
- Action: `Get3DBoundingBoxes{"elements":[{"elementId":{"guid":SL}}]}`.
- Interpretation: Archicad exits / connection refused → #686 LIVE_CONFIRMED on 1.5.9 → hard rule "no `Get3DBoundingBoxes` for Slab (and any element on a hidden story/layer) until 1.5.10". Correct box returned → downgrade to INFERRED-conditional (still forbid in non-floor-plan windows; try again from the 3D window if the user agrees).
- Cleanup: relaunch; reopen pristine sandbox. Do not save.

## LT-G1 — Batch vs single-call creation

- Action: 10 walls as one `CreateWalls` call vs ten calls; 30 reps interleaved. Report median/p95 per wall.

## LT-G2 — Window switch and rebuild cost

- Action: 30× `ChangeWindow` FloorPlan story 0↔1; 30× `RebuildView` (rebuild) and `RebuildView{regenerate:true}`; 30× `ChangeWindow` to Section and back. Report medians/p95 — this sets the budget for the context scheduler.

## LT-G3 — Per-GUID vs batched readback

- Action: 20 walls; `GetDetailsOfElements` one call with 20 ids vs 20 calls; verify order-by-GUID equality; report timings.

## LT-H1 — Font by role via favorites

- Setup: in the sandbox UI (once), create a Text with the GOST font, then `CreateFavoritesFromElements{"favoritesFromElements":[{"elementId":{"guid":T0},"favorite":"SB_TEXT_GOST_2_5"}]}`; `GetDetailsOfElements T0` → record `style.fontIndex` F.
- Action: `CreateTexts{"textsData":[{"favoriteName":"SB_TEXT_GOST_2_5","coordinate":{"x":200,"y":260,"z":0},"text":"ПРОБА"}]}` → readback `style.fontIndex == F`, `height` as favorite.
- Interpretation: equal → font-by-role without C++ works (LIVE_CONFIRMED); else favorites do not carry font → `GetFonts` PR becomes P1.
- Cleanup: delete text; keep the favorite (persist only if the user agrees to save — mark exception).

## LT-I1 — Composite build → wall → thickness

- Action: `CreateComposites` (two skins 0.2 Core BM + 0.05 Finish BM, separators 3 entries with an existing `lineTypeId`), `GetComposites` readback; `CreateWalls{structureType:"Composite", compositeId, thickness:0.25}`; readback `thickness == 0.25`; then a second wall with `thickness: 0.4` and the same composite → readback shows which value wins (expected: composite; record).
- Cleanup: delete walls; delete composite via `DeleteAttributes` only after `GetElementsByType Wall` shows no user.

## LT-I2 — Profile from `newSkins` → beam → readback

- Action: `CreateProfiles` with one rectangular `newSkins` polygon 0.2×0.4 (BM), `beamType:true`; `GetProfiles` readback; `CreateBeams` with `profileId`; readback `height/width/profileId` (R4 DIFF expected); analytic AABB vs `Get3DBoundingBoxes` (beam is not a slab; allowed).
- Cleanup: delete beam, then profile.

## LT-J1 — Assembly reuse via module + hotlink (stock)

- Setup: two walls + one door in the test area; front window = floor plan.
- Action: `SaveAsModuleFile{"moduleFilePath":"C:\\Users\\Admin\\Downloads\\SAFE_BIM_LIBRARY\\Modules\\sb_test_assembly.mod","elements":[…]}`; `CreateHotlinkNodes{"hotlinkNodes":[{"sourceLocation":"<same path>"}]}` → node id (`existing` flag on repeat call = dedupe check); `CreateHotlinkInstances{"hotlinkInstances":[{"hotlinkNodeId":…,"origin":{"x":210,"y":200,"z":0}}]}`; `GetHotlinks`; `GetElementsByType Wall` count; `GetDetailsOfElements` on an instance wall (hotlinked elements readable?).
- Interpretation: instance placed and elements readable → assemblies route LIVE_CONFIRMED. Failure codes recorded per step.
- Cleanup: delete instance elements (`DeleteElements` on the Hotlink element), remove node if a command exists (none in 1.5.9 → leave; do not save), delete originals and the .mod file.

## LT-K1 — Linear array via `MoveElements{copy:true}`

- Action: one column; 5× `MoveElements` copies at +1 m; verify 6 GUIDs distinct; readback positions; cleanup.

---

## Resulting evidence grades if all pass

| Item | Grade after |
|---|---|
| Batch partial commit | LIVE_CONFIRMED |
| Morph closedness class | LIVE_CONFIRMED (cause class) |
| `GetCollisions` evaluated | LIVE_CONFIRMED or downgraded to preflight |
| Built-in Volume evaluated | LIVE_CONFIRMED with canonical property GUID |
| Opening evaluated proof | LIVE_CONFIRMED |
| Per-write `ChangeWindow` necessity | LIVE_CONFIRMED (either way) |
| Wrong-database write risk | LIVE_CONFIRMED (either way) |
| Ghost GUID mechanism + check | LIVE_CONFIRMED |
| Slab bbox crash | LIVE_CONFIRMED (optional test) |
| Font by role via favorites | LIVE_CONFIRMED |
| Module/hotlink assemblies | LIVE_CONFIRMED |
