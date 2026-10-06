# Archicad 29 Template — Live Execution Runbook v0.1

This runbook converts the existing fail-closed builder actions into a reproducible live sequence for a clean Archicad 29 candidate project.

It does **not** claim that Archicad has already been executed from GitHub or from ChatGPT. The launcher must run on the Windows machine where Archicad 29 and the Tapir/native overlay are available.

## Launcher

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage preflight
```

Default Tapir port: `19723`.

Every stage writes one JSON evidence file per builder action plus `summary.json` under:

```text
outputs/archicad-template-live/<timestamp>/
```

The launcher stops immediately when:
- Python exits non-zero;
- the expected JSON evidence file is missing;
- builder result status is anything other than `PASS`.

This means `BLOCKED_ADDON_REBUILD`, `FAIL`, platform blocks, registry mismatches, non-empty-project write refusal, or other explicit gates cannot be silently bypassed.

## Stages

### 1. preflight

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage preflight
```

Runs:
1. `font-preflight`
2. `validate`
3. `inspect`
4. `plan`

No Archicad writes are expected.

### 2. core

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage core
```

Runs:
1. `apply-core`
2. `inspect`

Expected write scope: Project Info, Layers, Pen Tables, simple Line Types, Layer Combinations only.

### 3. materials-data

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage materials-data
```

Runs:
1. `apply-surfaces`
2. `plan-materials`
3. `apply-ready-materials`
4. `plan-data-schema`
5. `apply-data-schema`

### 4. navigator-master

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage navigator-master
```

Runs:
1. `plan-navigator`
2. `apply-navigator-shell`
3. `plan-master-layouts`
4. `apply-master-layout-shell`
5. `inspect`

The Master Layout stage must leave model-element count unchanged and must remove any temporary `__SBIM_MASTER_SEED_` Layout used by the builder.

### 5. all-safe

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage all-safe
```

Runs stages 1–4 in order. It intentionally does **not** run `plan-autotext`, because AutoText requires the rebuilt native overlay containing `GetAutoTextsV1`.

### 6. autotext gate

After rebuilding/loading the overlay:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage autotext
```

This runs only `plan-autotext`.

If the overlay is stale, the launcher must stop on `BLOCKED_ADDON_REBUILD`.

## Stop conditions before titleblock drawing

Do not proceed to full GOST R 21.101-2026 Form 3 geometry until all of the following are true:

- `all-safe` returns PASS;
- `autotext` returns PASS after overlay rebuild;
- one sacrificial Master Layout line is created and read back at the expected coordinates;
- one Text element is created and read back;
- one AutoText element is created and resolves to a real Archicad value;
- no model geometry count changes during any Master Layout test.

Only after those gates pass should full Form 3 line/text/AutoText generation be implemented.

## Deliberately excluded

This launcher does not:
- pass `--allow-nonempty`;
- create production model geometry;
- create or edit MVO, GO, Dimension Style, Publisher, DWG or IFC presets unsupported by the current API path;
- save a final `.tpl`;
- bypass any builder gate.
