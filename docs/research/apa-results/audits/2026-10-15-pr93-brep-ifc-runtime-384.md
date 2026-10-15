# APA independent new verification — BREP, IFC relations, and registration (2026-10-15)

## Source and isolation

Audit branch: `audit/apa-brep-ifc-runtime-unique-20261015`.
Pinned base: PR #92 head `e5598dace18e878147466961b5b3ba9580339369`.
All tests import production APA functions. They create only synthetic objects and
temporary disposable IFC files. No Archicad connection, native APX installation,
live runtime writes, real PLN file modifications, or user data extraction.

## NEW verification groups (384 identifiers)

| Target | Cases | Independent oracle / property |
|---|---:|---|
| Native planar BREP cuboids | 80 | Analytic volume w*h*d and complete 6-face surface area |
| Multi-solid native BREP | 48 | Sum of independent component surface and volume |
| BREP defects | 48 | Missing face, incorrect normal winding, nonplanar or zero-volume shell rejected |
| Unsupported native bodies | 48 | Curved or unclosed bodies explicitly NOT_VERIFIED |
| Native Beam/Column segment ownership | 48 | Aggregate only valid same-host, same-story and matching-type segment bodies, deny mismatches |
| SDK/Add-On availability contract | 64 | Stub transport checks exact namespace/name and availability booleans, without LIVE promotion |
| Actual synthetically authored IFC4 void relationships | 48 | Host/Opening GUID mappings, type/selection invariants, analytical/material absence stated honestly |
| **Total** | **384** | Production BREP + IFC + DynamicCommands adapters |

Test source: `tests/test_archicad_brep_ifc_registration_unique_qa.py`.
Isolated shard runner: `scripts/apa_brep_ifc_unique_qa_shard.py`.
Windows workflow: `.github/workflows/apa-brep-ifc-unique-384.yml`.
Ten SHA256-partitioned Windows runners and a separate aggregator enforce 384 unique
test IDs, no duplicates or omissions, and explicitly record ERROR/FAIL/XFAIL.
No tests from earlier 735 + 378 + 288 + 384 suites are rerun.

## Evidence state

Code committed to GitHub. CI must finish before reporting a PASS.
The 8 known router defects remain open (not reclassified by this suite).
The SDK availability tests use a stub *only* and provide zero evidence of
installed Archicad APX command registration. IFC assertions are local file
semantics, not normative or model-acceptance evidence.
