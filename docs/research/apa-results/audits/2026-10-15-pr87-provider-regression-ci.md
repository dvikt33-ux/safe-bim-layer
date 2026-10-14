# APA independent Windows regression: dynamic provider registration and policy gates

Date: 2026-10-15. Independent GPT-6 offline QA.

## Provenance

- **Source baseline**: PR #85 head `45ef6b734e70c0e2c40ea57ed9a0099d70c4a917`.
- **QA code under test**: commit `5bffb0c53974f443465d811b5a1dd97c89850373` on new separate branch `audit/apa-dynamic-provider-regression-20261015`.
- **QA PR**: [#87](https://github.com/dvikt33-ux/safe-bim-layer/pull/87), drafted against `feature/apa-executable-bim-workflows-20261015`. Work's original feature code is **unchanged**.
- **Actual Windows CI**: [GitHub Actions run 38648282345](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38648282345), `windows-latest`, Python 3.11, completed **SUCCESS**.
- Focused command: `python -m unittest discover -s tests -p 'test_archicad_independent_provider_audit.py' -v`.
- **Observed**: `Ran 28 tests in 0.007s`, `OK (expected failures=8)`. Hence **20 PASS**, **8 XFAIL**, **0 unexpected failure** and **0 unexpected success**. The five original failure expectations were retained, and three new failure expectations were added in the second run.
- These are **actual tests importing APA Python modules in remote Windows CI**, not manually transcribed algorithms. Archicad is not launched, local PLN/APX are not touched, and a full existing 741-test suite was not repeated for this QA package.
- Test file: `tests/test_archicad_independent_provider_audit.py`; workflow file: `.github/workflows/apa-independent-provider-audit.yml`.

## Positive guarantees verified by running the module (20 PASS)

1. Source-only command is discoverable but not mislabeled runtime registered or LIVE.
2. A simulated absent APX registration is rejected by the current runtime check.
3. Explicit runtime `False` registration is BLOCKED.
4. Explicit runtime `True` alone is not called LIVE_VERIFIED.
5. A namespaced add-on command does not replace an existing unqualified Tapir command.
6. Duplicate command identifier is rejected.
7. Namespaced `$ref` uses the declared schema; bad types are refused.
8. Incompatible reviewed contract hash prevents rebinding stale policies.
9. Missing policy source hash is rejected.
10. A **listed protected** host GUID is rejected for model creation.
11. An unknown `elementId.guid` is rejected by the scope.
12. Prepared ticket is independent of later caller mutation.
13. Changing effect policy invalidates a previously prepared ticket.
14. BIM Graph cycles are rejected.
15. Successful `success:true` envelope passes.
16. `success:false` envelope rejects.
17. Valid escaped JSON Pointer `/a~1b` resolves.
18. Adding a provider invalidates an existing prepared ticket.
19. Non-boolean registration evidence is rejected.
20. Invalid add-on JSON `$ref` fails during preparation.

These are synthetic schema and mocked-runtime tests using **the real** `DynamicCommands` class. They do not establish live third-party APX execution.

## Known defect expectations corroborated by Windows CI (8 XFAIL)

These tests assert the desired invariant and intentionally produce `expected failure` until the code is corrected. A green CI **does not mean** these invariants already hold.

### A. NEW: non-atomic failed provider registration

Test: `test_known_gap_failed_duplicate_registration_is_not_atomic`.

- Register `AddOn.Vendor.Call` with `#/Payload` requiring integer `amount`.
- Submit a duplicate command with conflicting `Payload` requiring string `amount`.
- The call correctly raises `PROVIDER_COMMAND_DUPLICATE`, **but the implementation has already overwritten `catalog['common_schemas']['Vendor__Payload']`** before checking the duplicate command.
- The catalog no longer equals its previous snapshot; `fingerprint` still reflects pre-failure catalog. This can poison subsequent preparation with drift failures.

**Fix:** perform complete duplicate validation of provider qualified command IDs and schema IDs before committing *any* mutation. Stage updates and recalculate fingerprint only after an atomic successful registration.

### B. NEW: namespace collision can silently retype an earlier provider

Test: `test_known_gap_ambiguous_schema_namespace_collides`.

- Provider namespace `A__B` declares common schema `C`, stored as `A__B__C`; command `AddOn.A__B.Call` expects integer `amount`.
- Provider namespace `A` declares common schema `B__C`, which maps to **the same key** `A__B__C`; its schema expects string `amount`.
- The second `add_provider` succeeds and silently replaces the first provider's schema. Its previously valid integer contract no longer validates.

**Fix:** use a collision-resistant namespace-to-schema mapping or reject collisions **before** updating existing schemas. Include provider identity in stable schema keys; do not silently alter existing contracts. This is important for integrating many independent APX modules.

### C. NEW: schema-side pointer accepts a nonabsolute path

Test: `test_known_gap_nonabsolute_schema_pointer_accepted`.

`_schema_at({'type':'object','properties':{'a':{'type':'integer'}}}, 'a')` accepts `a` although `_result_at()` rejects nonabsolute pointers. Preparation/runtime semantics are inconsistent. Apply common RFC 6901 validation to both.

### D. PREVIOUS: five still-open defects

1. Empty-member JSON Pointer `/a/` incorrectly resolved.
2. Noncanonical negative array index `/arr/-1` incorrectly accepted.
3. Unlisted `ownerWallId.guid` is omitted by `target_ids` and not rejected by the scope (this does **not** prove an actual unauthorized native write; SceneWriter checks still operate).
4. Valid successful result with nullable `error` is falsely rejected.
5. `_schema_example({'type':'integer','maximum':0})` emits an invalid placeholder.

Full earlier isolated scenarios and restoration/metadata reviews: [research PR #86](https://github.com/dvikt33-ux/safe-bim-layer/pull/86).

## Priority recommendation (separate from Work's feature development)

1. **P1 for multi-APX expansion:** atomic registration and collision-free common schemas (new issues A, B). Otherwise adding multiple providers may poison unrelated contracts.
2. **P1 for mutating operations:** fail-closed GUID target extraction and explicit scope semantics (existing issue D.3).
3. **P2:** shared pointer grammar and schema-placeholder correctness (C, D.1, D.2, D.5).
4. **P2:** response/error-envelope correctness (D.4), provenance and result schema coverage.

Work should proceed with SDK/APX integration in its separate branch. No regression test here removes or replaces previously verified safety gates. No large, repetitive offline regression suite was created. Merge/admission of QA findings into the canonical plan requires existing plan claim/lease/CAS approval and exact published-source review.
