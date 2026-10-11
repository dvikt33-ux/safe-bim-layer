# Final Audit Addendum — Gable Roof, Flat Roof/Parapet, Composite Structures

Date context: Archicad 29 + Tapir Additional JSON Commands 1.5.9.

## What is source-confirmed

### Native one-element gable roof
Archicad API supports a Multi-plane Roof as one native Roof element. Per pivot edge data supports `Sloped` and `Gable` segment angle types. Tapir 1.5.9 does not expose this per-edge write contract in `CreateRoofs`; a small Tapir extension remains the preferred solution rather than two independent Single-plane Roof elements.

### Composite structures
Archicad Composite attributes carry ordered skins, skin Building Materials, skin roles and thicknesses and may be flagged for Wall/Slab/Roof/Shell. Tapir 1.5.9 already exposes `GetComposites` and `CreateComposites`, and Wall/Roof creation can reference an exact `compositeId`.

### Flat roof + parapet
A normal constant-thickness sloping flat-roof build-up maps cleanly to a Single-plane Roof; parapet maps to Walls. A truly horizontal structural body can be a Slab. Optional grouping is available after individual element verification.

## What should be extended in Tapir 1.5.9

Highest-value small extension:

1. **Read first:** expose Multi-plane Roof `pivotPolyEdges` / per-edge `levelEdgeData`, including `angle`, `eavesOverhang`, `angleType`, through RoofDetails or a dedicated read command.
2. Verify one user-created native gable reference roof in AC29.
3. **Write second:** add optional `pivotEdgeSettings` to `CreateRoofs` for Multi-plane Roofs only, mapping exact polygon edges to `API_PivotPolyEdgeData` / `API_RoofSegmentData`.
4. Read back the created roof by exact receipt GUID and verify the per-edge definition.

This extension should remain version-gated to the exact audited Tapir build and should not alter current default hip-roof behavior when `pivotEdgeSettings` is omitted.

## What does NOT need a Tapir extension for first implementation

- Creating/reusing Composite attributes.
- Reading Composite skins/useWith/separators.
- Attaching a Composite to a Wall or Roof.
- Creating parapet Walls.
- Grouping roof + parapet elements.

These capabilities already exist in Tapir 1.5.9; Safe BIM needs wrappers, strict preflight, fingerprints, receipts and reconciliation.

## Safety findings

1. Never overwrite an existing project Composite automatically. Global attribute mutation can change many model elements at once.
2. Pre-resolve every Building Material and line type referenced by `CreateComposites`; Tapir's loop does not provide a sufficiently strong fail-closed guarantee for unresolved dependency IDs.
3. Always send `useWith`; omission can produce a Composite with no intended usage flags.
4. A Composite wall/roof's authoritative total thickness is the sum of its skins. Do not treat element-level `thickness` as an independent resize operation.
5. Do not infer a material from normative text by fuzzy name alone. Preserve source text and require exact/project-approved material mapping.
6. Tapir issue history includes accepted-but-ignored fields, including roof thickness on an AC28 report. Every field that matters must be read back; a successful command response alone is insufficient.
7. Grouping is convenience only and occurs after all member GUIDs are individually verified.
8. Existing live-probe and production gates remain unchanged until an independent audit explicitly changes them.

## Recommended read-only reference set

User can manually create in `Test_House.pln`:

- `GABLE_REF`: one ordinary rectangular Multi-plane Gable Roof, known pitch and overhang.
- `FLAT_ROOF_BASIC_REF`: Single-plane Roof with known small fall.
- `FLAT_ROOF_COMPOSITE_REF`: Single-plane Roof using an existing Composite.
- `WALL_BASIC_REF`: Basic wall with known thickness.
- `WALL_COMPOSITE_REF`: Composite wall with known Composite and total thickness.
- `PARAPET_REF`: parapet Wall at the flat roof perimeter.

The next automated interaction should initially be read-only.

## Target architecture after certification

```text
Construction requirement / SP evidence
        ↓
ConstructionAssemblySpec
        ↓
Building Material resolver
        ↓
verified Composite attribute receipt
        ↓
Native element recipe
  ├─ one-GUID Multi-plane Gable Roof
  ├─ Single-plane Flat Roof
  ├─ Basic/Composite Wall
  └─ Parapet Wall assembly
        ↓
exact GUID + attribute readback
        ↓
VERIFIED / STOP
```

## Final verdict

The roof requirement is not blocked by Archicad's native model. The principal roof gap is narrow and local to Tapir's JSON exposure of Multi-plane per-edge data. Multilayer construction creation is substantially closer: the core Tapir 1.5.9 attribute functionality already exists and should be integrated through strict Safe BIM resolution and verification rather than reimplemented.
