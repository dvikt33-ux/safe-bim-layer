# APA 29 / FeaturePack V2 — 12 read-only IFC/DXF functions (DRAFT)

**State: SOURCE verified + OFFLINE CI PASS (19/19 on Windows Python 3.11 and 3.12).** The compiled source and stdlib unit contracts passed on commit `fda2ae1dd14b33f8e46babd7f15e32e4a5a52c6c` (GitHub run [39150225899](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/39150225899)). **No vendored IFC/DXF package was installed or executed in this V2 CI; no local Windows install, Archicad run, LIVE or ACCEPTED evidence.**

## Changes relative to its base PR #154

- `scripts/apa_high_density_readonly_v2.py`: **12** reviewed, independently addressable commands. New namespace `AddOn.APAHighDensityReadOnlyV2.*`.
- `scripts/apa_high_density_entrypoint_v2.py`: opt-in entry point; invokes the **existing V1** session factory and original DynamicCommands Router, first verifies that the original **six** V1 commands are unchanged, then registers 12 additional READ_ONLY actions.
- `tests/test_apa_high_density_readonly_v2.py`: stdlib unittest source with coverage of cardinality, input types, GUID integrity, IFC2x3 georeferencing absence, relations, DXF facts, read-only permissions, unsafe responses.
- `scripts/apa_high_density_session_factory_v2.py`: strict opt-in composed session; loads source-verified V1 factory (six old commands), adds 12 V2 commands, independently checks both sidecar manifests and the V2 factory's own SHA256.
- `scripts/install_apa_high_density_readonly_v2.py`: explicit preflight/install/check only; uses atomic side-by-side copy into `external-tools/apa-readonly-v2`; never overwrites V1 or installs additional pip packages. Installer **has not been executed on the user machine**.
- `tests/test_apa_high_density_v2_install_factory.py`: 9 extra stdlib tests for duplicate prevention, SHA drift, separate receipts and 6+12 composition.
- `.github/workflows/apa-high-density-readonly-v2.yml`: independent Windows 3.11/3.12 compile, 19 offline tests, V1=6 + V2=12 catalog integrity; **PASS**.
- **No edits** to the original six handlers, the V1 installer, V1 catalog/session factory, SceneWriter, Tapir, main, PLN, APX, or deployed Python.

## New callable commands

IFC / only the pinned IfcOpenShell 0.8.5 environment when installed:

1. `IFCSchemaInventory`: IFC schema, types and element counts.
2. `IFCGlobalIdAudit`: duplicates, blank GlobalId.
3. `IFCSpatialRelations`: aggregation and containment.
4. `IFCOpeningRelations`: void/fill graph.
5. `IFCPortRelations`: exported `IfcRelConnectsPorts`.
6. `IFCPropertySetCoverage`: property-set assignment summary.
7. `IFCClassificationCoverage`: classification relation coverage.
8. `IFCGeoReferenceAudit`: CRS/map-conversion evidence only.

DXF / only the pinned ezdxf 1.4.5 when installed:

9. `DXFLayerInventory`: layer inventory and counts.
10. `DXFBlockInsertions`: INSERT transformations and attributes.
11. `DXFTextAnnotations`: TEXT/MTEXT raw facts.
12. `DXFDimensionEntities`: DIMENSION raw facts, **not** calibrated construction dimensions.

Total **12 new source routes** + **6 preexisting V1 source routes** = **18 potential read-only router routes**. This does not imply installed or tested functionality. No new pip dependencies were added.


## Current evidence by stage (verified 18.10.2026)

| Stage | State | Evidence |
|---|---|---|
| SOURCE | VERIFIED | Source under this draft branch, explicit readback SHA |
| OFFLINE | PASS | Windows Actions 3.11 and 3.12, 19/19 focused stdlib tests each |
| BUILD | PARTIAL | Python `py_compile` PASS; no AC29 add-on build required for this sidecar, no vendor executable smoke |
| INSTALLED | NOT VERIFIED | `--install` has **not** run against the actual `C:\\LocalAI\\APA_AC29_Stable` |
| LIVE | NOT RUN | No live Archicad connection and no real IFC/DXF vendor run in V2 CI |
| ACCEPTED | NO | Actual isolated install receipt, real sample source/report SHA and independent readback required |

**Deployment constraints:** Side-by-side only. The V2 installer explicitly requires a verified installed V1 vendor runtime and V1 session factory, then creates `apa-readonly-v2` without overwriting anything. Opt-in session factory used only after manual approval; it does not register new commands into already running APA processes. No local installation was attempted in this change.

## Explicitly not integrated

- IfcCSV / IfcConvert / BCF output: CSV/OBJ/ZIP needs a new safe file-type manifest. Existing V1 vendor invoke path only parses JSON, so adding those actions directly would fail.
- IfcPatch: may modify an IFC file; requires isolated copy, non-overwriting output and relationship preservation. Not a read-only first-wave command.
- Native Copy/Hotlink/Publisher/MEP: not part of the V2 reader. Keep existing APA native writer and require local Tapir command discovery and separate LIVE authorization.
- Heavy AI models, SAF→PyNite, Russian SP compliance claims, GPU workload.

## Preflight and acceptance ladder

1. **SOURCE:** verify SHA/branch, exact 12 command keys, independence from V1 six, inspect registration/review_policy.
2. **OFFLINE:** run `python -m unittest tests.test_apa_high_density_readonly_v2` in a nonproduction checkout; additionally test actual pinned vendor versions on synthetic IFC2x3/IFC4 and DXF with INSERT/DIMENSION/MTEXT. Never infer test success from committed source.
3. **BUILD:** if regression tests pass, create a side-by-side V2 installation receipt and pin SHA256 of the V2 source. Do **not** loosen V1 six-command/hash invariants; do **not** overwrite `C:\LocalAI\APA_AC29_Stable\external-tools\apa-readonly-v1`.
4. **INSTALLED:** check existing vendor V1 doctor/manifest, 12 names in opt-in temporary session and preservation of six V1 names; if V1 vendor is not installed, **BLOCKED**.
5. **LIVE:** optional read-only test against an exported IFC/DXF copy (not a source PLN). Inspect source/report SHA256, error paths, object/port/global-id relationship coverage.
6. **ACCEPTED:** independent readback + receipt and approval. **Not reached in this change.**

Safety: only `.ifc` or `.dxf` input; new explicit `.json` output; exclusive create; output forbidden under stable APA installation; fixed command whitelist; no `shell=True`, no PLN open/save, no native Archicad API calls, evidence of source SHA256; bounded sample arrays.

Base branch: `feature/apa-external-pdf-lossless-20261018`; compare/PR should target this branch rather than main.
