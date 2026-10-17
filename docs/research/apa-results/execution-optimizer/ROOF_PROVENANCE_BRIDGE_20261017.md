# Roof source-provenance bridge (after PR #132)

**Scope:** Unified Discovery only; does not change native tools or execute Archicad.

## Resolved contract mismatch

The existing source-derived Roof qualifier requires `sourceRoofId` to establish the source GUID, but the pinned Tapir `CreateRoofs` native input schema excludes that field.

Unified Discovery now accepts `roofSource` **at the task-step level**, not in native `roofsData`. The field must have exactly:

- `guid`: source Roof GUID appearing in `sourceVerification.ownedGuids` or `retainedGuids`;
- `nativeReadbackVerified: true`;
- `nativeSignatureSHA256`: 64-character hexadecimal signature of that source readback.

Because `roofSource` is part of the step rather than `sourceVerification`, it is included in the existing source-data hash. The existing `archicad_native_roof_editing.qualify_operation` checks an isolated deep copy of the native parameters with its provenance field injected. **The original native task stays schema-compatible without `sourceRoofId`**.

Roof creation also requires explicit `floorIndex`, `thickness`, `structureType`, `holes`, and the correctly corresponding `buildingMaterialId` or `compositeId`, using the existing polygon/pivot/slope qualifier for geometry.

## Qualification boundary

A caller-provided signature is not independent proof of live Archicad state. The unchanged original SceneWriter authorization, project identity, preflight and readback gates must verify source state and produced geometry before a model write. The change does not qualify a source-only runtime contract, claim native acceptance, modify a PLN, or benchmark an operation.

**Status:** source/schema integration changed; runtime verification NOT_RUN. Previously working APIs are not re-tested here. Other source-only Grid/ExactStair contracts remain unavailable for executable auto-selection until their runtime identity and matching contracts are confirmed. No synthetic substitution or forced activation was introduced.
