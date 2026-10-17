# Task-scoped live catalog binding for Unified Discovery

Depends on PR #133, which already installed the Roof provenance bridge on the laptop.

## Gap closed at the integration boundary

PR #132 discovers the historical contracts of Grid, ExactStair and other add-ons, but it deliberately leaves commands missing from the actual live export as `SOURCE_ONLY`. `DynamicCommands.probe_runtime` already checks `API.IsAddOnCommandAvailable` for selected add-on commands; its response by itself cannot authenticate a source snapshot's schema.

This change adds **`prepare_current_runtime_catalog_task(writer, intent, planner_python=None)`** to the existing Unified Discovery sidecar. It:

1. Loads the **current export** via existing `APA.catalog_with_provenance(writer.schema_path)` and compares its project binding with `writer.guarded_binding()` and installed Archicad 29 / Tapir version. Thus a historical JSON snapshot alone is not treated as the active runtime.
2. Reconstructs the **same existing DynamicCommands router** from that export, attaching the existing functional providers, official SDK and previously reviewed policies through existing functions. Absent commands stay source-only.
3. Prepares the task through the **same `discover_catalog_task` and existing BIM Graph**. Does not probe all catalog commands.
4. For native Grid/ExactStair candidates actually present in that exported schema, demands the existing **`APA.verify_native_runtime_identity`** exact APX build check.
5. Calls the existing `router.probe_runtime` *only for candidate commands in an otherwise executable task alternative*. Failed registration is excluded from this task. Source-only contracts are **never promoted** on registration evidence alone.
6. Re-prepares with the task-scoped availability facts, returning `(router, preview, report)`. The returned router is the one to pass to the **existing** APA execution function. The helper does not execute any model command or modify a PLN.

A read-only probe of a local analytical provider is **not** labelled native registration. A product-version check for official Archicad API methods is explicitly labelled `CLIENT_PRODUCT_MATCH_NOT_PER_METHOD_REGISTRATION` by the existing implementation. Unresolved effects remain `UNKNOWN`, and caller-supplied source data still requires the original qualification and writer scopes.

### Important limits

This is an opt-in **live** entrypoint and must run in the actual authorized laptop process with the correct, currently exported schema. It does not itself export a new native schema, install/replace an APX, change runtime permissions, save a PLN, or perform a write. For source-only commands absent from the actual export, the result is still blocked. No LIVE_PASS is claimed in this GitHub change.

The existing `APA.prepare_auto_optimized_native_task` offline entrypoint remains unchanged. This sidecar helper does not create another catalog, planner, command executor, or writer. Existing SceneWriter guardrails remain mandatory for any later authorized execution.

## Safe local update

The pre-existing incremental sidecar updater `scripts/apa_update_roof_discovery_bridge.py` has been retargeted to the exact **already installed** Roof bridge SHA256 `54f25c0f24bd65d929d51ffb73e1efecaaf3a44031e704849b8275b516a32812` and the final GitHub blob for the augmented module. As before, it validates the unchanged APA core and DynamicCommands hashes, creates a unique backup, and updates only `archicad_strategy_discovery.py`, never the original engine.

The earlier PR #133 updater remains available at its previous commit for its original installation/receipt. This GitHub pass has **not** installed the new revision locally, called Archicad, or run pre-existing tool functional tests.
