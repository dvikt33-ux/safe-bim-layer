# ARENA RECONCILIATION — GPT counter-audit of the Arena full-system audit

Date: 2026-09-28
Author: ARENA (agent-handoff turn 69 → 70)
Branch: `audit/arena-reconciliation-gpt-counter-audit-20260928` (parent `59239ce`, GPT counter-audit branch)
Inputs read: `GPT_COUNTER_AUDIT_ARENA_20260928.md`, `ARENA_TASK_RECONCILE_GPT_COUNTER_AUDIT_20260928.md`, the six Arena reports under `audit/arena-full-system-audit-20260928/` and the root `ARENA_*_20260928.md` files, Tapir sources at git tag `1.5.9` (`d0dbb11`) and at `b1dc828`, official Archicad 29 API reference (graphisoft.github.io/archicad-api-devkit), GOST 2.307-2011 and GOST R 21.101-2020 clause texts.

Evidence grades used throughout: `LIVE_CONFIRMED` (only from committed live evidence in this repo — Arena ran NO Archicad session), `STATIC_CONFIRMED` (exact source/schema/official documentation), `INFERRED` (reasoned from sources, not proven), `UNRESOLVED_LIVE_REQUIRED`, `CONTRADICTED`.

Scope discipline: this is a targeted reconciliation, not a repeat of the audit. Only the nine disputed points, Arena's own corrections that fell out of re-checking them, the publication-integrity issue, and the consolidated verdict/live-gate table are covered.

---

## 0. Method and cycle log

`AUDIT → targeted PASSES → AUDIT → targeted PASSES → FINAL AUDIT`

| Step | What was done | Result |
|---|---|---|
| AUDIT 1 | Re-read GPT's nine points against Arena's original wording (`ARENA_FULL_SYSTEM_AUDIT_20260928.md` lines 48, 114, 166, 351, 357, 367, 420–440). | 2 Arena statements are plainly wrong as written (GOST "policy", `GetElementsByType` composite filter); 1 Arena grade is too strong (rollback = STATIC); 6 points are architecture-precision disputes. |
| PASS 1 (Tapir source) | Extracted `GetElementsByType`, `FilterElements`, `GetDetailsOfElements` (`fields`, `ElementDetailsField`), `MorphBody`, `CreateMorphs/ModifyMorphs`, `CreateAssociativeDimensions`, `GetDimensionData`, Favorites, Library, Project/Hotlink, Classification/Grouping/IFC/Design-Option/Issue/Property command schemas from `docs/archicad-addon/command_definitions.js` + `CommonSchemaDefinitions.json` at tag 1.5.9; read `ElementCommands.cpp` GetDetails switch (Wall/Slab/Roof composite emission, Shell → "Not yet supported"). | Findings in §2.1, §2.2, §2.3, §2.5, §2.9. |
| PASS 2 (official API) | `ACAPI_CallUndoableCommand` reference page (return codes, remarks); Graphisoft Community thread on undoable command cancellation; `Modeler::MeshBody::IsClosedBody` semantics as cited by Tapir's own schema text. | Rollback-on-error is NOT stated in the official reference; only exception-abort → revert is attested (§2.6, §3.3). |
| PASS 3 (normative text) | GOST 2.307-2011 §5.10/5.11/5.12 and GOST R 21.101-2020 §5.4.2 clause text (two independent transcriptions each). | §2.1. |
| AUDIT 2 | Re-checked every reconciled architecture for hidden live claims and for fail-closed regressions. | Found none introduced; found one Arena over-grade (rollback) and downgraded it. Opened one new source question: Shell composite readback → closed in PASS 4. |
| PASS 4 | `GetDetailsOfElements` default branch for Shell; `GetLibraries/AddLibraries/SetLibraries/GetAvailableLibraryParts` existence; `GetRelationsOfElements`/`GetConnectedElements` for dependency capture. | Shell composite usage unreadable in stock 1.5.9 → fail-closed rule (§2.2). Library auto-attach is stock (§2.5). Relations capture partially stock (§2.3). |
| FINAL AUDIT | Every remaining unknown expressed as an executable live test with pass/fail criteria (§5). No open static/source/design question remains for the nine points. | Done. |

---

## 1. Publication integrity — inventory text drift (must be known to GPT)

`audit/arena-full-system-audit-20260928/TAPIR_1.5.9_COMMAND_INVENTORY.md` is a *generated* file (header says so; source = `command_definitions.js` at tag 1.5.9). GPT re-created the Arena branch through the GitHub contents API (remote `181ca75`, local original `d90341c`). Five of the six published files are byte-identical. The inventory differs in five description rows; the remote wording does **not** exist in Tapir 1.5.9 or in `b1dc828` (`git grep` in both trees: 0 hits for the remote wording, 2 hits each for the local wording).

| Command | Remote (181ca75) wording — NOT in Tapir | Exact Tapir 1.5.9 wording (d90341c, restored here) |
|---|---|---|
| `ReleaseElements` | Releases the given elements in Teamwork mode. | Releases elements in Teamwork mode. |
| `GetElementsAttachedToIssue` | Retrieves attached elements to the specified issue, filtered by attachment type. | Retrieves attached elements of the specified issue, filtered by attachment type. |
| `ImportIssuesFromBCF` | Imports issues from a BCF file. | Imports issues from the specified BCF file. |
| `DeleteKeynoteFolders` | Deletes keynote folders including their content. Available from Archicad 28. | Deletes the given keynote folders including their content. Available from Archicad 28. |
| `DeleteKeynoteItems` | Deletes keynote items. Available from Archicad 28. | Deletes the given keynote items. Available from Archicad 28. |

Action taken on this branch: the file is restored to the exact generated content (SHA-256 `4192ce118be6095572183db8496e8c0f93bd303f5dac27cd795b8706857502d0`, identical to `d90341c`; the remote variant was `5b60526f…686b`). No other published file was touched. Nothing is deleted: the drifted wording is preserved in the table above. Process rule going forward: publish Arena artifacts from the bundle/patch (byte-exact), never by retyping; every generated file carries its SHA-256 in the handoff note.

