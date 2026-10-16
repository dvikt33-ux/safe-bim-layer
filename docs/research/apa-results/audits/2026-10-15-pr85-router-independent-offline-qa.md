# APA independent offline QA — router edge cases / APX provider consistency

- Date: 2026-10-15
- Audited feature PR: [#85](https://github.com/dvikt33-ux/safe-bim-layer/pull/85)
- **Exact source head:** `45ef6b734e70c0e2c40ea57ed9a0099d70c4a917`
- Canonical project plan at audit: revision 162; `APA-P70.A11.S03` = `PARTIAL`.
- **Mode:** read-only GitHub source retrieval, independent isolated execution of the published Python algorithms with stubbed collaborators, real jsonschema validation, manifest inspection. **No Archicad calls, no native PLN/APX write, no change to Work's development branch.**
- Caveat: full original Python repository was not locally cloned in this test environment; targeted isolated functions were transcribed from the exact GitHub source. Counts below are **not** full-repository test counts, and no isolated failure implies a tested LIVE Archicad failure.

## Existing Windows CI independently verified (not rerun)

At exact SHA, [Actions run 38643318495](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38643318495) is SUCCESS, **741/741** APA tests, **102/102** upstream Knowledge Graph tests, stdio MCP integration PASS. Its test suite is not exhaustive for deliberately hostile or unusual schema inputs.

## Focused isolated tests: 46 cases total, 27 expected outcomes, 19 deviations

| Subsystem | Cases | Expected behavior matched | Deviations | Evidence |
| --- | ---: | ---: | ---: | --- |
| `DynamicCommandRouter.scope` explicit GUID target invariant | 5 | 4 | **1** | unlisted target GUID filtered out |
| `validate_result` success/error envelope | 7 | 4 | **3** | permitted nested `error` data treated as failure |
| `_result_at` JSON Pointer / RFC 6901 | 13 | 7 | **6** | empty tokens, array-index grammar, escape grammar |
| `_schema_example` + jsonschema 4.26 | 12 | 4 | **8** | invalid placeholder for bounded legitimate schemas |
| `run_workflow` after successful mutation, bad later binding | 1 | 0 | **1** | raises IndexError, last success checkpoint retained |
| 33-APX provider registry invariants | 8 | 8 | **0** | see details below |

These are intentionally selected **edge cases**, not a statistically representative reliability score. Tests of existing successful Wall/Window behavior are not repeated.

## Finding A: scope accepts a GUID not in affected or retained (medium; invariant failure, downstream exploit NOT proven)

Source: `scripts/archicad_dynamic_commands.py`, `scope()`, around lines 222–239.

The inner `target_ids` yields a direct dictionary `guid` **only when that GUID is already in** `affected ∪ retained`. Thus the subsequent condition `set(target_ids(params)) <= set(affected)` cannot see an unlisted direct GUID. Example with synthetic IDs:

```python
affected = []
retained = ['11111111-1111-4111-8111-111111111111']
params = {'windowsData': [{'ownerWallId': {'guid': '22222222-2222-4222-8222-222222222222'}}]}
# scope() => ACCEPTED, expected: reject unknown ownerWallId target
```

Control cases: host in affected = accepted, host in retained = rejected, `elementId.guid` outside scope = rejected, targetless create = accepted. **4/5 PASS, 1/5 FAIL**.

The existing SceneWriter independently checks complete current inventory and protects retained signatures, reducing consequences for elements inside the enumerated PLN. The test **does not prove** an unauthorized native write. Nevertheless, effect-scoping must fail closed for an element target outside the permitted inventory; review non-`elementId` target shapes such as `ownerWallId` using provider schema field semantics rather than filtering by the allowlist being tested.

## Finding B: valid responses with error data falsely rejected (medium for generic provider support)

Source: `validate_result()`, around lines 211–220. The recursive `errors(v)` returns failure as soon as a dictionary *contains* an `error` key, regardless of its value or whether the key is legitimate data.

Source-exact isolated validation tests (schema allows the payload):

- PASS: `{'success': True}`, `{'success': False}` (rejected), `{'error': {'code': 'bad'}}` (rejected), nested `{'items':[{'success':False}]}` (rejected).
- **FAIL:** `{'success': True, 'error': None}` rejected.
- **FAIL:** `{'success': True, 'error': ''}` rejected.
- **FAIL:** `{'success': True, 'measurements': [{'error': 0.0}]}` rejected.

Distinguish actual provider error envelopes and `success:false` from nullable/empty error fields and legitimate measurement data. Do not suppress actual nested failures. The recorded 262-command Tapir snapshot does not itself show an `error` return field in the scanned inline command returns; relevance to new providers is prospective.

## Finding C: RFC 6901/array pointer cases (medium; also in earlier PR85 review)

Source: `_result_at()` and `_schema_at()`, around lines 310 and 269. Both use `pointer.strip('/').split('/')`.

13 isolated runtime cases: PASS for `''` root, `/a/b`, `/a~1b`, `/a~0b`, `/arr/1`, rejection of out-of-range `/arr/10`, and rejection of nonabsolute `a/b`. FAIL for:

- `/a/` and `//a` — significant empty property names silently lost.
- `/arr/01`, `/arr/+1`, `/arr/-1` — invalid array-index grammar accepted; negative index wraps from the end.
- `/a~2b` — invalid tilde escape accepted.

**7/13 matched, 6/13 deviations.** Additionally, `_schema_at()` accepts nonabsolute `a/b` while `_result_at()` rejects it: a prepare/runtime contract mismatch. Fix both readers consistently; preserve the first slash, reject forbidden escape/index grammar. The known successful 17-step model workflow did not use these pointers.

## Finding D: placeholder synthesis does not satisfy legitimate JSON Schemas (medium)

Source: `_schema_example()`, around lines 291–306. 12 source-exact synthetic examples validated using `jsonschema.Draft202012Validator` with format checking:

**4 PASS:** string enum, valid-format UUID, integer with minimum 8, unconstrained array.

**8 FAIL** examples:

1. `{"type":"string","minLength":30}` → `"schema-placeholder"` too short.
2. `{"type":"string","pattern":"^[A-Z]{3}$"}` → unmatched placeholder.
3. `{"type":"integer","maximum":0}` → 1.
4. `{"type":"number","exclusiveMaximum":0}` → 1.
5. `{"type":"array","items":{"type":"integer"},"maxItems":0}` → nonempty array.
6. Required object property with `minLength:30` → too-short nested placeholder.
7. `oneOf:[{"type":"null"},{"type":"number","maximum":0}]` → 1 invalid.
8. `{"type":"array","items":{"type":"string"},"minItems":0,"maxItems":0}` → nonempty array.

This is a generic dataflow planner defect, not evidence of a failed real Roof operation. Prefer typed **symbolic result references** until concrete producer data exists, or implement a bounded schema-respecting placeholder strategy.

## Finding E: late resolution failure after successful write lacks structured STOP (medium)

Source: `run_workflow()`, around lines 339–367.

Isolated two-step workflow: first `Write` returns `{'elements':[{'id':'GUID-NEW'}]}` with PASS; following consumer dereferences `/elements/2/id`, which is missing.

Observed: **IndexError** propagates from `resolve()`; one prior `WORKFLOW_CHECKPOINT` exists confirming completed write, but no final structured `STOPPED_...` response or failure checkpoint is emitted. No automatic retry was observed in this isolated harness, and there is **no evidence the SQLite journal is lost**.

Recommendation: handle post-write resolution/validation exceptions as a safe, recoverable partial-workflow stop with complete completedSteps, error classification and `automaticRetry:false`. Never implicitly retry completed creates.

## Finding F: effect-policy supplemental requirements not directly consumed by inspected executors (review item, not a proven permission bypass)

`operation-effects.json` has `confirmationRequired`, `saveRequired`, `verification`, `affectedData`, `possibleSideEffects` metadata on exactly **49** newly classified commands. In the inspected files `archicad_dynamic_commands.py`, `archicad_scene_run.py`, `archicad_project_accelerator.py`, `apa_executable_bim_smoke.py`, these exact keys were not referenced as gates; the router uses kind, impact and separate operation-specific before/after callbacks. This is **not proof** of unauthorized execution because an external authorization layer and SceneWriter still operate. It is a follow-up test: demonstrate that requirements for UI/process/external/transaction commands are actually enforced at the appropriate layer, not merely present as advisory text.

## APX / DevKit provider registry: 8/8 structural PASS

At the audited SHA, `schemas/accelerator/mass-capabilities/providers.json`:

- 33 unique provider records; all have SHA-256-shaped identifiers.
- Exactly one provider marked INTEGRATED (Tapir).
- All other listed modules declare zero *independent* discovered JSON user commands.
- 28 statuses NOT_EXPOSED have explicit reasons; four non-Tapir providers have limited indirect/MEP/IFC accessibility.
- The 848 public SDK function names and 14 DevKit examples are counted separately, not promoted to registered JSON commands.
- These are catalog consistency checks, not tests of each APX executable or its undocumented C++ ABI.

## Suggested narrow corrections; do not block new module integration

Priority order for next code patch:

1. **A:** fail-closed target extraction for `MODEL` mutations, using schema-aware owned/target semantics and exact inventory.
2. **E:** structured partial stop after a downstream binding error.
3. **B/C/D:** common result-envelope, JSON Pointer and dataflow schema-placeholder correctness (small focused tests only).
4. **F:** trace supplemental effect metadata to actual permission gates; demonstrate without weakening current SceneWriter checks.

New SDK/APX integrations may proceed independently while these regressions are reviewed. Do not repeat 741 unchanged tests on the laptop; independent Windows CI and focused cases remain sufficient for offline work. The full linkable audit report belongs to this research PR; downstream acceptance into canonical task plan requires separate existing CAS/lease review.
