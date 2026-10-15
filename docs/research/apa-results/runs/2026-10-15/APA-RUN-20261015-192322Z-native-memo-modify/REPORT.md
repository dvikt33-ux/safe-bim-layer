# Native assembly editing: real effects and bounded memo contracts

Continuation of exact PR107 `9a3091638eaa1a9c72f9a08c17d02855d8419edc`. A11.S03 remains **PARTIAL**. No offline tests, test workflow dispatch or quantity-engine calls.

The approved live cycle used the exact PR107 APX in an explicitly authorized Save As copy. The original saved model was never overwritten. The original APX and registration are restored; the copy was reopened in a new process, and all409 current native signatures independently matched.

| Operation | Actual native result | Acceptance |
| --- | --- | --- |
| Extruded Shell vector | Length4.0→4.5m along existing Y vector; unchanged profile, frame, contours, native material assignments, story, GUID and IFC identity | **LIVE_PASS** for this exact supported subset; IFC export and engineering not verified |
| Railing Rail height |0.07→0.17m; native BREP rises0.10m;18 dependent baluster bottoms rise0.10m while their tops remain1.08m | Geometry confirmed; **PARTIAL**, because two GDL BuildingMaterial assignments on one nested native Object drifted |
| Curtain Wall scalar height | SDK returned NoError, but actual height stayed2.0m and resultant body did not change | **NO_EFFECT**, no PASS or retry; new preparation and SDK reject this scalar route |
| Exact material recovery | One approved setter attempt; original material GUID/index37 independently confirmed. Only unlocked bmatRail sent; disabled bmatFixing reserved for dependent readback | `APIERR_NOTSUPPORTED` from native Element_Change/AddPars; all409 signatures and all128 placed parameters unchanged. **Not restored**; owner-aware edit still required |

