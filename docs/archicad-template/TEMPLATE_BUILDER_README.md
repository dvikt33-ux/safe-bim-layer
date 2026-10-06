# Archicad Template Builder

This builder materializes the proven safe subset of the AC29 RU/SBIM template specification through the existing Tapir 1.5.8 JSON API.

## Commands

Offline validation:

```powershell
python scripts/archicad_template_builder.py validate
```

Windows font preflight before opening/issuing the candidate template:

```powershell
python scripts/archicad_template_builder.py font-preflight --out template-fonts.json
```

This checks required font families from `fonts-manifest.yaml` in the Windows font registry. Style detection is advisory because Windows registry display names vary.

Read-only inventory of the currently open Archicad project:

```powershell
python scripts/archicad_template_builder.py inspect --out template-inspect.json
```

Read-only live plan:

```powershell
python scripts/archicad_template_builder.py plan --out template-plan.json
```

Resolve Building Material dependencies against the actual open project (read-only):

```powershell
python scripts/archicad_template_builder.py plan-materials --out template-material-plan.json
```

Create the deterministic texture-free Surface registry in a CLEAN candidate project:

```powershell
python scripts/archicad_template_builder.py apply-surfaces --out template-surfaces.json
```

Create only Building Materials whose live Fill + Surface dependencies are already resolved:

```powershell
python scripts/archicad_template_builder.py apply-ready-materials --out template-materials.json
```

Plan the SBIM classification/property schema using native Archicad classification discovery (read-only):

```powershell
python scripts/archicad_template_builder.py plan-data-schema --out template-data-plan.json
```

Inspect live View Map / Layout Book / Publisher prerequisites and report missing MVO or unverified GO/Dimension presets (read-only):

```powershell
python scripts/archicad_template_builder.py plan-navigator --out template-navigator-plan.json
```

Create the secondary `SBIM Semantic` Classification System and scoped SBIM Property Groups/Definitions:

```powershell
python scripts/archicad_template_builder.py apply-data-schema --out template-data-schema.json
```

The Building Material command never forces blocked dependencies. Specialized GOST cut fills remain blocked until their geometry is visually verified and calibrated in Archicad.

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

It does NOT yet auto-create:
- specialized GOST Fills (visual-source/calibration gate)
- unresolved Building Materials
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


## Navigator shell

After the manual seed presets (MVO / Graphic Override / Dimension Styles) are created and `plan-navigator` is reviewed:

```powershell
python scripts/archicad_template_builder.py apply-navigator-shell --out template-navigator-shell.json
```

This creates only:
- View Map folders
- Layout Book subsets

It intentionally does not create formal Views, Master Layout titleblock graphics, Layout drawings or Publisher Sets.

Current live sequence for a clean candidate project:

1. `font-preflight`
2. `validate`
3. `inspect`
4. `plan`
5. `apply-core`
6. `apply-surfaces`
7. `plan-materials`
8. `apply-ready-materials`
9. `plan-data-schema`
10. `apply-data-schema`
11. create/verify manual seed presets from `seed-presets-registry-v0.1.yaml`
12. `plan-navigator`
13. `apply-navigator-shell`
14. read-back / Model Dump verification
