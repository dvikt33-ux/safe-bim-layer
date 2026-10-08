# Checkpoint 30 — AC29 live delta QA: reuse Solibri Connection, IFC tools and HarnessBIM

Date: 2026-10-08
Scope: research-only. Do not touch user's open Archicad 29 PLN.
Carry-forward: checkpoints 24–29, CSE, normative junction rule matrix, Documentation Coverage Signature.
Parallel work (separate research track): native observer + zone-boundary + MEP distribution graph; work cited commits 1072b4d, e261c66, 44f6a0f. Treat as researched, not yet locally end-to-end proven.

## Breakthrough: official native incremental Archicad→Solibri already exists

Graphisoft **Solibri Connection for Archicad 29**:
- official AC29 add-on build 3000, 2025-10-01;
- automatically detects and transfers **only changed elements** into Solibri;
- IFC exchange includes classification, properties, types, colors, space boundaries, junctions and priority connections, hierarchical elements;
- BCF 2.1 issue return and round-trip selection;
- Solibri >=9.10.3.5 required, not Anywhere; paid/appropriate product entitlement needed;
- do not build our own Solibri synchronizer before assessing official extension.

Sources:
https://www.graphisoft.com/en-us/downloads/add-ons/solibri/
https://help.graphisoft.com/AC/29/INT/_AC29_Help/900_ExtraTopicsALL/900_ExtraTopicsALL-2.htm
https://help.graphisoft.com/AC/29/INT/_AC29_Help/900_ExtraTopicsALL/900_ExtraTopicsALL-5.htm

## Solibri open, documented interfaces — not a hypothetical API

Official REST: https://solibri.github.io/Developer-Platform/latest/RestApiUsage.html
- `POST /models`: upload initial IFC;
- `PUT /models/{modelUUID}/partialUpdate`: partial IFC carrying changed elements, directly related entities and the complete spatial containment tree;
- `POST /models/{modelUUID}/deleteComponents`: explicit IFC GlobalId list of deletions;
- `PUT /models/{modelUUID}/update`: full fallback;
- `POST /selectionBasket` + `GET /selectionBasket`: focused IFC component IDs;
- `GET /bcfxml/{version}`: BCF of current presentation issues;
- `GET /status`: busy / saved / modified;
- `GET /about` and `GET /ping`: capability and reachability;
- requires eligible Solibri license + running local Solibri.
CAUTION: REST's documented capabilities do **not** prove there is a public REST endpoint to execute every checking ruleset. Solibri Autorun batch checking is a separate documented execution route.

Solibri selected checking (UI):
https://help.solibri.com/hc/en-us/articles/1500004784001-Checking-a-Model-or-Selected-Components
- select components in Selection Basket, run Check Selected; useful for impact cone;
- Check Model provides complete release-stage check;
- need to validate whether automated trigger for selected check exists in the actual installed API; otherwise use UI/Java API where licensed.

Official Solibri Java API supports custom rules and geometry/component checks.
https://solibri.github.io/Developer-Platform/latest/getting-started.html
Solibri Autorun uses XML batch files to open IFC/SMC, open cset or IDS rules, run check, save SMC, export BCF/Excel. Requires Solibri software/license; exact entitlement depends on product.
https://solibri.github.io/Developer-Platform/latest/autorun.html
https://solibri.github.io/Developer-Platform/latest/autorun-tasks.html

Critical: Solibri warns checking results become UNSYNCHRONIZED after model updates and require rechecking.
https://help.solibri.com/hc/en-us/articles/1500004052882-Updating-Models

Do not confuse delta transfer with delta revalidation.

2026 alternative: Solibri WebChecker beta enables IFC upload + built-in health or custom .cset ruleset and PDF/BCF, but is cloud-oriented and model upload policy must be addressed.
https://www.solibri.com/articles/solibri-release-notes-april-2026

## OSS verifier toolkit: mature, but different roles

buildingSMART IDS 1.0 is a final standard.
https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/

**Hard limit**: IDS is restricted to IFC alphanumeric information, property/quantity/classification/material/relation facets, NOT arbitrary geometry. It cannot independently prove roof-membrane rise, fillet geometry, critical clearances or thermal bridges.

IfcTester:
https://docs.ifcopenshell.org/ifctester.html
- Python, CLI or web usage, human/machine-readable IDS;
- outputs HTML, ODS and BCF;
- appropriate for conditions such as required CSE family property, declared fire rating, or presence of junction test report identifiers;
- only validates supplied data, not truth of properties.

IfcClash + geometry BVH:
https://docs.ifcopenshell.org/ifcclash.html
https://docs.ifcopenshell.org/ifcopenshell-python/geometry_tree.html
- real geometric clashes, collision/intersection/clearance, tolerance;
- candidate wall-slab penetrations, ducts crossing structural zones, misalignments;
- still not whole normative compliance.

IfcDiff:
https://docs.ifcopenshell.org/ifcdiff.html
- compares two IFC files by STABLE GlobalIds;
- added/deleted/changed, properties, containment, geometry, type, classification;
- geometry comparison may report a difference when equivalent shape was represented through different constructs (false dirty candidate);
- suitable COLD snapshot delta regression and backup, not a replacement for Native Observer HOT events.

