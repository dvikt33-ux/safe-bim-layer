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

**CI result VERIFIED: SUCCESS / 384 of 384 PASS**, run
https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38660906311

- Verified code+workflow commit: `8028cd5ab37c5d23d311cb897e4dde3d6212bd0d`.
- 10 of 10 Windows test shards SUCCESS, cross-shard accounting SUCCESS (11/11 jobs).
- 384 discovered and 384 executed unique test IDs; 0 FAIL, ERROR, SKIP, XFAIL or unexpected success, 0 coverage issues.
- SHA256 of sorted test IDs: `2ee93d1b002165d63419048b04a03b95e802d4cc8f04fbc5d513ec55ba38ff92`.
- Test count per shard: 34 + 40 + 33 + 47 + 37 + 40 + 31 + 37 + 44 + 41 = 384.
- GitHub Actions aggregator printed `APA_BREP_IFC_EXACT_384 True` and `APA_BREP_IFC_SHARDS success`. Logs and shard/aggregate artifacts retained in Actions.
- This final evidence documentation commit does not change tested executable code. No previous suites were rerun.
The 8 known router defects remain open (not reclassified by this suite).
The SDK availability tests use a stub *only* and provide zero evidence of
installed Archicad APX command registration. IFC assertions are local file
semantics, not normative or model-acceptance evidence.
