# Material-role rules for generated architectural models

## Purpose

Generated BIM geometry must preserve stable material separation for render post-processing. Visual realism of the selected material is secondary to semantic consistency and deterministic grouping.

## Mandatory rules

1. Every generated element belongs to exactly one semantic material role before element creation or modification.
2. Elements in the same semantic role must reuse the same Archicad BuildingMaterial / Surface assignment within a project and across resumptions of the same generation job.
3. Different semantic roles must use different attribute IDs whenever the project contains enough distinct attributes. Do not intentionally reuse one material for unrelated roles merely because its name looks suitable.
4. Persist the selected role-to-attribute mapping in generation state. Never reselect materials on every run.
5. Material selection may use names as a preference, but names are not authoritative. Deterministic uniqueness of role mapping is the primary requirement.
6. For render-oriented output, keep at least these roles distinct when available: STRUCTURAL_STONE, TRIM_STONE, ROOF, METAL, GLAZING, FLOOR, TERRAIN, ROAD, DECORATIVE_STONE.
7. Native Archicad elements are preferred. Morph is reserved for shapes that cannot reasonably be represented by Wall, Slab, Roof, Beam, Column, Opening, Object, Stair, Railing, Shell, Mesh or other native tools.
8. If a custom Morph is required, assign its BuildingMaterial and per-face Surface consistently with its semantic role.
9. Material assignment is a quality gate: MODEL_READY is false if two roles that were requested as separate render groups collapse to the same attribute without an explicit documented reason.
10. Read-back must verify assigned attribute IDs where Tapir exposes them.

## Recommended state shape

```json
{
  "materialRoleMap": {
    "STRUCTURAL_STONE": {"buildingMaterialId": "...", "surfaceId": "..."},
    "TRIM_STONE": {"buildingMaterialId": "...", "surfaceId": "..."},
    "ROOF": {"buildingMaterialId": "...", "surfaceId": "..."},
    "METAL": {"buildingMaterialId": "...", "surfaceId": "..."},
    "GLAZING": {"buildingMaterialId": "...", "surfaceId": "..."}
  }
}
```

## Generation consequence

The generator should select materials once, persist the mapping, then pass only semantic roles through higher-level geometry code. Geometry builders should never independently search for materials. This avoids inconsistent render grouping after partial regeneration or retries.
