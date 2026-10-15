# Native parametric editing and linked parameter data

Continuation of PR104, exact base `6ae582b9f2a9666389fc06fd0528bbfff3fde6b4`. A11.S03 remains PARTIAL. This package performs **no offline tests, model writes, APX installation or quantity-engine calls**.

The product now has a shared, compiled native MODIFY contract and a single preparation/readback adapter. These new mutation paths are **BUILD_PASS, not LIVE_PASS**. Existing runtime calls independently demonstrate a useful material → placed GDL parameter → native component → IFC identity → property dependency chain. The previously pending visual inspection of the three accepted complex native samples is completed.

## Available operations and exact limits

| Native type | Masked changes implemented | Scope boundary |
| --- | --- | --- |
| Curtain Wall root | Height, story-relative level | Reference lines, segment patterns and full frame/panel schemes require additional native memo work. Existing MoveElements handles placement. |
| Curtain Wall frame | Building Material, surface, own-material flag | Exact typed attribute GUID required; names are not identities. |
| Curtain Wall panel | Thickness, Building Material, outer/inner/cut surfaces and override flags | Root and target GUID retained; generated children must be reconciled. |
| Railing root | Default segment height, default post offset, bottom offset | A default height is not proof that every customized segment changes. Association with Stair remains NOT_VERIFIED. |
| Railing segment/node | Segment height and offsets; node elevation/post offset | Does not create associations or alter the reference-path topology. |
| Railing rail/handrail | Height, horizontal offset, visibility | Applicable native component fields only. |
| Shell | Level; Basic thickness/material or Composite identity; surfaces and flags; Extruded begin/vector | Applicable structure/class fields only. Extruded profile editing preserves vertex count and accepts one straight contour without arcs. Existing memo closure/body/edge data are preserved. New holes and Revolved/Ruled editing remain unsupported. |

`GetNativeAssemblyEditStateV1` reads current type, story, decimal-string native modification stamp, applicable values and typed attribute identities. `ModifyNativeAssemblyV1` takes the exact GUID, expected type/stamp and explicit changes. It rereads and checks the stamp inside the native undoable operation, applies SDK masks with `ACAPI_Element_Change`, and never implements MODIFY by delete/create. Root/component masks are shared across nine native types; source availability is not execution permission.

`scripts/apa_native_parameter_edit.py` provides `prepare_assembly_edit`, `execute_assembly_edit` and `prepare_existing_gdl_edit`. Preparation returns an existing dynamic-command ticket and no permission. Execution delegates to the **existing router → SceneWriter → SQLite**. The caller supplies explicit authorization for an isolated copy, the affected root/complete child subtree, retained signatures and saved-model identity. A fresh captured-state digest guards preconditions; independent parameter, attribute and membership reads reconcile added/removed children. Physical resultant geometry still requires separate body acceptance. No automatic dependent writes, second journal, retries or alternative executor were added.

## Public MEP integration

`GetNativeMEPTopologyV1` adds the missing public SDK ownership/identity facts for RoutingElement, RoutingSegment, RoutingNode, RigidSegment and Transition. It returns native parents, segment/node IDs, system identity, applicable dimensions/preferences, terminal logical references and transition ports. Existing `GetMEPPorts`, `GetMEPRoutingElements` and `GetMEPDistributionSystems` provide ports, physical flags, peer references and distributions; those implementations are reused.

The existing dependency adapter preserves separate native, port, connection, system, segment and node namespaces. A physical connection requires reciprocal native port evidence. Logical references, system membership and geometric proximity never substitute for physical connectivity. Missing specialized headers/relationships remain explicit. Current open architectural copy has no MEP elements or systems, so positive topology runtime validation remains NOT_VERIFIED. No global preferences, route GUIDs, connectors or quantity engine were changed.

## Practical GDL / material / IFC flow in the original runtime

One existing placed Curtain Wall frame supplies **49 current GDL parameters**, including one **2×2 array**. The adapter reuses `SetGDLParametersOfElements` rather than introducing another setter. Current GetGDL returns flattened arrays, while the existing setter interprets a flat array as Nx1. Preparation reconstructs the declared row-major matrix, preserving both dimensions; scalar/array/type/lock checks fail closed. A current-value preview was prepared, **not executed**. Native GDL editability and dependent script effects are not accepted by preparation alone.

