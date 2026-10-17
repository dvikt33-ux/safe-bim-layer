# APA AC29 — external read-only tools (isolated V1)

**Source branch:** `feature/apa-readonly-tools-isolated-20261017`, stacked on PR #139,
**not** on the unsafe/unreconciled PR #140. **Main is unchanged.**

## Why

The existing APA already has `ifcopenshell==0.8.5` in
`scripts/requirements-connected.txt` and a real
`archicad_connected_ifc.inspect_quantified_exchange`.
This package does **not** create a second IFC engine, SceneWriter, task
executor, native command router, or quantity computation implementation.

This read-only **sidecar** only integrates the available upstream tools:

- `ifcclash==0.8.5`: IFC geometry collision report (clashes are NOT errors by default);
- `ifcdiff==0.8.5`: compare two user-supplied IFC exports;
- `ifctester==0.8.5`: validate model against an explicitly provided IDS file;
- `ifc5d==0.8.5`: optional availability in same family; no new QTO computations;
- `ifcopenshell==0.8.5`: pinned to existing APA version;
- `pdfplumber==0.11.10`: PDF text, lines, rectangles in PDF points;
- `ezdxf==1.4.5`: DXF raw modelspace primitives;
- `networkx==3.6.1` / `shapely==2.2.0`: existing local IFC quantity reader dependencies.

Official references:
- https://docs.ifcopenshell.org/ifcclash.html
- https://docs.ifcopenshell.org/ifcdiff.html
- https://docs.ifcopenshell.org/ifctester.html
- https://pypi.org/project/ifcopenshell/0.8.5/
- https://github.com/jsvine/pdfplumber
- https://ezdxf.readthedocs.io/en/stable/

## Installation boundary

**Preconditions:** Windows 11 x64, `py -3.12`, verified installed
`C:\LocalAI\APA_AC29_Stable` with
`apa-selector-install-receipt.json`. Download to a separate clone.
No Archicad process, PLN, APX, dispatcher or mailbox update is needed.

The installer only creates:
`C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1\`

It creates a **new isolated Python 3.12 venv**, uses
first downloads **odfpy 1.4.1** and verifies its published PyPI SHA-256; then installs\nthe remaining exact pinned packages using `pip install --only-binary=:all:` and runs `pip check`,
imports three actual vendor CLIs, then writes `installation.json`.
It neither upgrades the core APA interpreter nor installs any Archicad Add-On.

Execute from PowerShell (only after reviewing this PR):

```powershell
$ErrorActionPreference = 'Stop'
$repo = 'dvikt33-ux/safe-bim-layer'
$ref = 'feature/apa-readonly-tools-isolated-20261017'
$clone = Join-Path $env:TEMP 'APA_ExternalReadonly_20261017'
if (Test-Path $clone) { throw "Source folder already exists; inspect it before proceeding: $clone" }
gh repo clone $repo $clone -- --branch $ref --depth 1
if ($LASTEXITCODE -ne 0) { throw 'GitHub clone failed' }
& py -3.12 (Join-Path $clone 'scripts\install_apa_external_readonly.py') --install
if ($LASTEXITCODE -ne 0) { throw 'Isolated installer blocked; do not blindly retry' }
```

Verification is read-only:

```powershell
$py = 'C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1\venv\Scripts\python.exe'
$adapter = 'C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1\apa_external_readonly.py'
& $py $adapter doctor
```

Examples with **your own user-supplied paths**:

```powershell
& $py $adapter ifc-diff --a 'D:\IFC\before.ifc' --b 'D:\IFC\after.ifc' --output 'D:\IFC\diff-evidence.json'
& $py $adapter ifc-clash --a 'D:\IFC\architecture.ifc' --b 'D:\IFC\services.ifc' --output 'D:\IFC\clash-evidence.json'
& $py $adapter ids-validate --a 'D:\IFC\architecture.ifc' --ids 'D:\IFC\criteria.ids' --output 'D:\IFC\ids-evidence.json'
& $py $adapter ifc-qto --a 'D:\IFC\architecture.ifc' --output 'D:\IFC\qto-existing-apa-evidence.json'
& $py $adapter pdf-vectors --a 'D:\Drawings\source.pdf' --output 'D:\Drawings\source-vectors.json'
& $py $adapter dxf-vectors --a 'D:\Drawings\source.dxf' --output 'D:\Drawings\source-dxf-vectors.json'
```

Every run has an allowlisted action, known upstream module, local source
SHA256 and **new exclusive** JSON output. No shell string input or arbitrary
external command execution. Subprocess invocations are fixed and never use
`shell=True`.

**Important:** a PDF drawing's raw vectors are not metres and are never
treated as approved BIM coordinates. DXF unit header does not establish
coordinate system or project origin. IFC clash overlap may be intentional.
IDS PASS is not Russian building-code or engineering acceptance.

## Integration with APA

V1 connects via a deterministic **read-only evidence file interface**. The
normal APA process keeps all native operations unchanged. The adapter can be
started explicitly by a caller with `subprocess` and its resulting
`APA_EXTERNAL_READONLY_EVIDENCE_V1` JSON can be attached to the existing
BIM Graph / provenance task. There is **no automatic command-catalog registration
or autonomous model writer** in this package; that requires a separate
reviewed integration after installing and verifying the real vendor outputs.

For quantities, `ifc-qto` imports and calls the **existing**
`archicad_connected_ifc.inspect_quantified_exchange` from the stable APA
instead of duplicating geometry formulas.

## Acceptance statuses

- Source files on GitHub: `SOURCE_PREPARED`.
- Stdlib test/compile CI (if successful): `OFFLINE_INTEGRATION_PASS`.
- Windows isolated installation: `NOT_RUN` until exact install receipt.
- Actual upstream analysis on real user IFC/PDF/DXF: `NOT_RUN`.
- Native CREATE/MODIFY/save: **not supported by this sidecar**.
- The separate BDD 1.14 unknown write outcome must be reconciled before any
  native write or job retry. Isolated package installation does not reconcile it.

Rollback: uninstalling only the reviewed isolated directory and its venv is
possible later; the installer intentionally has **no delete command**.
Do not delete the core APA or user PLN. Do not merge to main, repoint
Dispatcher, or auto-install an APX as part of this work.
