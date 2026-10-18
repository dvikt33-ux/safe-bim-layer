# APA AC29 IFC artifacts B2

Three new commands attach to the existing DynamicCommands instance:

| Command | Ready upstream implementation | Independent artifact |
|---|---|---|
| IFCCSVExport | IfcCsv.export | properties.csv, property and quantity selectors |
| IFCExtractElements | fixed ExtractElements.Patcher | subset.ifc, reopened with selected GUID check |
| IFCBCFIssues | BcfXml 2.1 + topic.add_viewpoint | issues.bcfzip, selected IFC GUIDs read from XML |

Namespace: `AddOn.APAIFCArtifactsB2`. All take `a`, `output` (new directory),
`query` (IfcOpenShell selector). CSV also takes `attributes` (list of selectors).
BCF takes `title`, `description`, `author`. Every operation produces report.json.
Register using `apa_ifc_artifacts_b2.register(existing_router, trusted_python_path)`;
the executable is deployment configuration, never a routed input.

## Source and file preservation

All vendor operations use a SHA-verified private IFC copy inside a temporary
directory under the new output directory. No original is passed to a mutator.
The parent compares the original SHA before/after the child process and checks
the JSON receipt, adapter SHA and artifact SHA through typed CSV/IFC/ZIP readers.
CSV formula-like cells are escaped for spreadsheet opening; the count is reported.
The IFC recipe is imported directly, so IFCPATCH_RECIPE_DIR cannot substitute code.
Asset deduplication by name is disabled to avoid mixing distinct same-name assets.
BCF requires placed IfcProducts, limits topics to 2000, creates real viewpoint
selection references, and makes no snapshot or native Archicad GUID claim.

## Validation and versions

- Windows Python 3.12, real IfcOpenShell/IfcCSV/IfcPatch/bcf-client **0.8.5**.
- Nine targeted tests: real router/subprocess CSV properties/quantities, formula
  escaping, IFC re-open/GUID/spatial tree/property/representation preservation,
  BCF reload and selected GUID, nonoverwrite, empty-selection failure, missing
  placement, version/boundary guards, recipe override resistance, 21 old catalog
  entries preserved byte-for-byte at the object level (24 total).
- Real B1 tests and 21 V2 regression contracts also run in CI on Windows
  Python 3.11/3.12 using the committed full dependency lock.
- IfcCSV and IfcPatch: LGPLv3+ source headers; bcf-client 0.8.5: GPLv3 METADATA.
  Libraries remain independent installed distributions; no vendor code/binary is
  copied into this repository. Preserve license notices on any redistribution.
- New autonomous policy explicitly authorizes isolated installation. Earlier B1
  installation-permission blocker is resolved by the user's newer instruction.

SOURCE: VERIFIED. OFFLINE: real synthetic-fixture tests PASS. BUILD: Python only.
INSTALLED/LIVE/ACCEPTED require their own receipts. No native Archicad calls or
PLN/APX changes occur in these adapters. Output schema integrity is not proof of
full geometry equivalence or Russian regulatory compliance. Failed commands may
leave an incomplete output directory; diagnose and select a new output path.

Base: package B1 branch/PR #166. No main merge or project-plan #182 changes.
Remaining package B: IfcConvert binary/format verification; existing V1 IFCDiff
and IDS JSON operations are reused and are not counted as new.
