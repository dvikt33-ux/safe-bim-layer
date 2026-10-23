# Counteraudit B — snapshot vs runtime and geometry completeness (SOURCE-only)

Independent angle: verify readback evidence and project identity without using mutation path.

1. Pinned `tapir-scene-live.json` has 262 commands, metadata provider_version 1.5.10, historical test PLN `Тест MER .pln`, port 19723. It contains neither `GetModelDumpV1` nor `GetAPARuntimeInfoV1`; this does NOT establish absence in the installed APX.
2. `DynamicCommands.probe_runtime` can check `API.IsAddOnCommandAvailable` for a selected command. It does NOT hash the loaded APX or prove the entire parameter/return contract; GetAddOnVersion alone also does not.
3. `GetAllElements` has optional `databases` and return `executionResultForDatabases`. Current `inventory_guids` calls `GetAllElements({})` and reads `elements`; this does NOT prove omission of story 1, but does not establish exhaustive multi-database completeness either.
4. `Get3DBoundingBoxes`/typed details are not independent closed BREP. `GetModelDumpV1` fallback is source-known but its runtime registration must be proven before reliance. Active filters and 3D view scope need explicit evidence.
5. New BUILD-01 requires separate scratch path/SHA/authorization, Save/Close/Reopen and fresh GUID+BREP inventory, then second changed brief; historical PR74 21-element success is bounded demo.

**Counterfinding B-01:** G0 remains BLOCKED on exact loaded APX SHA and runtime inventory; G4 independent BREP NOT_FOUND for current installed contract. Minimal path: Windows read-only loaded-module path+SHA, runtime probes, per-database fail-closed inventory, existing guarded save and independent BREP. No new writer/engine.

Sources: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-automatic-group-routing-20261018/schemas/tapir-live-1.5.10/tapir-scene-live.json ; https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-automatic-group-routing-20261018/scripts/archicad_dynamic_commands.py ; https://github.com/dvikt33-ux/safe-bim-layer/issues/192

OFFLINE=0 BUILD=0 INSTALLED=0 LIVE=0 ACCEPTED=0.
