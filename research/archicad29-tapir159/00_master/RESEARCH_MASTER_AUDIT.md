# RESEARCH MASTER AUDIT

Branch: `research/archicad29-tapir159-expansion`

Final consolidated audit:

`../09_final_audit/FINAL_RESEARCH_AUDIT.md`

## Objective

Maximize Archicad project throughput while minimizing routine, failures, background resource use and unsafe automation.

## Research baseline

- Archicad 29
- Tapir Additional JSON Commands 1.5.9 (user-reported installed version)
- upstream Tapir 1.5.9 tag pinned in research to commit `d0dbb11b13942e014661e1402b07958b70cd9dba`
- Safe BIM fail-closed runtime remains the only intended production write authority

## Research documents

### Missing data / source semantics

- `../01_missing_data_audit/MISSING_DATA_AUDIT_PASS_01_10.md`
- `../01_missing_data_audit/MISSING_DATA_AUDIT_PASS_11_20.md`

### Tapir 1.5.9 delta

- `../02_tapir_159_delta/TAPIR_159_DELTA.md`

### Expansion candidates

- `../05_expansion_candidates/AI_RUNTIME_AND_DEV_ACCELERATION.md`
- `../05_expansion_candidates/PROJECT_ACCELERATION_PASSES_01_20.md`
- `../05_expansion_candidates/PROJECT_ACCELERATION_PASSES_31_40.md`
- `../05_expansion_candidates/PARAMETRIC_GDL_LIBRARY_FACTORY.md`

### Integration audits

- `../06_integration_audits/AI_RESOURCE_EFFICIENT_ARCHITECTURE.md`
- `../06_integration_audits/DEVELOPMENT_ACCELERATION_AUDIT.md`
- `../06_integration_audits/PROJECT_ACCELERATION_FOLLOWUP_PASSES_21_30.md`
- `../06_integration_audits/EXTERNAL_TECHNOLOGY_INTEGRATION_AUDIT.md`

### Final passes/audits

- `../09_final_audit/PREFINAL_AUDIT_AFTER_PASS_40.md`
- `../09_final_audit/FINAL_PASSES_41_50.md`
- `../09_final_audit/FINAL_RESEARCH_AUDIT.md`

## Master conclusion

The research converged on a deterministic **project compiler + Safe BIM runtime** architecture:

`template/seed + project profile + favorites + hotlink modules + optional GDL library -> versioned ProjectRecipe -> deterministic DAG compiler -> certified Safe BIM operations -> Tapir 1.5.9 -> incremental QA/docs/publish`.

AI is optional, on demand, and used for planning only. Known recipes bypass AI. Local AI is unloaded before physical BIM execution/reconciliation.

## Highest-value next implementation sequence

1. Pin Tapir 1.5.9 schema/source and version compatibility.
2. Correct Arc/Mesh/Morph/Roof offline contracts.
3. Capability/evidence registry.
4. Typed ProjectRecipe and deterministic DAG compiler.
5. Project Profile/preflight.
6. Filtered multi-GUID readback batching.
7. Favorites + selection/highlight/ScriptUI.
8. Hotlink module catalog.
9. Reusable archetype recipes.
10. Incremental QA/documentation pipeline.
11. SEO/trims and GDL component factory.
12. Optional AI broker last, after deterministic fast paths exist.

## Research boundary

Broad source archaeology is no longer the main bottleneck. Remaining uncertainty is concentrated in narrow controlled live probes, performance benchmarks and implementation-specific certification. See `FINAL_RESEARCH_AUDIT.md` for the exact list.
