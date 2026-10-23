# APA-P10.A01.S02 — Native BIM stories, attribute types and typed slab semantics (AC29 / Tapir)

**Date:** 2026-10-11. **Run:** `APA-RUN-20261011-apa-attributes-native-tapir-01`. **Task:** `APA-P10.A01.S02` (attributes, stories, materials, profiles and host links). **State:** `PARTIAL / SOURCE_VERIFIED + USER_LIVE_READBACK`. Not a claim that the full Archicad 29 SDK or deployed Tapir 1.5.10 has been built from independently verified sources.

## 1. Provenance and independently supported root cause

**Installed target observed in user-supplied reports:** Archicad 29, Tapir reports `1.5.10`, test project `Тест MER .pln`; after Save As, `APA_Pavilion_MVP_SUCCESS.pln`, and pre/post-existing GUIDs preserved. The original test's slab `7539799C-D432-42F5-9F31-FED10E1047C4` was created as **Composite**, 0.3 m thick, even though `CreateSlabs` received `thickness=0.2`, then repaired with `ModifySlabs(structureType=Basic, thickness=0.2, buildingMaterialId=...)`; final saved-copy JSON contains `SAVED_COPY_LIVE_READBACK_PASS` for **12/12**, slab Basic, thickness 0.2, bbox Z [-0.200000003,0]. This is direct owner-uploaded evidence, independently examined but **not** our direct access to their Archicad process.

See [raw-evidence analysis and checksum](apa-p20-a02-s03-saved-pln-live-readback-20261010-222136.md), [initial failure / repair report](../2026-10-10/apa-live-user-log-20261010-200512z-pavilion-slab-readback.md). The operator attested save → full close → reopen → read-only audit. This applies only to one fixed scene; not a universal writer.

