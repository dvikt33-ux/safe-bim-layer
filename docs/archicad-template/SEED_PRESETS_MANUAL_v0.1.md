# Archicad 29 Seed Presets — Manual Gap v0.1

The current Tapir 1.5.8 workflow can create and assign most template data, but it cannot author three preset families from scratch:

- Model View Options combinations
- Graphic Override rules/combinations
- Dimension Style presets

These are therefore treated as a **small manual seed**, not as an excuse to build the rest of the template manually.

## Required seed names

### Dimension Styles

- `DIM_01_SPDS_MM`
- `DIM_02_LEVEL_M`

`DIM_01_SPDS_MM`: linear dimensions in millimeters, 0 decimals, 2.5 mm text baseline.

`DIM_02_LEVEL_M`: level/elevation display in meters with 3 decimals, signed levels, 2.5 mm text baseline.

The exact project dimension settings are stored with Views, so these names become part of the View API contract.

### Model View Options

Create exactly:

- `MVO_01_WORK_FULL`
- `MVO_10_AR_DOCUMENT`
- `MVO_20_COORD`
- `MVO_30_SITE`
- `MVO_40_PRESENTATION`

Do not over-configure MVO on day one. The first goal is stable differences between working, documentation, coordination, site and presentation representation. Library-part-specific options are calibrated with the Global Library actually loaded in the clean candidate project.

### Graphic Overrides

Create the semantic rules listed in `seed-presets-registry-v0.1.yaml`, then assemble:

- `GO_00_NONE`
- `GO_10_QA_DATA`
- `GO_11_QA_NORM`
- `GO_20_PB_FIRE_COMPARTMENTS`
- `GO_21_PB_EVACUATION`
- `GO_30_MEP_SYSTEMS`
- `GO_40_AUTOMATION_STATE`
- `GO_90_PRESENTATION`

Rule order is part of the contract. A higher rule wins when simultaneous overrides conflict.

The rules are intentionally based on SBIM Properties instead of layer names or surface colors. This keeps semantic state independent from visualization.

## Why this is safe

Graphisoft stores Graphic Override Combination and Model View Options selection as View settings. Graphic Override combinations are ordered collections of rules; their order controls precedence.

After the seed exists, the builder can assign these exact names to generated Views. Before the seed exists, View creation stays blocked.

## Verification

After manual seed creation run:

```powershell
python scripts/archicad_template_builder.py plan-navigator --out template-navigator-plan.json
```

MVO presence is checked directly. Tapir 1.5.8 cannot enumerate GO/Dimension preset registries, so those remain explicit manual assertions until a stronger API/add-on path is available.

Then create only the safe Navigator shell:

```powershell
python scripts/archicad_template_builder.py apply-navigator-shell --out template-navigator-shell.json
```

This creates View Map folders and Layout subsets only. It does not create model geometry, formal Views, titleblock graphics, Layout drawings or Publisher sets.
