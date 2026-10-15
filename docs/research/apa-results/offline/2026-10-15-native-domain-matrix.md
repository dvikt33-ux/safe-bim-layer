# APA offline native-domain & dynamic-security matrix (2026-10-15)

Status: **OFFLINE_PASS / JUNIT_VERIFIED**. GitHub Actions [#38728924457](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38728924457), code commit `84c40745693aea3a2a2467eadda3e148e755c897`: 1922/1922, 12/12 Windows shards PASS, 0 failure, 0 errors, 0 skipped. Initial run [#38728539689](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38728539689) showed 12 test-oracle failures in Navigator map routing; test oracle corrected without changing production implementation. Research receipt: draft PR in `research/apa-new-offline-domains-20261015`.

Source base: draft PR #100 head 31b4d39b35907ef21fa0fe7dbf13dd1c7c8ed82a, with native-positive code from PR #97. Follow-up isolated branch ci/apa-offline-mass-parallel-new-domains-20261015; no changes to main or the original PR branches.

## New coverage: 640 parametrized pytest instances

- 128 hierarchical membership / parent / root GUID and impact-propagation variants for Curtain Wall and Railing-style assemblies.
- 128 Generic Opening host / reverse / cut / self-reference / duplicate-link combinations.
- 128 Navigator-to-Drawing exact identity, map, deletion, ownership and ambiguous-source combinations.
- 128 Slab/Roof straight-parameter-polygon, hole, malformed record and partial omission cases.
- 128 dynamic-command ticket tamper and effect/scope permission cases.

These use production offline adapters against deterministic synthetic data; they are not proof of native Archicad CurtainWall/Railing/Shell geometry, resultant Generic Opening voids, live Navigator resolution, or native writing. The suite deliberately does not exercise model writes.

## Execution acceptance gates

Windows Python 3.11: all 12 independent CI shards + 2 workers each; collect per-shard actual JUnit and manifests. Report exact executed tests, failures, errors and skips only from emitted artifacts. No OFFLINE_PASS assertion before GitHub Actions verifier succeeds. The former 1282/1282 run is an independent historical receipt, not evidence for this new matrix.

## New audit candidates

1. Build archived-native contract mutation fixtures for Shell's contour-edge serialization and Revolved/Ruled class discriminants (SOURCE/BUILD only).
2. Reconcile forward and reverse Generic Opening links with native void BREP in the authorized Archicad test environment (LIVE only).
3. Verify nested Railing/CurtainWall membership against independent parent/root SDK queries (LIVE only).
4. Reject ambiguity between trusted explicit view IDs and mismatched Navigator query identities (safety audit).