The material drift is specifically bmatRail and bmatFixing, index37→36 (stainless→structural steel), on one native-owned Object. Aggregate effective face surfaces were unchanged and were insufficient to prove material preservation. Initial geometry callback wording is explicitly corrected by [the side-effect audit](https://github.com/dvikt33-ux/safe-bim-layer/blob/13139d6cd03340bff7fbde5ccac5735929843b7a/docs/evidence/APA_NATIVE_MODIFY_SIDE_EFFECT_AUDIT.json). Historical raw records remain intact.

The saved copy has409 GUIDs, with zero additions or removals. Against the pre-edit native baseline,20 resultant BREP signatures and one additional material-only signature differ.314 elements outside the qualified Railing/Shell roots and all prior258 elements retain their signatures. Native body-pool index changes are excluded using the existing geometry-signature implementation.

The Curtain Wall and recovery scenes retain their original UNKNOWN journal state, supplemented by independent reconciliation hashes. The timed-out Open call was not replayed. Subsequent restart and original-runtime readback independently verified persistence of the saved state, including the material drift. No rollback or dependent repair was fabricated.

## Product changes

The existing `GetNativeAssemblyEditStateV1` now exposes supported native memo data: Curtain Wall reference polygon, contour, plane/segment information, primary/secondary pattern distances and native IDs; Railing path/Z values; explicit association/write limits. The existing `ModifyNativeAssemblyV1` supports bounded same-topology straight Curtain Wall reference/contour and pattern edits. Coordinates, closure, counts, allocation bounds and IDs are checked before native Element_Change. Scalar Curtain Wall height is refused after its observed no-effect result.

Extruded Shell retains its existing vector/profile path and adds class-specific native tilt fields. Revolved scalar-angle fields are a separate **source/build-only** subset. Ruled profile editing, new Shell holes and Railing association/path writes are not advertised as supported. Railing path data are readable, but changing the path remains blocked until its native association contract is qualified.

No new command names or second executor were added. Shared preparation and execution stay in `apa_native_parameter_edit.py` and delegate to the existing DynamicCommands → SceneWriter → SQLite path. Optional body and typed-material verifiers are independent. Omitting the material verifier explicitly leaves material acceptance unverified. `native_material_retention` compares every scoped element's native materialBindings, including typed GDL assignments, instead of aggregate face-surface sets. Existing GDL getter/setter preparation preserves scalar/matrix types and now has before/after readback and script-dependent-change diagnostics. It distinguishes native Disabled, Fixed and hidden flags.

The existing MEP topology command adds public SDK Elbow/Branch ownership, dimensions, domain and applicable preference/insulation facts. `Transition.GetAngle()` is documented in degrees; the new field is `angleDegrees`, correcting the prior `angleRadians` label. This is a schema change requiring consumers to use the new schema. Existing ports, systems and routing commands remain reused. There is no new MEP connection, preference mutation or positive MEP runtime claim.

## One dependency graph

Actual native component ownership, applicable materials, assembly states,128 placed GDL parameters, three IFC identities and nine IFC properties pass through the existing dependency adapter. The resulting captured slice has **346nodes/472edges**. A structural-steel material impact reaches four nodes through the existing DependencyImpact. The source hash and relation counts are in [the connected-flow evidence](https://github.com/dvikt33-ux/safe-bim-layer/blob/13139d6cd03340bff7fbde5ccac5735929843b7a/docs/evidence/APA_NATIVE_MEMO_CONNECTED_FLOW.json). This slice is not an additive count against PR104's different captured scope.

Root, parent and declared-owner identities remain distinct.24 differing declared-owner/parent cases do not generate inferred edges. Missing library-part identity does not produce a name-based relationship. Curtain Wall scalar height is a read-only derived fact, not an editable driving parameter. No dependent native writes are scheduled.

## Build and runtime boundaries

The newest full Windows/Archicad29 Release artifact is SHA256 `84841037512024d1a2df5832453968422c1046575fd461a3c7555745ed3289ba`, native source revision `bc241f54ba463f305d6e45178427ba79871271f3`. It is **BUILD_PASS_NOT_INSTALLED**. Python-only material acceptance improvements were added after that native source revision.18 existing SDK contracts remain; no command-name inflation.

The approved and tested PR107 binary is SHA256 `4e6cdf2a59e46c50b78f52558fe2e9f3cd19a51c4b1142898dda29d2bcc3aead`. Its actual documentation exposed293 commands. Its enhanced opening/envelope/component fields are distinct from the still-pending exact PR104 binary authorization. The newest memo/MEP changes have no runtime acceptance yet.

No new APX permission is inferred. The original runtime is restored and the authorized copy remains open. IFC accessor identity preservation is separate from export verification. Quantity engine stays quarantined. Opening107 post-close comparison, positive MEP topology, three unresolved Drawing sources and complex-class native editing remain open.

## Exact continuation

First implement an owner-aware native route for the two Railing material assignments; the direct nested-Object AddPars setter is proven unsupported and must not be replayed. Keep the approved material-only scope and Rail0.17m/Shell4.5m geometry. A changed native implementation requires an exact-binary approval before deployment.

Then obtain separate approval for the reviewable848410 candidate and an explicit same-root contour/pattern trial in the existing copy. Check actual Curtain Wall contour/BREP height, child GUID mapping and per-element typed materials. Do not reuse the failed scalar scene. Positive MEP reads need an existing authorized MEP sample; no recreation or unsafe ConnectLogically call is implied.

Publication uses one new draft PR, all commits `[skip ci]`, direct existing publisher functions and byte/blob GitHub readback. Actual push/pull_request/manual workflow definitions are checked before publication; no workflow settings or protected rules are changed.


Published [draft PR109](https://github.com/dvikt33-ux/safe-bim-layer/pull/109) at `13139d6cd03340bff7fbde5ccac5735929843b7a`. Claim revision178; A11.S03 remainsPARTIAL. This publication action changes only repository artifacts, not PLN/APX/runtime. The preceding explicitly authorized native copy cycle and its material-restoration failure are recorded above.
