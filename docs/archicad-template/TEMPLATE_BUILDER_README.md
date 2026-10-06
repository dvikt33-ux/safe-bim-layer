# Archicad Template Builder

This builder materializes the proven safe subset of the AC29 RU/SBIM template specification through the existing Tapir 1.5.8 JSON API.

## Commands

Offline validation:

```powershell
python scripts/archicad_template_builder.py validate
```

Read-only inventory of the currently open Archicad project:

```powershell
python scripts/archicad_template_builder.py inspect --out template-inspect.json
```

Read-only live plan:

```powershell
python scripts/archicad_template_builder.py plan --out template-plan.json
```

Apply safe core to a CLEAN candidate project:

```powershell
python scripts/archicad_template_builder.py apply-core --out template-apply.json
```

The builder refuses a project that already contains model elements unless `--allow-nonempty` is explicitly supplied.

## What apply-core writes

- custom SBIM Project Info fields
- registered Layers
- registered Layer Combinations
- semantic Pen Tables
- simple deterministic Line Types

It does NOT yet create:
- Fills
- Surfaces
- Building Materials
- Composites
- Properties/Classifications
- Favorites
- Views/Layouts/Publisher
- MVO or Graphic Override presets

Those remain gated by source/attribute-dependency resolution and additional regression tests.

## Safety

Every Tapir request/response is retained below the normal `SAFE_BIM_MVP_EVIDENCE` directory.

The safe-core phase does not create/delete model geometry. Element count is checked before and after the write pass.

## Dependency

```powershell
python -m pip install -r scripts/requirements-template.txt
```