IfcPatch ExtractElements:
https://docs.ifcopenshell.org/autoapi/ifcpatch/recipes/ExtractElements/index.html
- can extract a subset of IFC elements and re-create spatial tree;
- **not** automatically guaranteed to meet Solibri partial IFC update protocol without relationship completeness checks;
- candidate research adapter only.

## CRITICAL GUID contract

Graphisoft IFC translator offers:
- Keep ARCHICAD IFC ID (stable across exports), recommended for version comparison/BCF;
- Generate new values (new IFC GlobalIds each export) defeats direct GUID delta tracking.

Source:
https://helpcenter.graphisoft.com/user-guide/89329/

Archicad native API Guid and IFC GlobalId are not the same identifier. Track a verified two-way map:
```
archicad_element_guid <-> ifc_global_id
```
with per-export translator identity, project identity, source revision and element type.

IFC Export View scope may hide elements: floor-plan view exports visible elements on selected story. Use audited 3D export view + translator to prevent false model absence.
https://help.graphisoft.com/AC/29/INT/_AC29_Help/900_ExtraTopicsALL/900_ExtraTopicsALL-5.htm

## HarnessBIM detailed source audit

Repo: https://github.com/ReverseZoom2151/harnessbim
License Apache-2.0; Python v0.0.1, externally optional packages: ifctester, ifcclash, PyNiteFEA, etc.
Verified source files: `pyproject.toml`, `docs/19-capability-ledger.md`, `docs/08-verification-and-eval.md`.

Useful **method/code audit candidates**:
- 9 checker aggregator (schema, IDS, clash, code, structural, MEP, egress, proofs, relations);
- verifier integrity / evidence;
- ruleset + revision routing;
- BCF worklist and per-discipline attribution;
- consistent evaluation and tests.
Project self-reports several focused test suites with skips and calls generative quality / substantial external training unproven. Its "architect-grade" output, Russian compliance, live AC29 backend, performance at our scale, and production resilience are NOT independently verified.

Existing parallel chat had already documented HarnessBIM in matrix v1.6; **do not reimplement generic verifier suite, nor copy claims as runtime proof**.

## Design decision: HOT/WARM/COLD verifier reuse hierarchy

**HOT — native AC29**:
- observer changes native GUIDs; native Model Dump selective geometry; CSE interface graph; zone/MEP graph when readback-ready;
- cheap local geometry and rule-applicability predicates, no full IFC export;
- every rule result signed to source GUID, CSE signature, revision, edition, evidence.

**WARM — optional delta external verification**:
- commercial lane when Solibri licensed: official Connection first; or partial-IFC Solibri REST if justified and tested;
- in Solibri: Check Selected for impacted IDs, then revalidate affected results;
- OSS lane: IfcTester/IfcClash/IfcOpenShell on IFC affected subset where data semantics sufficient; full-IFC baseline still needed for cross-system relationships.

**COLD — full release audit**:
- full IFC export with stable GlobalIds, audited export scope;
- IfcTester, IfcClash, optional HarnessBIM checker subset, Solibri full ruleset with paid license;
- verify consistency of plans, sections, schedules, issued PDF and building code evidence;
- NOT an unconditional Russian normative approval.

**RULE SEPARATION**:
1. IDS -> required metadata/quantities/classifications, not geometric roof upstand.
2. Geometric check -> physically measurable modeled details only, with LOD flag.
3. Numeric table -> SP 230.1325800.2015 if applicability signature exactly matches.
4. Simulation -> only the discipline-specific question it actually models.
5. Certification/human signoff -> assembly test and professional review.

## Status contract

Every finding returns:
```yaml
finding:
  id: ""
  affected_native_guids: []
  affected_ifc_global_ids: []
  condition_signature: ""
  rule_id: ""
  normative_edition: ""
  applicability: true # or false / unknown
  evidence_revision: ""
  source_model_revision: ""
  result: NOT_VERIFIED # NOT_APPLICABLE/PASS_GEOMETRY/PASS_DOCUMENTED/PASS_ENGINEERING/FAIL/NEEDS_SPECIALIST
  coverage_signature: ""
  linked_bcf_issue: null
  trust_tier: "native_hot|ifc_snapshot|solibri|specialist"
```

Partial external reports must never change unaffected COLD PASS into whole-model PASS.

## Future test plan (NO execution yet)

1. AC29_SOLIBRI_CONNECT_01 — audit install/license/versions; do not install into live project without consent.
2. IFC_ID_STABILITY_01 — export test model twice without edits; verify stable IFC GlobalIds, GUID mapping, geometry, properties; then move one wall and check 1 changed not 5,000.
3. IMPACT_CONE_01 — move wall adjacent to two zones; Native Observer + Zone Update + boundaries, partial readback, MEP links; compare affected set with independent manual audit.
4. SOLIBRI_PARTIAL_01 — initial IFC + partial update + deletion + BCF; verify Solibri updated state and checking stale signals.
5. IDS_VS_GEOMETRY_01 — IDS catches missing declared membrane property but not physical missing 300mm geometry; geometry rule catches latter when sufficient LOD.
6. IFC_DIFFERENCE_01 — compare IfcDiff result vs native event stream, flag representation-only noise and unstable IDs.
7. SECTION_QA_01 — after verified wall modification check dependent Section/CSE/detail Coverage Signatures.

**Primary KPIs**: human-minutes-to-accepted-fix, false PASS count (zero target), changed-elements transferred / total, actual check execution time, full vs selected QA correctness, stale-evidence detection.