---

## 2. The nine disputed points

### 2.1 GOST dimension spacing — normative minima vs policy

**GPT claim.** Arena was wrong to label dimension placement offsets as "policy, not normative". GOST 2.307-2011 §5.11 (7 mm / 10 mm minima), §5.12 (avoid crossings) and GOST R 21.101-2020 §5.4.2 (2–4 mm 45° ticks, 0–3 mm overrun) are normative and belong in `normative_ref`.

**Arena's original wording** (`ARENA_FULL_SYSTEM_AUDIT_20260928.md` line 351): "placement offsets are policy, not normative".

**Exact evidence (normative text).**
- GOST 2.307-2011 §5.11: «Минимальные расстояния между параллельными размерными линиями должны быть 7 мм, а между размерной и линией контура — 10 мм и выбраны в зависимости от размеров изображения и насыщенности чертежа.» — «должны быть» = mandatory minima; the second half makes the *actual* value above the minimum a design choice.
- GOST 2.307-2011 §5.12: «Необходимо избегать пересечения размерных и выносных линий.» — mandatory avoidance requirement (not a hard prohibition; SPDS practice tolerates some crossings on construction drawings — clause for that tolerance not verified here, see UNRESOLVED_SOURCE below).
- GOST 2.307-2011 §5.10: «Выносные линии должны выходить за концы стрелок размерной линии на 1—5 мм.»
- GOST R 21.101-2020 §5.4.2: «Размерную линию на ее пересечении с выносными линиями, линиями контура или осевыми линиями ограничивают засечками длиной 2–4 мм, наносимыми с наклоном вправо под углом 45° к размерной линии, при этом размерные линии продолжают за крайние выносные линии, линии контура или осевые линии на 0–3 мм.»
- Values such as 14–21 mm for the first chain on general views, and axis-bubble distance 4 mm, appear only in teaching/secondary sources in this pass → INFERRED, must not be encoded as normative without the clause.

**Verdict: ACCEPT (Arena statement CONTRADICTED and withdrawn).**

**Reconciled architecture.**
1. `Rule.normative_ref` (mandatory, audit grade FAIL when violated): `GOST 2.307-2011 §5.11` ≥ 10 mm contour→first dimension line, ≥ 7 mm between parallel dimension lines; `§5.12` no dimension/extension crossings (severity WARN on construction drawings until the SPDS tolerance clause is cited); `§5.10` extension-line overrun 1–5 mm; `GOST R 21.101-2020 §5.4.2` tick 2–4 mm at 45° right-slanted, dimension-line overrun 0–3 mm (precedence: SPDS over ЕСКД for construction drawings where they differ).
2. `Rule.policy` (office/project, audit grade INFO/WARN): actual offsets above minima (e.g. 12/8 mm), chain order (openings → axes → overall), staggered text, first-chain distance presets per view type.
3. Units: rules are stored in **paper millimetres**; conversion `offset_model_m = mm × scale_denominator / 1000` (1:100 → 10 mm = 1.00 m, 7 mm = 0.70 m; 1:50 → 0.50 m / 0.35 m). Scale comes from the view/drawing settings readback (`GetViewSettings`/layout drawing scale), never assumed.
4. Tapir 1.5.9 mapping (STATIC_CONFIRMED): `CreateAssociativeDimensions` takes only `referencePoint` (a point on the dimension line), `direction`, `witnessPoints`, `floorIndex`; it has **no** marker/tick/text/font input and no `favoriteName`. Marker style therefore comes from the Dimension tool defaults → Safe BIM applies a Safe-BIM-owned Dimension favorite with `ApplyFavoritesToElementDefaults` (Favorites Commands, 1.5.9) immediately before creation, in the same job. Placement minima are computed by Safe BIM (contour polygons from `GetDetailsOfElements` `floorPlanPolygons` + scale) and passed as `referencePoint`.
5. Audit side: `GetDimensionData` returns `referencePoint`/`direction`/witness points → §5.11 distances are auditable geometrically. Tick length/angle and dimension-line overrun are **NOT readable** through any 1.5.9 command → `NOT_AUDITABLE` (small Tapir PR "dimension marker readback" = P2-23).

**Remaining live test.** GPT-LT-08 (= Arena LT-H2 new): on the sandbox at 1:100 and 1:50, apply the Dimension favorite to defaults, create one chain at the computed offset, read back with `GetDimensionData`, verify offsets ≥ 10/7 mm on paper; marker style verified by human screenshot only (until P2-23).

**UNRESOLVED_SOURCE (low impact):** exact GOST R 21.101-2020 clause that tolerates crossings on construction drawings — until cited, §5.12 stays WARN not FAIL for SPDS views.

---

### 2.2 Composite "in use" detection

**GPT claim.** `GetElementsByType` cannot filter by `compositeId`; its filters are fixed context flags. A stock implementation must enumerate element types and inspect minimal `GetDetailsOfElements` fields, or add a dedicated attribute-usage wrapper.

**Arena's original wording** (line 367): "check `GetElementsByType` filter by `compositeId` first".

**Exact evidence (STATIC_CONFIRMED, tag 1.5.9).**
- `GetElementsByType.inputScheme = {elementType, filters: [ElementFilter], databases}`; `ElementFilter` enum = `IsEditable, IsVisibleByLayer, IsVisibleByRenovation, IsVisibleByStructureDisplay, IsVisibleIn3D, OnActualFloor, OnActualLayout, InMyWorkspace, IsIndependent, InCroppedView, HasAccessRight, IsOverriddenByRenovation, IncludeSubElemObjects`. `FilterElements` uses the same enum. No attribute predicate exists → Arena's check is impossible as written.
- `GetDetailsOfElements.fields` (optional, `ElementDetailsField` enum = `type, id, floorIndex, layerIndex, drawIndex, details, floorPlanPolygons, hotlinkId`; `ElementCommands.cpp` 849–852 `isFieldRequested`) — requesting `["details"]` skips the expensive `floorPlanPolygons` branch.
- `details` emits `structureType` and, for composite structures, `compositeId` for **Wall** (`elem.wall.composite`), **Slab** (`elem.slab.composite`) and **Roof** (`base.composite`) (`ElementCommands.cpp` GetDetails switch, Wall/Slab/Roof cases). **Shell** is not a case → falls to `default:` → `details: {"error": "Not yet supported element type"}` (lines 1508–1510). Curtain-wall/other types cannot carry a composite.

