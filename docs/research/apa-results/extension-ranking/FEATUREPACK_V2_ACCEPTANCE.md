# APA 29 / FeaturePack V2 — 12 read-only IFC/DXF functions (DRAFT)

**State: SOURCE only.** This branch adds code and offline test *sources* but does not claim that tests were executed, that any package was installed on Windows, that Archicad was opened, or that LIVE/ACCEPTED evidence exists.

## Changes relative to its base PR #154

- `scripts/apa_high_density_readonly_v2.py`: **12** reviewed, independently addressable commands. New namespace `AddOn.APAHighDensityReadOnlyV2.*`.
- `scripts/apa_high_density_entrypoint_v2.py`: opt-in entry point; invokes the **existing V1** session factory and original DynamicCommands Router, first verifies that the original **six** V1 commands are unchanged, then registers 12 additional READ_ONLY actions.
- `tests/test_apa_high_density_readonly_v2.py`: stdlib unittest source with coverage of cardinality, input types, GUID integrity, IFC2x3 georeferencing absence, relations, DXF facts, read-only permissions, unsafe responses.
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