Current reads of that same frame yield **one nonempty IFC identity and seven property rows**. Native Building Material and Surface headers resolve typed GDL attribute indices to actual attribute GUIDs. The existing graph now represents **60 nodes / 59 dependencies**: 49 parameter edges, two typed material/surface edges, one IFC identity and seven property edges. Existing `DependencyImpact` finds **11 affected nodes** for a selected material change. This is impact analysis, not an instruction to perform dependent writes. A library-part edge was omitted because no actual library-part identity was captured. IFC accessor strings do not prove export or complete semantic compatibility; `IFC_EXPORT_NOT_VERIFIED` remains.

## Native visual and retention evidence

The existing Shell, Railing and Curtain Wall were selected individually in the actual Archicad 3D window. Native `GetSelectedElements` confirmed the sample GUID for each screenshot. Targeted Native Model Dump readback of only those three roots matches their accepted geometry signatures; saved PLN bytes remain unchanged. This closes the prior visual-inspection gap without recreating samples or repeating the full 409-GUID inventory.

![Existing native Extruded Shell](https://github.com/dvikt33-ux/safe-bim-layer/blob/9a3091638eaa1a9c72f9a08c17d02855d8419edc/docs/evidence/native-parametric-visual/shell.png)

![Existing native Railing](https://github.com/dvikt33-ux/safe-bim-layer/blob/9a3091638eaa1a9c72f9a08c17d02855d8419edc/docs/evidence/native-parametric-visual/railing.png)

![Existing native Curtain Wall](https://github.com/dvikt33-ux/safe-bim-layer/blob/9a3091638eaa1a9c72f9a08c17d02855d8419edc/docs/evidence/native-parametric-visual/curtain-wall.png)

An attempt to open the separate 107-GUID Opening project encountered a save-changes prompt for the current model. **Open was cancelled** to preserve unknown unsaved state. No Save/Discard was selected. The prior 107-project post-close comparison remains NOT_VERIFIED; this no longer depends on an unavailable computer-use interface.

## Build, runtime and catalog

- Full Archicad29 Windows Release compile/link passed. Binary hash, size, build identity, source hashes and private build-log digest are in `docs/evidence/APA_NATIVE_PARAMETRIC_BUILD.json`; binaries and raw private logs are not committed.
- Three new SDK contracts are source-identified, implemented and BUILD_PASS. All three were independently reported absent by the original runtime registration probe. They have **no CALLABLE_VERIFIED or LIVE_PASS** yet.
- Existing source catalog attachment produces **391 preparable entries**: 276 Tapir-source, 73 official JSON, 32 add-on-source and ten local entries. This is a deduplicated preparation count, not 391 installed commands. The functional manifest has 18 SDK contracts. Current original-runtime compatibility retains the historical337 baseline; only the three new negative registration checks are fresh in this package.
- Exact PR104 binary `2ed42a…e91cb` permission is still pending; no duplicate request or deployment occurred. The newer build is a distinct binary and is not authorized by that pending request.
- Quantity engine stays QUARANTINED. The three unmatched Drawing sources, class-specific Shell extensions and unrestricted assembly path editing retain their precise limitations. No Navigator update was invoked.

## Publication without tests

Actual workflows on the code base, canonical research branch and default branch were inspected before publication. Only push, pull_request and manually dispatched workflows were present; no pull_request_target or workflow_run handler was found. All new commits include `[skip ci]`. The existing publisher is invoked directly for one immutable run, its normal indexes and receipt; no publisher workflow, watchdog or test runner is invoked. The preexisting pending publisher file is preserved. GitHub byte/blob readback and Actions inspection establish the publication outcome. Workflow behavior follows the [GitHub skip-workflow documentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs); skip text alone is not treated as a universal guarantee.

## Exact continuation

1. When the existing exact PR104 APX permission is answered, perform only its authorized read-only enhanced-field checks and restoration; do not substitute this newer binary.
2. Separately authorize the new compiled binary and an isolated-copy MODIFY scenario. Validate one root parameter, one native component attribute and an Extruded profile/vector change through the shared journal, independently accept bodies/child GUID mapping, then Save/Open. Do not alter accepted samples without that permission.
3. Validate the new MEP topology on an existing positive MEP model once it can be accessed without losing unsaved current state. Then extend native paths/patterns and Shell contour classes sequentially. Audit proposals are recorded without creating duplicate task IDs.


Published [draft PR107](https://github.com/dvikt33-ux/safe-bim-layer/pull/107) at `9a3091638eaa1a9c72f9a08c17d02855d8419edc`. Canonical claim revision176; task remainsPARTIAL. No offline tests, native model writes or APX changes. Actual build is distinct from the pending PR104 exact-binary request.