**Verdict: ACCEPT (Arena implementation REJECTED and replaced; goal unchanged).**

**Reconciled architecture — stock algorithm `CompositeUsageIndex` (pure Tapir 1.5.9, ≤ 3 + Σ⌈N_t/200⌉ calls):**
```
for t in [Wall, Slab, Roof]:
    ids_t = GetElementsByType(elementType=t)              # no filters = no restriction (hidden/locked/hotlinked included)
    for chunk in chunks(ids_t, 200):
        det = GetDetailsOfElements(elements=chunk, fields=["details"])
        for e in det: if e.details.structureType == "Composite": index[e.details.compositeId.guid].add(e.elementId)
shells = GetElementsByType(elementType=Shell)
usage(compositeGuid) = {users: index.get(compositeGuid, ∅), unknown: len(shells) > 0}
```
Overwrite/`DeleteAttributes` of a Composite is refused when `users ≠ ∅` **or** `unknown == true` (a Shell can carry a composite and its readback is unsupported → fail-closed, exactly the rule the user demanded). The snapshot is per job (P2-18 verdict), invalidated by any write in the same job. Elements inside hotlink instances count as users (they are listed; `hotlinkId` available) — a composite used only by a hotlink is still in use.
Wrapper (optional, P2): Tapir command `GetAttributeUsers{attributeType, attributeIds}` doing the same enumeration server-side (`ACAPI_Element_GetElemList` + `ACAPI_Element_Get` per type, including Shell) — justified only if live timing of the stock scan is unacceptable.

**Remaining live test.** GPT-LT-06 (CompositeBuilder): create composite → create wall using it → `usage()` must list the wall → overwrite refused; delete wall → `usage()` empty → overwrite allowed; timing of the scan on the sandbox recorded.

---

### 2.3 Permanent Morph delete/recreate policy

**GPT claim.** Automatic delete+`CreateMorphs`+relink is safe only for Safe-BIM-owned temporary/operator Morphs; permanent Morph body replacement stays fail-closed until dependency capture/replay is complete or an in-place fix is live-proven. A lineage record alone does not prove preservation.

**Arena's original wording** (lines 170–172, 401, 420): delete+create+relink "now" with a `guid_lineage` record; planner refuses `ModifyMorphs(body)` for `lifecycle=final`.

