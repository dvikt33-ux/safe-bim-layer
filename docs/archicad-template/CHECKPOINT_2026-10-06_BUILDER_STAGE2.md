# Archicad 29 Template — Executable Builder Checkpoint 2

Date: 2026-10-06
Branch: `feature/working-archicad-mvp`
Validated pre-checkpoint HEAD: `191cf1893ddf33ead7afb60bfd4dcd23e3405c27`

This checkpoint records the first repository state where the Archicad 29 RU/SBIM template specification has both:
1. machine-readable registries, and
2. an executable fail-closed builder with CI validation.

## CI evidence

GitHub Actions workflow:
- name: Validate Archicad template specs
- run id: 37518634694
- result: SUCCESS
- validated head: 191cf1893ddf33ead7afb60bfd4dcd23e3405c27

Passed:
- Python compile
- parse all template YAML files
- offline builder validation
- validation artifact upload

Offline validation counts:
- Layers: 40
- Layer Combinations: 14
- Semantic Pens: 30
- Candidate Line Types: 4
- Surfaces: 18
- Fill roles: 14
- Building Materials: 27
- SBIM Semantic Classification Items: 12
- SBIM schema Properties: 54
- Errors: 0
- Warnings: 0

## Executable builder actions

`scripts/archicad_template_builder.py`

Read-only/offline:
- validate
- inspect
- plan
- plan-materials
- plan-data-schema

Write stages, fail-closed by default:
- apply-core
- apply-surfaces
- apply-ready-materials
- apply-data-schema

All write stages refuse a non-empty project unless `--allow-nonempty` is supplied explicitly.

## apply-core

Creates/updates only the safe deterministic base:
- SBIM Project Info fields
- registered Layers
- Layer Combinations
- Pen Tables
- deterministic simple Line Types

Postcondition:
- model element count must remain unchanged.

## Surface stage

`surface-registry-v0.1.yaml`
- 18 deterministic, texture-free Surfaces.
- RGB and transparency are internal template visualization choices, not normative material properties.
- read-back validation is required after write.

## Fill stage

`fill-registry-v0.1.yaml`

Fail-closed policy:
- Empty and Solid are resolved from existing Archicad singleton fill subtypes rather than duplicated by localized name.
- generic 45-degree hatch is a live-calibration candidate.
- specialized material graphics (metal, wood, concrete, soil, etc.) remain `blocked_visual_source` until authoritative visual reconstruction and Archicad print/DWG tests are completed.

No specialized GOST fill is promoted merely from memory.

## Building Material stage

`apply-ready-materials`:
- resolves actual Fill and Surface attributes in the open project;
- creates only `READY_FOR_CREATE` Building Materials;
- physical properties are intentionally omitted until verified source data exists;
- blocked dependencies stay blocked;
- read-back validates IDs, priority, fill/surface indices, collision state and orientation;
- model element count must remain unchanged.

## Semantic data stage

Secondary Classification System:
- `SBIM Semantic`
- does not replace native Archicad classification used for IFC/type mapping.

12 stable semantic items:
- STRUCTURAL
- ENVELOPE
- PARTITION
- FINISH
- OPENING
- CIRCULATION
- SPACE
- MEP
- SITE
- REFERENCE
- ANNOTATION
- OTHER

The builder resolves real classification-item GUIDs through native Graphisoft JSON commands and creates 54 SBIM Property definitions with scoped availability.

Project-wide property defaults are not asserted globally; Favorites/agent workflows set instance/type defaults where appropriate.

## Tapir version decision

Current validated project pin:
- Tapir schema 1.5.8

Observed upstream:
- Tapir 1.7.0 released 2026-10-04.

No automatic upgrade is performed.
Upgrade requires regression of the already-proven model dump and write cycles.

Known template gaps remain:
- create/edit Model View Options presets
- create/edit Graphic Override rules/combinations
- Save As a new .tpl path
- Work Environment profile creation

## Next live gate

The repository-side preparation is ready for a clean Archicad 29 candidate project.

Required live sequence:

1. `validate`
2. `inspect`
3. `plan`
4. `apply-core`
5. `apply-surfaces`
6. `plan-materials`
7. `apply-ready-materials`
8. `plan-data-schema`
9. `apply-data-schema`
10. inspect/read-back again

After that:
- calibrate GOST fills in real Archicad views/print;
- create remaining Building Materials;
- create first verified Favorites;
- run junction matrix;
- build views/layouts/publisher;
- resolve MVO/Graphic Override gap;
- save first candidate TPL.

This checkpoint is not a released .tpl and does not claim live Archicad execution has occurred.
