# APA AC29 IFC reports B1

Three new independent operations, extending the existing DynamicCommands router:

| Command | Inputs besides a/output | Result |
|---|---|---|
| AddOn.APAIFCReportsB1.IFCSelect | query (IfcOpenShell selector expression) | Selected STEP ids, IFC GlobalIds, classes and inverse references |
| AddOn.APAIFCReportsB1.IFCSchemaValidate | none | IfcOpenShell schema diagnostics, no EXPRESS/geometry/code compliance claim |
| AddOn.APAIFCReportsB1.IDSReportODS | ids (specification path) | Upstream IfcTester ODS spreadsheet plus JSON evidence |

`a` is an exported IFC, `output` is a **new directory**. Every operation creates
`report.json`; IDS also creates `ids-report.ods`. No source file is overwritten.
The parent process verifies source hashes before/after the vendor subprocess and
independently re-reads the JSON and ODS ZIP metadata/CRC/SHA. Failure can leave an
incomplete output directory; choose a new directory after diagnosing failure.

## Reuse and invocation

Reuse V1's verified isolated interpreter, V2 path/hash guards, and the original
DynamicCommands registration, prepare and read implementation. No router, BIM
engine, SceneWriter or native transport is added or edited.

```python
import apa_ifc_reports_b1 as reports
# router is the caller's existing approved APA DynamicCommands instance
reports.register(router)
ticket = router.prepare("AddOn.APAIFCReportsB1.IFCSelect", {
    "a": "export.ifc", "output": "new-selection-report", "query": "IfcWall"})
result = router.read(None, ticket, reviewed_read_only=True)
```

The module must be available on the caller's Python path. Registration is opt-in;
there is no installer or attachment to a running installed APA session.

## Evidence on 2026-10-18

- Package A base: PR #165 SHA `94441ebebd0fffdedcea2e044a09e80bfedbe244`.
- Base diff against `ca28e9b8003eeb3a38ca201ea96c0096e07b677f`: eight additive V2 files;
  no V1/core changes. Base local tests 21/21 PASS; Windows 3.11/3.12 CI:
  https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/39150750133
- B1: 10 real-vendor tests PASS on Windows Python 3.11.9, including real router,
  subprocess, IFC4 and IFC2X3 selection, inverse containment, invalid GUID,
  passing/failing IDS ODS, source preservation and output/error guards.
- B1: six dependency-free contracts PASS, including deep equality of all 18
  pre-existing catalog entries after registration (21 total).
- CI runs the six contracts plus 21 V2 tests on Windows Python 3.11/3.12.
  CI deliberately does not install or run vendor packages; local vendor evidence
  must not be confused with CI source-contract evidence.
- SOURCE: VERIFIED. OFFLINE: PASS (synthetic fixtures, real vendor execution).
  BUILD: Python only. INSTALLED: NO. LIVE: NOT RUN. ACCEPTED: NO.

## Vendor contracts and licenses

Source inspected in existing installed distributions: IfcOpenShell **0.8.5**
`util.selector.filter_elements`, `file.get_inverse`, `validate.validate` and
`validate.json_logger`; IfcTester **0.8.5** `ids.open`, `Ids.validate`,
`reporter.Ods.report/to_file`. Both distributions declare LGPLv3+ in METADATA.
No vendor source/binaries are copied or redistributed; exact versions are
checked at execution. Existing ODS dependency is odfpy 1.4.1 from V1.
Newer online docs are navigation references, not proof of the 0.8.5 contract:
https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/selector/index.html
https://docs.ifcopenshell.org/autoapi/ifcopenshell/validate/index.html

## Boundaries and remaining package B

- IFCSelect uses the existing IfcOpenShell selector; it is not a claim to install
  the separate IfcQuery product. Result arrays are capped at 5000 with totals.
- Schema validation disables EXPRESS rules; it is not geometry or SP/GOST review.
- IFCDiff (including relationships) and IDSValidate JSON already exist in V1.
  They are reused, not counted as new functions.
- IfcCSV and IfcPatch are absent from the inspected V1 environment. A requested
  isolated test installation was rejected by automatic approval review under
  the user's installation restriction; user approval remains pending.
- IfcConvert executable/version/format contract and BCF package are not verified;
  no callable placeholders have been registered.
- No installed APA files, PLN/APX, main or project plan #182 changed.

Next available work: package C primitives/contours/repeated assemblies using
existing ezdxf APIs, preserving coordinates, units and explicit uncertainties.