**Exact evidence — what a GUID replacement loses or must rebind (Tapir 1.5.9 command groups, STATIC_CONFIRMED existence; behaviour of Archicad on the *old* GUID's dependents is INFERRED unless noted):**

| Relation class | Capture (1.5.9) | Replay (1.5.9) | Status on GUID replacement |
|---|---|---|---|
| SEO links where Morph is operator **or target** | `GetSolidElementLinks` (+ `GetElementTrims`) | `CreateSolidElementLinks` (+ `TrimElements`) | Lost; replayable only if *both* ends still exist; links where the Morph is target of other operators are easy to forget → must be captured by scanning all links, not only the Morph's own |
| User-defined properties | `GetPropertyValuesOfElements` | `SetPropertyValuesOfElements` | Replayable (built-in/read-only properties are not) |
| Classifications | `GetClassificationsOfElements` | `SetClassificationsOfElements` | Replayable |
| Groups | `GetGroupsOfElements` / `GetElementsOfGroups` | `CreateGroups` | Replayable but the *group* GUID changes → transitive lineage |
| Design Option membership | `GetDesignOptionForElements` | `MoveElementsToDesignOptions` | Replayable |
| Issue attachments (BCF) | `GetElementsAttachedToIssue` | `AttachElementsToIssue` | Replayable |
| IFC GlobalId / IFC properties | `GetIFCIdsOfElements`, `GetIFCPropertiesOfElements` | **no setter in Tapir 1.5.9** | **Lost** — any IFC-coordinated model makes replacement non-reversible |
| Associative dimensions/labels whose witness points reference the Morph | `GetDimensionData` (`witnessPoints.elementId`) | re-create dimension | Association lost (INFERRED: Archicad converts/removes the witness point when the element is deleted); label owner link lost |
| Hotlink membership | `hotlinkId` field | — | Element inside a hotlink cannot be deleted/recreated in place at all (BADPARS class) → always STOP |
| Teamwork ownership/reservation | `ReserveElements`/`ReleaseElements` | — | New element owned by the acting user; foreign reservations on the old GUID → STOP |
| Layer / story / renovation / element ID string | `GetDetailsOfElements` | `SetDetailsOfElements`, `CreateMorphs` inputs | Replayable (layer via SetDetails, since `CreateMorphs` has no `layerIndex`) |
| External references (BIMx, schedules by GUID, third-party DBs, saved views' selections) | none | none | **Undetectable** from Tapir |

**Verdict: ACCEPT with MODIFY of the criterion.** The split is not "temporary vs permanent" by label but **"Safe-BIM-owned and dependency-closed" vs everything else**:
- **Class A (automatic delete/recreate allowed):** element created by Safe BIM in this or an earlier job (ownership recorded in receipts and in a Safe-BIM property/ID prefix), AND dependency capture finds only classes in the replayable set above, AND no IFC export/coordination flag on the project, AND no hotlink/teamwork foreign ownership. Covers temporary Morphs, SEO operators/helpers, disposable test geometry.
- **Class B (everything else, including all user-authored Morphs):** result `STOP_NEEDS_SAFE_MORPH_REWRITE`; GUID replacement only with explicit user approval **per element**, after presenting the captured dependency list with the non-replayable classes highlighted (IFC GlobalId, associative dimensions/labels, external references).
- `ModifyMorphs(body)` stays disabled for both classes until LT-B1/LT-B2 settle the `isClosed`/`bodyType` semantics; `ACAPI_Element_ChangeMorphEdgeType` (P1-6) fixes edge *display* only and does not change this policy.
- The `guid_lineage` record stays mandatory but is downgraded from "proof of preservation" to "audit trail + replay input".

**Remaining live tests.** LT-B1, LT-B2 (unchanged); GPT-LT-05 (lineage/relink on Class A); **new LT-B4**: on a disposable Morph attach one property value, one classification, one associative dimension and one SEO link (as target); delete/recreate; observe which survive/rebind; result fixes the INFERRED rows above.

---

### 2.4 SEO verifier status

**GPT claim.** `GetCollisions` and built-in Volume are candidate verifiers, not confirmed; SEO-evaluated semantics are `UNRESOLVED_LIVE_REQUIRED` until LT-C1/LT-C2; results stay `LINK_ONLY` before that.

**Check whether Arena promoted them.** Arena's Domain F ladder (audit §F, lines 280–303) lists rungs 3 (`GetCollisions`) and 4 (built-in quantities) as `STATIC_CONFIRMED` *existence* and gates their use on LT-C1/LT-C2; the live-test plan's phrase "`GetCollisions` is a valid functional closedness test (LIVE_CONFIRMED)" (`ARENA_LIVE_TEST_PLAN_20260928.md` line 53) is written as the **interpretation branch of a not-yet-run test**, not as a finding. So Arena did not claim live proof — but the ladder table lacked an explicit status column, which allowed the reading GPT warned about.

**Evidence re-check (official API):** `ACAPI_Element_GetCollisions` documentation defines collision by intersection body volume/surface tolerance and says nothing about SEO-evaluated geometry; `ACAPI_Element_GetQuantities` documentation lists surface/volume/… per type and says nothing about SEO nets. Both remain `UNRESOLVED_LIVE_REQUIRED` for the SEO case.

**Verdict: ACCEPT (tightening, no substantive disagreement).**

**Reconciled architecture.** Verification ladder with explicit status:

| Rung | Method | Status today | Promotes SEO result to |
|---|---|---|---|
| 1 | typed readback (`GetSolidElementLinks`, `GetElementTrims`, `GetDetailsOfElements`) | STATIC_CONFIRMED usable | `LINK_ONLY` |
| 2 | analytic AABB / interval reasoning in Safe BIM | Safe BIM math, unit-tested | `LINK_ONLY` (+ geometric plausibility) |
| 3 | `GetCollisions` | CANDIDATE — gate LT-C1 | `EVALUATED_EFFECT` only after LT-C1 passes |
| 4 | built-in quantities (Volume via properties) | CANDIDATE — gate LT-C2 | `EVALUATED_EFFECT` only after LT-C2 passes |
| 5 | `EvaluateElements3D` (Tapir PR, ModelAccess) | post-PR, post-rungs-3/4 measurement | `EVALUATED_EFFECT` |
| 6 | visible 3D / human | — | human confirmation |

Rule: `seo_status ∈ {LINK_ONLY, EVALUATED_EFFECT, FAILED}`; the planner may never emit `EVALUATED_EFFECT` unless the verifier used has a passed live gate recorded in the capability registry (P2-17/P0). If LT-C1 and LT-C2 both fail, rung 5 becomes the first evaluated verifier and SEO stays `LINK_ONLY` until that PR is live-tested.

**Remaining live tests.** LT-C1 (= GPT-LT-01 collision half), LT-C2 (= GPT-LT-01 quantity half) — unchanged, first in the live order after identity.

---

### 2.5 Shared asset architecture

**GPT claim.** `.mod` + Hotlink complements a linked shared library, does not replace it; three stores (linked library for GSM, module repository for native assemblies, Favorites/template pack); a GSM writer is still needed for true reusable parametric objects. User requirement: add an asset once, available in later projects.

**Arena's original wording** (P1-16): "`.mod` + hotlink for assemblies (stock); GSM deferred".

**Exact evidence (STATIC_CONFIRMED, tag 1.5.9).** Library Commands: `GetLibraries`, `ReloadLibraries`, `AddFilesToEmbeddedLibrary`, `SetLibraries` ("Makes the given folders the project's local libraries; … Set the libraries before opening a file that needs them and the missing-library dialog does not appear."), `AddLibraries` (absolute local folder/container paths), `GetAvailableLibraryParts` (guid/index/documentName/fileName/typeId; `skippedCount` signals partial inventory). Project Commands: `SaveAsModuleFile` (absolute `.mod` path; "The current window must be a floor plan, section, elevation or detail"), `GetHotlinks`, `CreateHotlinkNodes` (dedupes by source path, `existing:true`), `CreateHotlinkInstances` (nodes created via API placeable from AC26+), `ChangeHotlinkInstances`. Favorites Commands: `ExportFavorites` (`.prefs` file or folder), `ImportFavorites` (path, `targetFolder`, `importFolders`), `ApplyFavoritesToElementDefaults`, `CreateFavoritesFromElements`, `UpdateFavoritesFromElements`, `RenameFavorites`, `DeleteFavorites`.

**Verdict: ACCEPT.** Arena's P1-16 wording collapsed two stores into one; GPT's three-store split is correct and fully stock-supported for attach/list/place; only the GSM *authoring* step is missing.

**Reconciled architecture — `AssetResolver` with three stores, all satisfying "add once, reuse later":**
1. **Shared linked library** (folder path, e.g. `…\SafeBIM_Library\`): GSM/library parts. Per project: `GetLibraries` → if absent `AddLibraries` (or `SetLibraries` before `OpenProject`) → `ReloadLibraries` → `GetAvailableLibraryParts` must list the part (`skippedCount == 0` else `PARTIAL_INVENTORY`). Authoring of new GSM = deferred P2 (GDL source → `LP_XMLConverter`, a stock Graphisoft tool; INFERRED path, no live evidence); until then only pre-existing GSM are managed.
2. **Module repository** (folder of `.mod`): native BIM assemblies. Authoring: `SaveAsModuleFile(moduleFilePath, elements)` from a floor-plan window; reuse: `CreateHotlinkNodes` (idempotent by path) → `CreateHotlinkInstances(origin, rotationAngle, …)`; update path via `ChangeHotlinkInstances`. Constituents keep native semantics inside the hotlink but are **not editable in place** (hotlink membership → BADPARS class; see §2.3).
3. **Favorites/template pack**: `ExportFavorites` from the Safe-BIM sandbox to `SafeBIM_Favorites.prefs`; `ImportFavorites` into every new project (or bake into a `.tpl` template so import is unnecessary). Carries the GOST dimension/text/label recipes (§2.1, §2.9).
Template-first rule: the sandbox/template contains all three attachments so that a project created from it needs zero setup; the resolver still verifies presence at job start (fail-closed `ASSET_MISSING`).

**Remaining live tests.** GPT-LT-10 (library across two disposable projects: `AddLibraries` → `GetAvailableLibraryParts` lists the same GSM), GPT-LT-11 (`.mod` round-trip incl. `existing:true` dedupe and instance placement), LT-J1 merged into these two.

---

### 2.6 `atomic:true` response contract

**GPT claim.** Response must be rollback-aware: GUIDs produced earlier in the loop must not be exposed as durable if the undoable lambda returns an error; the command must mark them rolled back/clear them and Safe BIM must verify absence.

**Arena's original wording** (line 48, 114): TrimElements "returns the real error from the lambda → rollback" (graded STATIC_CONFIRMED); atomic flag: "on the first item error, return that error from the lambda (rollback) and report `executionResults` for all".

**Exact evidence.**
- Official `ACAPI_CallUndoableCommand` reference: return codes `NoError`, `APIERR_UNDOEMPTY`, `APIERR_REFUSEDCMD`, `APIERR_COMMANDFAILED` ("The current command threw an exception"), `APIERR_NOTMINE`; remarks describe the scope as a database transaction. **The page does not state that returning an error from the lambda discards the changes.**
- Graphisoft Community thread "ACAPI_CallUndoableCommand() gets cancelled" (Graphisoft staff): elements vanish "as if Undo" when a command inside throws an exception — attests revert for the *exception* path only.
- Tapir 1.5.9 sources: no comment or test asserting rollback on error return (`grep -i "roll\|revert"` → 0 relevant hits).
→ **Rollback on error return is INFERRED, not STATIC_CONFIRMED.** Arena's grade is corrected (§3.3).

**Verdict: ACCEPT, plus Arena self-correction.**

**Reconciled contract (Tapir PR, shared create/modify executors):**
```
request:  { ..., "atomic": true }
response: {
  "atomic": true,
  "committed": bool,               // lambda returned NoError
  "rolledBack": bool,              // !committed
  "rollbackVerified": bool,        // after the undo scope closed, ACAPI_Element_GetHeader on every loop GUID → all BADID/DELETED
  "failedIndex": int|null,         // first failing input item
  "executionResults": [ ... ],     // aligned with input; success items of a rolled-back batch are reported as
                                   // {"success": false, "error": {"code": "ROLLED_BACK", ...}}
  "elements": [ ... ],             // EMPTY when rolledBack — never the loop GUIDs
  "rolledBackCandidates": [guid…]  // present only when rolledBack; explicitly non-durable; for absence verification only
}
```
Safe BIM rules: (a) durable receipts only from `committed == true`; (b) if `rolledBack && !rollbackVerified` → job state `PARTIAL_APPLIED_UNKNOWN`, run `GetDetailsOfElements(rolledBackCandidates)` and, for any that still exist, explicit compensating `DeleteElements` + absence re-check (existing A.4 compensation rule); (c) until the PR exists, GPT's interim rule holds: one risky write item per command, `PARTIAL_APPLIED` bookkeeping for multi-item batches; (d) no component may use the word "transaction" in a grade until LT-A3 passes.

**Remaining live tests.** LT-A2 (partial commit today, unchanged); **new LT-A3 (post-PR integration):** batch of 3 valid + 1 invalid item with `atomic:true` → expect `committed:false, rollbackVerified:true`, `GetElementsByType` count unchanged; then the same batch without `atomic` → 3 created (baseline behaviour). If `rollbackVerified:false` is ever observed, the add-on must perform explicit deletion inside a fresh undo scope and the contract gains `compensated:true`.

---

### 2.7 Slab bounds crash-test policy

**GPT claim.** Do not deliberately reproduce the #686 Slab crash in a normal test; blacklist by version + positive test on a fixed build; crash repro optional only in an isolated sacrificial session.

**Arena's original wording:** LT-F3 proposed a controlled crash reproduction as part of the live plan.

**Exact evidence (STATIC_CONFIRMED).** Post-1.5.9 diff (`b1dc828`, `ElementCommands.cpp`): "The Slab is routed here to avoid a crash… Archicad dies with a SIGSEGV instead of returning an error (#686). Deliberately no CalcBounds fallback for the Slab… CalcBounds crashes." Tag 1.5.9 still calls `ACAPI_Element_CalcBounds` for Slab from `Get3DBoundingBoxes`. Official `ACAPI_Element_CalcBounds` docs list only BADPARS/BADID/DELETED — the crash is undocumented upstream, known only from Tapir #686.

**Verdict: ACCEPT.** A crash that is source-attributed does not need reproduction to be blacklisted; reproducing it endangers the user's session and the sandbox file for no design information.

**Reconciled architecture.** Capability registry (P2-17→P0) entry `FORBIDDEN{command: Get3DBoundingBoxes, elementType: Slab, addOnVersion ≤ 1.5.9 and any build whose source lacks the #686 routing}` keyed by `GetAddOnVersion` (identity gate GPT-LT-00). Slab bounds today: analytic AABB from `GetDetailsOfElements` (`floorPlanPolygons`/polygon + thickness + level, `fields` limited). Upgrade gate: when a Tapir build carrying the #686 fix is installed, run **one** positive test in an isolated disposable session (Slab + section window active → `Get3DBoundingBoxes` returns, no crash) before removing the entry. LT-F3 is removed from the normal live sequence and re-labelled `LT-F3-ISOLATED (optional, sacrificial session only, never on the sandbox that holds other evidence)`. Unit tests assert that the planner refuses the forbidden pair.

**Remaining live test.** None required on 1.5.9. Positive test only on a fixed build.

---

### 2.8 Morph topology validator contract

**GPT claim.** Do not rely on a single Euler `V−E+F = 2(1−g)` rule as the universal solid test; disconnected shells change the characteristic; required checks are manifold-edge pairing, opposite winding, connected components, signed volume per closed component, duplicate/zero-length rejection, planarity, self-intersection; Euler is a per-component diagnostic.

**Arena's original wording** (line 166): closed orientable 2-manifold via "each undirected edge shared by exactly two polygons with opposite direction", **and** Euler check, **and** signed volume > 0, duplicates, planarity, self-intersection, volume-vs-primitive. Euler was one of seven checks, not the sole acceptance rule — GPT's premise is partly a straw man — but Arena's text did not say "per connected component", and a multi-component body would have failed the Euler line as written.

**Exact evidence (STATIC_CONFIRMED, 1.5.9 `MorphBody` schema):** `isClosed` is "READ-ONLY, Get output only … Geometrically computed (`Modeler::MeshBody::IsClosedBody`): true if every edge in the body has exactly two adjacent faces (a watertight/manifold volume)". `bodyType` "on Create/Modify … a confirmed Archicad SDK bug means it may not take effect (… always coming back Solid)". `edgeOverrides` controls display only. `ModifyMorphs.body` "discards the Morph's ENTIRE existing geometry".

**Verdict: MODIFY (accept GPT's precision; correct the premise).**

**Reconciled validator contract `MorphBodyValidator` (pure Python, unit-tested with known-good/known-bad fixtures):**
1. Lexical: vertex indices in range; each polygon ≥ 3 distinct vertices; hole loops separated as Tapir expects; no duplicate vertices within 1e-6 m; no zero-length edges; no degenerate (collinear) polygons.
2. Half-edge build: every directed edge appears at most once; **acceptance for `Solid`:** every undirected edge has exactly two incident face uses **with opposite direction** (this is `IsClosedBody` plus orientability — the strongest check that matches Archicad's own definition).
3. Connected components (via shared edges): report `componentCount`; each component checked independently; multiple components are allowed only if the caller declared `allowMultipleShells`, else `REJECT_MULTI_COMPONENT` (SEO operators must be single-shell).
4. Per component: signed volume > 0 (else the loops are reversed *once*, then re-checked); Euler characteristic `V−E+F` computed and **reported as a diagnostic** (`2` expected for a genus-0 shell; a mismatch with a passing edge test means a handle/hole, not a failure unless the caller declared `expectGenus`).
5. Face planarity within 1e-5 m (Archicad requires planar polygons per face); self-intersection: AABB pair pre-filter + exact triangle test on candidates (rejection for SEO operators, warning otherwise).
6. Optional: volume within tolerance of the requested primitive when generated from one.
Post-write comparator (unchanged): canonical vertex renumbering, polygon count equality, `isClosed == true` expected for a validated `Solid`; `bodyType` readback is **not** trusted as proof (SDK bug) — functional verification per §2.4 ladder.

**Remaining live tests.** LT-B1/LT-B2 unchanged (do `isClosed`/`bodyType` reflect the validator's verdict on W7-class bodies?).

---

### 2.9 Font architecture

**GPT claim.** Favorites suffice for deterministic creation but not for auditing arbitrary project text by family name; future `GetFonts/ResolveFontByName` is P1 for audit/portability; snapshot/readback of `fontIndex` now.

**Arena's original wording** (line 355, P1-14): favorites-based creation now; `GetFonts` PR for audit — same direction.

**Exact evidence (STATIC_CONFIRMED, 1.5.9).** `favoriteName` accepted by `CreateTexts`, `CreateLabels` (and 18 other creators); `CreateTexts` also takes `height`; `ModifyTexts`/`ModifyLabels` and `TextStyleSettableDetails` expose `fontIndex`, `height`, `penIndex`, `widthFactor`, `fixedSize` — no font family name anywhere; no font enumeration command. Favorites are exportable/importable (`.prefs`).

**Verdict: ACCEPT.**

**Reconciled architecture.** NOW: Safe-BIM-owned favorites `SB_TEXT_GOST_2_5`, `SB_TEXT_GOST_3_5`, `SB_LABEL_GOST_*`, `SB_DIM_GOST_SPDS` in the template/`.prefs` pack; creation uses `favoriteName` (+ `height` for texts); immediately after creation Safe BIM reads `fontIndex/height/penIndex` and stores the tuple as the *expected signature* for that role **within the same project session** (font indices are session/project tables — INFERRED unstable across machines, so never persisted as truth). Audit of Safe-BIM-created text = signature comparison; audit of arbitrary/legacy text by family name = `NOT_AUDITABLE` until the P1 Tapir PR `GetFonts` (index ↔ family name via the official font-manager API; exact function names to be verified in the PR) and Safe BIM `ResolveFontByName` (fail-closed `FONT_MISSING`). Missing favorite → `NOT_AUDITABLE`/`ASSET_MISSING`, never a default font.

**Remaining live test.** GPT-LT-09 (= LT-H1): create text/label from favorite, read back signature, repeat in a second project after `ImportFavorites` → same visual font, signature may differ (documents the index instability).

---

## 3. Arena self-corrections produced by this cycle

| # | Original Arena statement | Correction | Grade now |
|---|---|---|---|
| 3.1 | "placement offsets are policy, not normative" (audit line 351) | Withdrawn; §5.11/5.12/5.10 and 21.101 §5.4.2 are normative minima; policy only above minima. | CONTRADICTED → fixed (§2.1) |
| 3.2 | "check `GetElementsByType` filter by `compositeId`" (line 367) | Impossible in 1.5.9; replaced by `CompositeUsageIndex` with Shell fail-closed rule. | CONTRADICTED → fixed (§2.2) |
| 3.3 | TrimElements error return "→ rollback" graded STATIC_CONFIRMED (line 48) | Error propagation is STATIC_CONFIRMED; that Archicad discards the scope on error return is INFERRED (official reference silent; only exception path attested). | downgraded → LT-A3 |
| 3.4 | LT-F3 deliberate crash reproduction in the live plan | Removed from the normal sequence; isolated optional only; blacklist + positive test on fixed build. | policy fixed (§2.7) |
| 3.5 | Euler check stated without "per connected component" (line 166) | Validator contract rewritten with components; Euler diagnostic only. | fixed (§2.8) |
| 3.6 | P1-16 "`.mod` + hotlink … GSM deferred" read as one store | Three stores; GSM library remains a required, stock-attachable subsystem (`AddLibraries/SetLibraries/GetAvailableLibraryParts`). | fixed (§2.5) |
| 3.7 | Verification ladder without a status column | Explicit CANDIDATE/gate column; `EVALUATED_EFFECT` only with a passed gate in the registry. | fixed (§2.4) |

No live claim was added anywhere in this document.

---

## 4. Consolidated verdict table (all P0/P1/P2 items, reconciled) and live gates

| Item | Arena audit verdict | GPT counter-verdict | **Reconciled (this cycle)** | Live gate remaining |
|---|---|---|---|---|
| P0-1 `ModifyMorphs(body)` closedness | MODIFY: delete+create+relink + lineage | MODIFY: recreate only for temp/operator | **MODIFY: recreate only for Class A (Safe-BIM-owned ∧ dependency-closed); Class B = STOP + per-element approval; `ModifyMorphs(body)` disabled** (§2.3) | LT-B1, LT-B2, LT-B4, GPT-LT-05 |
| P0-2 `rotationDegreesZ` | ACCEPT+: forbidden param | ACCEPT | **ACCEPT** (unchanged) | none |
| P0-3 SEO evaluated proof | MODIFY: stock rungs first | MODIFY: experimental until LT-C1/C2 | **ACCEPT tightened: ladder with status column; `LINK_ONLY` until a gate passes** (§2.4) | LT-C1, LT-C2 (GPT-LT-01) |
| P0-4 partial batch writes | MODIFY: Tapir `atomic` flag | MODIFY: rollback-aware results | **ACCEPT: exact contract §2.6; rollback INFERRED until LT-A3; interim one-risky-item rule** | LT-A2, LT-A3 (post-PR) |
| P0-5 evidence integrity | MODIFY: raw + SHA-256 manifest | ACCEPT | **ACCEPT + publication rule: byte-exact bundles, SHA-256 in handoff (§1)** | — |
| P1-6 Morph edge type | MODIFY: `ChangeMorphEdgeType` all-edges | ACCEPT | **ACCEPT** (display only; no effect on P0-1 policy) | LT-B3 |
| P1-7 polygonal Opening | ACCEPT+ | ACCEPT + live gate | **ACCEPT** | LT-C4 |
| P1-8 destructive Morph boolean | ACCEPT (lifecycle) | ACCEPT | **ACCEPT; Class A/B rule of §2.3 applies to its GUID replacement** | LT-C5 (post-PR) |
| P1-9 native Shell | ACCEPT | ACCEPT | **ACCEPT** (+ note: Shell composite readback missing in 1.5.9 → §2.2 fail-closed) | post-PR |
| P1-10 per-edge Roof | ACCEPT | ACCEPT | **ACCEPT** | post-PR |
| P1-11 section dimension existence | ACCEPT | ACCEPT+ | **ACCEPT+** (`GetElementsByType(databases=[…])` + `GetDimensionData`) | LT-E3 (GPT-LT-03) |
| P1-12 background DB execution | MODIFY: DB param on executors | MODIFY: only proven-safe pairs | **MODIFY: DB param only for command/type pairs with a passed live gate; no generic runner** | LT-E1, LT-E2 (GPT-LT-02) |
| P1-13 `EvaluateElements3D` | ACCEPT after stock rungs | ACCEPT | **ACCEPT** (rung 5) | after LT-C1/C2 |
| P1-14 font by name | MODIFY: favorites now, `GetFonts` PR | MODIFY | **ACCEPT §2.9: favorites + session signature now; `GetFonts` P1 for audit** | LT-H1 (GPT-LT-09) |
| P1-15 GOST engine | ACCEPT (architecture) | ACCEPT with correction | **ACCEPT with correction §2.1: minima normative; paper-mm rules × scale; Dimension favorite via `ApplyFavoritesToElementDefaults`; marker style NOT_AUDITABLE (P2-23)** | GPT-LT-08 |
| P1-16 shared library | MODIFY: `.mod`+hotlink, GSM deferred | MODIFY: three stores | **ACCEPT three stores §2.5; all attach/list/place steps stock; GSM authoring P2** | GPT-LT-10, GPT-LT-11 |
| P2-17 capability negotiation | ACCEPT → P0 | ACCEPT → P0 | **P0** (version gate + allowlist + forbidden pairs incl. §2.7 entry + live-gate registry used by §2.4) | GPT-LT-00 |
| P2-18 caches | MODIFY: per-job snapshot | ACCEPT v1 | **ACCEPT** (also governs `CompositeUsageIndex` §2.2) | — |
| P2-19 context grouping | ACCEPT | ACCEPT | **ACCEPT** | LT-E1 |
| P2-20 transactions/round-trips | MODIFY: atomic + batched readback | MODIFY: no "transaction" claim | **MODIFY: as P0-4; word "transaction" forbidden in grades until LT-A3** | LT-A3, LT-G1/G3 |
| **P0-21 (new)** composite overwrite preflight | — (implied in CompositeBuilder) | REJECT implementation | **`CompositeUsageIndex` stock algorithm; Shell present → UNKNOWN → refuse** (§2.2) | GPT-LT-06 |
| **P1-22 (new)** dependency capture/replay | lineage record | required for permanent Morphs | **Capture set of §2.3 table; non-replayable classes block Class A** | LT-B4 |
| **P2-23 (new)** dimension marker readback | — | — | **Tapir PR: expose tick type/size/overrun in Dimension details so §5.4.2 becomes auditable** | post-PR |
| **P2-24 (new)** `GetAttributeUsers` wrapper | — | "future `GetAttributeUsage`" | **Only if GPT-LT-06 timing is unacceptable** | GPT-LT-06 timing |

---

## 5. Remaining unknowns — executable live tests only

Order follows GPT's sequence (identity first; Slab crash excluded). Each test lists the exact stock command path and the pass criterion; all run on the disposable sandbox (`Test_House_WriteSandbox.pln`) with raw request/response JSON + SHA-256 manifest committed (P0-5).

| Order | Test | Stock commands | Pass criterion | Resolves |
|---|---|---|---|---|
| 0 | GPT-LT-00 identity | Tapir `GetAddOnVersion` + official JSON API `GetProductInfo` | `1.5.9` exact; registry loads forbidden pair §2.7 | P2-17 |
| 1 | LT-C1 / LT-C2 (GPT-LT-01) | wall + closed cutter Morph; `GetCollisions` and Volume property before/after `CreateSolidElementLinks` (subtraction) | collision/volume change consistent with subtraction → rungs 3/4 promoted; else stay `LINK_ONLY` | P0-3 |
| 2 | LT-E1/E2 (GPT-LT-02) | create with `floorIndex` without `ChangeWindow`; readback `floorIndex` | as requested → `ensure_active_story` optional per pair | P1-12 |
| 3 | LT-E3 (GPT-LT-03) | section DB current → `CreateAssociativeDimensionsOnSection` → `GetElementsByType(Dimension, databases=[sectionDb])` → `GetDimensionData` | GUID present in section DB and readable | P1-11 |
| 4 | LT-B1/LT-B2 (GPT-LT-04) | disposable Morph; validator-passing body via `CreateMorphs` and `ModifyMorphs(body)`; readback `isClosed`, `bodyType` | `isClosed` matches validator verdict; document `bodyType` bug | P0-1, P1-6 pre-req |
| 5 | LT-B4 (new) | disposable Morph with property, classification, associative dimension, SEO link as target; delete + `CreateMorphs` + replay | table of survived/rebound/lost relation classes | P1-22 |
| 6 | GPT-LT-05 | Class-A recreate lineage + relink | links re-created; `GetSolidElementLinks` readback equal | P0-1 |
| 7 | GPT-LT-06 | `CreateComposites` → `CreateWalls(compositeId)` → `CompositeUsageIndex` → overwrite attempt → delete wall → retry; record scan timing | refused while used; allowed after; timing recorded | P0-21, P2-24 |
| 8 | GPT-LT-07 | ProfileBuilder (unchanged from audit plan) | as in audit plan | P1 profile items |
| 9 | GPT-LT-08 | `ApplyFavoritesToElementDefaults(SB_DIM_GOST_SPDS)` → `CreateAssociativeDimensions` at computed `referencePoint` (1:100, 1:50) → `GetDimensionData` | paper offsets ≥ 10/7 mm; human screenshot for ticks | P1-15 |
| 10 | LT-H1 (GPT-LT-09) | `CreateTexts(favoriteName)` → readback signature; repeat after `ImportFavorites` in a second project | deterministic visual result; signature behaviour documented | P1-14 |
| 11 | GPT-LT-10 | `AddLibraries` → `ReloadLibraries` → `GetAvailableLibraryParts` in two projects | same GSM listed, `skippedCount == 0` | P1-16 |
| 12 | GPT-LT-11 | `SaveAsModuleFile` → `CreateHotlinkNodes` (twice → `existing:true`) → `CreateHotlinkInstances` | assembly placed; dedupe works | P1-16 |
| post-PR | LT-A3 | `atomic:true` 3 valid + 1 invalid | `committed:false, rollbackVerified:true`, counts unchanged | P0-4, P2-20 |
| post-PR | LT-C4, LT-C5, LT-B3, Shell/Roof/EvaluateElements3D/GetFonts tests | as in audit plan | as in audit plan | P1-7/8/9/10/13/14 |
| never on 1.5.9 | LT-F3-ISOLATED | — | only on a fixed build, sacrificial session | P2-17 entry removal |

---

## 6. Final audit statement

- Static/source/design questions for the nine disputed points: **closed**. One low-impact normative citation (SPDS crossing tolerance clause) is left as `UNRESOLVED_SOURCE` and does not affect architecture (rule severity WARN until cited).
- Arena withdrew two statements and downgraded one grade (§3). GPT's counter-audit stands on all nine points; on §2.8 its premise was partly inaccurate, and the reconciled contract adopts its precision anyway.
- No `LIVE_CONFIRMED` grade was created or upgraded in this cycle. Every remaining unknown is in §5 as an executable test.
- Publication integrity: the inventory drift is documented and corrected on this branch (§1); remote branches are not rewritten.
- `main` of both repositories is untouched.