**Primary Archicad 29 user documentation:**
- [Slab Tool Settings AC29](https://help.graphisoft.com/AC/29/INT/_AC29_Help/150_UserInterfaceToolSettings/150_UserInterfaceToolSettings-6.htm): on **Composite** slabs thickness comes from the **sum of Composite skin thicknesses**, cannot be edited in Slab Settings. Basic slab permits direct thickness editing. Basic reference plane Top/Bottom; Composite may use Top/Bottom/CoreTop/CoreBottom.
- [Composite Structures AC29](https://help.graphisoft.com/AC/29/INT/_AC29_Help/025_Attributes/025_Attributes-26.htm): composites consist of Building Materials and separator lines and can be used on walls/slabs/roofs/shells.
- [Graphisoft SDK API_StoryType](https://archicadapi.graphisoft.com/documentation/api_storytype): `index` is the native story index; `floorId` is an independent identifier; `level` is the absolute story elevation. Do not assume first human floor maps to `index=1`.
- [Graphisoft SDK Attribute Overview](https://archicadapi.graphisoft.com/documentation/attribute-overview): attribute identities include GUID and database index. Attribute IDs must be resolved in **the active project**, not copied blindly between PLNs.
- [Graphisoft SDK API_CompWallType](https://archicadapi.graphisoft.com/documentation/api_compwalltype): `totalThick`, `nComps`, `use with` flags and skins are native attribute semantics.

**Exact project-reviewed Tapir command contract** pinned in [PR16 base commit `bcac2e821a95f927fa6ae9f5fa5742b45d9ca2dd`](https://github.com/dvikt33-ux/safe-bim-layer/blob/bcac2e821a95f927fa6ae9f5fa5742b45d9ca2dd/schemas/tapir-live-1.5.10/tapir-scene-live.json). This is a **repository snapshot labelled 1.5.10**, not independently established byte-for-byte correspondence with the installed APX.

## 2. Typed native readback / creation capability matrix

| Capability / native distinction | Available Tapir contract (pinned snapshot) | Expected safety readback and failure condition | Evidence status |
|---|---|---|---|
| Native stories | `GetStories` yields `firstStory, lastStory, actStory, skipNullFloor, stories[index,floorId,level,height,...]` | Resolve actual `index` by expected floorId/name/level; `floorIndex` is the API index, not human floor number. Re-read `GetDetailsOfElements.floorIndex`; verify project identity before and after. | **SOURCE_VERIFIED + LIVE user test**: first human storey has `index=0, floorId=1, level=0`. |
| Building Material | `GetAttributesByType(attributeType=BuildingMaterial)`; `GetBuildingMaterials(attributeIds)` | Confirm attribute ID/GUID, name and application in **current project**; `GetDetailsOfElements.details.buildingMaterialId` per Wall/Basic Slab/Column and 3D bbox. Avoid implicit default or **GUID from another PLN**. | **SOURCE_VERIFIED + LIVE selected GUID** `922C639B-9875-48DF-A3FC-E0A8AC5F2839` for the fixed test scene only. |
| Composite | `GetAttributesByType(Composite)`; `GetComposites(attributeIds, fields=[useWith,skins,separators])` | Ensure `useWith` supports target element type, skin thickness/properties, expected total thickness and placement of core reference plane. Read `structureType=Composite`, `compositeId`, `thickness`. Never assume `thickness` request overrides layers. | **SOURCE_VERIFIED + LIVE failure demonstrated**: inherited Composite ID `A8836EE9-5C72-492B-A7F6-30EFED26B3EE`, 0.3 m. Specific selection-default algorithm **NOT_VERIFIED**. |
| Basic Wall | `CreateWalls` accepts `structureType=Basic`, `buildingMaterialId`, `thickness`, `floorIndex`, coordinates and reference line. | Read both reference-line endpoints, type, beginning/end thickness, height, bottomOffset, floor index, building material. | **SOURCE_VERIFIED + LIVE user test PASS 4 walls**. |
| Basic Slab **existing 1.5.10** | `CreateSlabs` accepts `favoriteName`, `level`, `thickness`, `referencePlaneLocation`, `floorIndex`, polygon; **no** `structureType` or `buildingMaterialId` in this snapshot. `ModifySlabs` accepts `structureType`, `buildingMaterialId`, `compositeId`, `thickness`. | On test PLN, Create → durable journal → readback; if undesired Composite or wrong thickness, **stop**. A separately approved, one-shot ModifySlabs is possible; re-read material/type/thickness, bbox, polygon and level. Never replay Create after ambiguous error. | **SOURCE_VERIFIED + LIVE user test**: exact failure and guarded repair PASS. One-off flow does not prove a general auto-repair policy. |
| Composite Slab | `CreateSlabs` may use a named Favorite after **read-only favorite validation**; `ModifySlabs` can select `Composite` and `compositeId`. | Enforce `Composite.useWith` includes `Slab`; use desired skin-sum thickness; confirm `referencePlaneLocation` for CoreTop/Bottom. | **SOURCE_VERIFIED**, not live-tested for arbitrary composite types in this project. |
| Basic Column / profile | `CreateColumns` may specify `buildingMaterialId` **or** `profileId`, plus width/depth/height, floor index; `GetDetailsOfElements` returns `buildingMaterialId` or `profileId`. | Read `type=Column`, `origin`, dimensions, cross-section subtype, `floorIndex`, bbox. Complex profiles may not obey basic width/depth semantics. | **SOURCE_VERIFIED + LIVE user test 4 Basic columns**. Profile creation/shape readback **NOT_VERIFIED**. |
| Profile catalog | `GetProfiles(attributeIds, fields)` can return `useWith, width, height, minimumWidth, minimumHeight, widthStretchable, heightStretchable, hasCoreSkin, skins, skinOutlines, profileModifiers`. | Resolve profile GUID, target useWith and dimensions. **Raw editable 2D vector geometry not exposed** by this command per schema; do not imply full native Profile Editor equivalence. | **SOURCE_VERIFIED (schema only)**, no full installed live proof. |
| Surfaces / overrides | `GetSurfaces` and `GetBuildingMaterials` separate Surface attributes from Building Materials; Wall/Slab/Column readbacks may expose overrides. | Preserve `overridden` flags and distinguish the BM's default surface from any explicit face override; material identity alone does not certify every visible rendered face. | **SOURCE_VERIFIED (schema)**; per-face IDs on all created elements **NOT_VERIFIED**. |
| Hosted openings | `GetDetailsOfElements` returns `ownerElementId` for Window/Door along with width/height/sill/offset. | Read back exact parent wall GUID and dimensions; reject missing/wrong host, even if bounding box looks plausible. | **SOURCE_VERIFIED + LIVE user test PASS** for 2 Windows and 1 Door. |
| Hierarchical subelements | `GetSubelementsOfHierarchicalElements`, `Get3DBoundingBoxes`; some ColumnSegment responses have inverted `1e35/-1e35`. | When 3D bbox invalid, only resolve a *uniquely verified parent* with valid 3D bbox, never silently discard unknown volumetric geometry. | **LIVE user test on 4 ColumnSegments** with parent bbox; general coverage not proved. |

**Coordinates/levels:** `CreateWalls.floorIndex` is native API index and shifts `zCoordinate` interpretation to a floor-relative bottomOffset when supplied (per schema). Slab `level` and `floorIndex` are separate inputs and must be checked against actual `GetStories`, `GetDetailsOfElements`, and bbox. Prohibit guessed "story zero is nonexistent": the API index can be 0 while the **human first floor** is named "Первый Этаж".

## 3. High-value upstream source change: CreateSlabs fields

Upstream [ENZYME-APD Tapir PR #785](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785) was **OPEN / not merged** at inspection (2026-10-11; head commit from GitHub API). It extends `CreateSlabs` with `structureType=Basic|Composite`, `buildingMaterialId` for Basic, `compositeId` for Composite and reuses `ApplySlabStructure`. Diff read from GitHub: addition to `ElementCreationCommands.cpp`, helper linkage in `ExtendedElementCommands.hpp/.cpp`, and an example. The PR explains the exact semantics: for Composite, `thickness` is **ignored in favor of skins**. The author **reports** builds AC25/AC29/AC30 and one live AC29 test after linkage fix, but an accepted release/merge or parity with the currently installed user's version is **not verified**. **Do not silently replace installed APX or assert installed 1.5.10 has these fields.**

Direct upstream diff comparison confirmed:
- **Installed pinned snapshot** `CreateSlabs`: no structure/material fields.
- **PR #785** `CreateSlabs`: explicit structure/material/composite fields.
- `ModifySlabs` accepts these fields already (proven on user test).

## 4. Shortest implementation decision for APA arbitrary plan-driven modeling

**Adopt a capability-negotiated typed attribute resolver, not a hardcoded material GUID and not a compulsory Tapir upgrade:**

1. **Read-only discovery** bound to single already-open PLN: `GetProjectInfo`, `GetStories`, `GetAddOnVersion`, list of required attributes and surface/profile/composite details. Capture a project-local typed catalog with GUIDs, `useWith`, basic/composite semantics, profile dimensions, and consistency fingerprints. Avoid mutating project defaults.
2. **Typed intent**: for each planned slab require either `Basic {buildingMaterialGuid, thickness>0}` or `Composite {compositeGuid, derivedThicknessFromSkins}`; never mix IDs; require explicit story API index/level, bounded polygon, reference plane, owner and bounds. For ambiguous material names, return BLOCKED with candidates, not a guessed first attribute.
3. **Capability branching**: if runtime **proves** `CreateSlabs` supports type/material fields, use direct typed Create with native readback. Otherwise in local 1.5.10, allow only a *validated* Basic Favorite/create path or a **separately explicitly authorized** one-shot Create→typed readback→Modify on exactly the created GUID. Because writes can have ambiguous effects, each intent and GUID must be durable in a journal **before/after** native mutation; no replay/auto-save/automatic retry. For ambiguous/failing readback, stop, reconcile by GUID and project. Do not use the old v1.3 menu 5 again.
4. **After each write**: verify type, home story API index, physical bbox, precise geometry dimensions, structure/material/composite ID, surface overrides, parent GUID where applicable. Complex profiles require extra geometric verification since GetProfiles does not expose entire raw shape.
5. **Staged rollout**: geometry+materials+stories first. Before universal automatic placement, measure actual GUID coverage and missing commands/elements on diverse **expendable** PLNs and establish rollback/recovery by isolated journal. No claim of arbitrary model support until tests pass.

**Preferred near-term choice:** existing working Tapir 1.5.10 with validated typed plan/readback and isolated single-element experiments; monitor PR #785 as optional future direct-create capability. No need to spend time rewriting Tapir into an entirely separate new add-on for this gate.

## 5. Audit decisions / remaining gaps

**Done at research-source level:** normalized matrix of story/material/composite/profile/surface/host commands; rigorous Basic vs Composite slab rule; PR #785 source-diff and deployment boundary; real saved-copy slab failure and repair, floor identity and door/window ownership evidence.

**NOT_VERIFIED:** byte parity of pinned `tapir-scene-live.json` to installed 1.5.10 APX; actual complete local AC29 SDK headers + compile of specific PR #785 in owner's environment; installed profile and surface detailed live capture beyond the tested sample; all 3D body material faces; composite skin-sum live tests across several real PLN; generalized parametric geometry and planner quality; any timing/speedup number.

**User data/privacy policy:** actual private `.pln` bytes and source JSON with absolute local paths were NOT uploaded or written into the GitHub repository by this research. All GitHub modifications restricted to research docs.

## 6. Next task proposal (pending independent acceptance)

Propose under `APA-P30.A02` a distinct substep **"Capability-negotiated typed slab creation and recovery adapter"** linked to `APA-P10.A01.S02` and `APA-P10.A02.S01`. The next step should deliver a plan/schema adapter plus offline negative tests and one separate owner-authorized test on an expendable PLN; explicitly reject mixed buildingMaterialId/compositeId, Composite thickness override, missing material GUID, ambiguous concurrent/create outcome. If it overlaps existing generic `APA-P30.A02.S01`, the independent auditor should re-scope/reject rather than duplicating work.


## 7. Deduplication against earlier P10.A01.S02 source audit

Previous [P10.A01.S02 profile/edge material source audit](../2026-10-10/apa-technical-20261010-153928-profile-fields-edge-material-8c21.md) independently identified **GetProfiles `skinOutlines` filtering bug** in public Tapir 1.5.9/1.7.0 code: requesting only `fields=["skinOutlines"]` may omit the result; a conservative client may request `fields=["skins","skinOutlines"]` or omit `fields`. It also identified per-edge material distinct from the skin's building material, and missing composite nComps fidelity in source. That work was SOURCE/SYNTHETIC only; installed 1.5.10 LIVE still NOT_VERIFIED.

**No duplicate task requested:** this new report contributes *verified one-off AC29 live saved-copy attributes and observed Basic/Composite thickness failure*, plus upstream PR #785 actual schema/API diff and a parametric adapter decision. The earlier report remains canonical for profile/edge field limitations. A future full-model attribute resolver must integrate **both** sources rather than silently claiming that the simple metadata matrix above covers complete profile geometry or material override fidelity.
