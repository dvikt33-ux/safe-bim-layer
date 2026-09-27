# Runtime hardening v1 — Phase H1 only (B1 adapter parity)

Baseline: `c55f404829e4e11004ea5c59c8b3aec18b663866` on historical
`arena/t0-probes`. Work branch: `arena/runtime-hardening-v1`, created directly
from that commit. **No production certification. No live execution authorised.**

## Scope and source of the contract

H1 removes the separate TEMPLATE protocol from `reference/bimexec/tapir_raw.py`.
It does not implement recovery, reconciliation, resume, a new Executor, an HTTP
service, or new BIM operation types. Production Router and legacy root scripts
are unchanged. Historical `bimexec/results/` files are byte-for-byte unchanged.

Contract sources at the baseline:

- `probes/backends_v13.py`: Tapir GetProjectInfo/GetStories/GetDetailsOfElements;
  official property utilities and typed property write items.
- `probes/probe_t2_connections_v13.py:129–169,268–293`: single-wall `wallsData`
  recipe/dispatch and wall observation. T3/T4/T5 already delegate to these helpers.
- `probes/probe_t2_live_v13.py`: historical T1 runner with the same wall wire recipe.
- `results/capability_matrix_v13_2.json`: raw wall observation and story mapping;
  `results/t0b_receipt_live_v13.json`: Element ID property round-trip.

These are historical sources, not proof of a new live run of H1. The final audit
limitations on their completeness continue to apply.

## One contract, two consumers

```
T1/T2 wall helpers ───────────┐
                            ├─ probes/ac29_contract.py (wall payload/dispatch/observation)
reference TapirRaw ──────────┘
          │
          └─ probes/backends_v13.py (read/property transport)
                   └─ existing backends.py connection and AC29 normalizer

Executor → ExecutorAdapter → TapirRaw
```

The shared module remains in `probes/` so the standalone probes do not import
Executor code. `TapirRaw` resolves this repository-local directory relative to
its own file; there is no machine-specific absolute path. Import/construction
is lazy and does not connect to Archicad. The full repository layout is required;
copying only `reference/` is not a supported installation.

The T0 mutation denylist is unchanged. The shared `create_wall_once` is a
single-command wire helper used only by explicit create callers, not by T0A/T0B.
It is not a write authorisation or recovery engine. Runtime still requires the
unchanged Executor capability/WriteGate/confirm gates. No capability file is
promoted and no production permission is added.

## B1 differences eliminated

| Baseline defect | H1 behaviour |
|---|---|
| Runtime official GetProjectInfo | Uses v1.3 Tapir `ExecuteAddOnCommand(TapirCommand, GetProjectInfo)`; official GetProductInfo remains optional metadata |
| Runtime official GetDetailsOfElements / wrong response parsing | Uses v1.3 Tapir `elements: [{elementId: {guid}}]` and `detailsOfElements`; error/empty/malformed result raises |
| Independent TEMPLATE CreateWalls | Deleted. Runtime and T1/T2 delegate to the same builder and single-call dispatcher |
| `walls` + nested `coordinates` | `wallsData` + direct `begCoordinate`, `endCoordinate`, explicit `floorIndex` |
| Default `story_index=0` / center reference line in ExecutorAdapter | Removed; bridge forwards only explicitly provided fields; raw resolves exact name+elevation to the actual returned index |
| Missing runtime thickness/story/layer read normalization | Shared T2-style observation: equal beg/end thickness, floorIndex→named story, official ModelView_LayerName property, reference-line endpoints |
| Count read error interpreted as 0 | Only a successful explicit empty array means 0. Transport/shape/error-row/empty-GUID failures raise; no partial count result |
| Missing read interpreted as absence | Empty/error details, incomplete property dictionaries, failed list/filter/marker scans raise typed errors rather than None/[]/0 |
| Parallel marker property protocol | Runtime uses v1.3 official typed property read/write path and the tested General_ElementID carrier only |

`TapirRaw.AdapterUnavailable` subclasses `bimexec.adapters.AdapterError`.
The v1.3 backend normalizes read failures as `BackendError`; the runtime boundary
translates all ordinary transport/shape exceptions to the Executor error type.
There is no retry. A write exception or ambiguous write response is **unknown**,
never proof that the mutation did not apply.

The existing Executor can still let a typed count/detail PRECHECK exception
escape `run()` rather than journal a complete pause taxonomy. H1 verifies that
no transport write occurs; it does **not** fix that state-machine/recovery issue.
Similarly, story refusal occurs before the adapter's `CreateWalls` transport
call; the unchanged Executor may already have recorded its conservative INTENT.
H1 does not alter that WAL lifecycle.

## Deliberately narrow wall recipe

Runtime inputs must explicitly provide:

- `story: {name, elevation}` — name must match exactly (no stripping/renaming),
  elevation within `1e-6`; exactly one mapping must resolve, with a real integer
  index. Missing/duplicate index, missing/ambiguous story, failed stories read,
  wrong elevation, or conflicting optional `story_index` all refuse dispatch.
- Two finite 2D endpoints, nonzero segment length.
- `height: 3.0`, `thickness: 0.30`.
- `reference_line: CoreOutside`, `structure_type: Composite`.
- Explicit `composite_id` GUID. Runtime does not guess a composite or select one
  from the current tool/defaults. This is caller-supplied recipe identity, not a
  new composite capability certification.

The common payload is exactly:

```json
{
  "wallsData": [{
    "begCoordinate": {"x": 1.5, "y": 2.5},
    "endCoordinate": {"x": 6.5, "y": 2.5},
    "floorIndex": 0,
    "zCoordinate": 0.0,
    "height": 3.0,
    "thickness": 0.3,
    "offset": 0.0,
    "arcAngle": 0.0,
    "referenceLineLocation": "CoreOutside",
    "structureType": "Composite",
    "compositeId": {"guid": "29EE690D-089C-4573-94C8-DEC75CFA0950"}
  }]
}
```

`floorIndex: 0` above is an **example resolved result**, not a default. Offline
regressions also use reordered stories/nonzero and negative indices to catch
an accidental array-position/index-0 fallback. They do not certify live writes
on additional storeys.

No Basic/profile/curved-wall support is invented. Nonzero base_level/offset/
arc_angle are refused. The historical wire recipe has no explicit `top_link`
field: runtime rejects a supplied `top_link` instead of silently ignoring it or
claiming that `absolute` was proved. Legacy fake plans remain valid for fake
adapters, but are not live runtime recipes.

No `layerName` is invented in CreateWalls. Historical probes wrote the layer in
a **separate** SetDetailsOfElements step. H1 does not add that second mutation to
runtime CreateWall: returned layer is read, and the unchanged verifier must
refuse a mismatch. There is no hidden layer/marker write after CreateWalls.

Before a runtime write, `TapirRaw` requires explicit `expected_project`, a
matching saved Solo project, and confirmed Tapir 1.5.9. A reported non-29
Archicad version is rejected; missing optional product metadata stays unknown,
not a fabricated version. These are adapter preconditions, not a claim that
all B4 instance/binding guarantees have been repaired.

## H1 offline regression coverage

`tests/test_h1_contract.py` uses a command-spy connection, the stored T0 raw
observation, and a **fixed golden payload transcribed from baseline**, independent
of the new builder. Socket creation is blocked in each H1 test.

24 registered tests cover:

- Complete emitted payload equality through ExecutorAdapter→TapirRaw and both
  probe wrappers; all six T2 segments; no official project/details methods.
- Details request/normalization, optional GetProductInfo, explicit empty counts.
- Count/list/detail/property timeout, malformed/error/empty/partial results;
  no negative matches produced by unavailable reads.
- Story name+elevation/index resolution, missing/ambiguous/reordered mapping,
  wrong elevation and conflicting indices.
- Wrong project, untitled/teamwork/unknown identity flags, absent expected
  project, wrong/missing add-on version: zero write calls.
- Rejection of missing recipe fields and unsupported wall semantics.
- Unknown write response: exactly one CreateWalls call, no retry.
- Read-only discovery and unchanged T0 denylist.
- Actual Executor PRECHECK with injected count/details/project failures:
  no underlying mutation dispatch. These tests reuse an existing synthetic
  capability fixture only; no report/certification flag is created or changed.

`test_all.py` now registers H1 alongside the existing tests. The unrelated v1.3
shim regression's old superclass monkeypatch was replaced with a per-instance
wire-response stub (same blank-story rejection assertion, no global patch leak).

### Commands and measured results

All commands run offline in Arena, not on Windows/Live Archicad:

- `python3 bimexec/tests/test_all.py`: **117 PASS, 0 failures** (93 existing + 24 H1).
- `python3 bimexec/tests/test_h1_contract.py`: **24 PASS, 0 failures** independently.
- `python3 bimexec/tests/test_probe_v13.py`: **5/5 PASS**.
- `python3 bimexec/tests/selftest_probes.py`: **62/62 PASS**.
- `py_compile` of all 55 repository Python sources: **55 PASS, 0 failures**.

These are offline source/contract regressions, not repeated live T0–T9 runs.
No historical result is reclassified or overwritten. Offline logs and source SHA-256 hashes are committed separately in
`tests/h1_evidence/`; the final commit SHA is delivered in the H1 handoff.
Historical `results/` is untouched.

## TODO — B2–B7 explicitly NOT closed by H1

| Blocker | Deferred work / continuing limitation |
|---|---|
| B2 | Proof-carrying reconcile/resume, candidate transfer, verify-before-ADOPT, human token and durable decision replay |
| B3 | Full crash-window recovery, intermediate states, OP_VERDICT replay, binding/dependency/geometry-hash restoration |
| B4 | Executor mapping/tag-guard/newness/provenance guarantees and generic per-mutation identity/host revalidation. Adapter-specific preconditions here do not close B4 |
| B5 | Full strict schema/immutable plan, bounded tolerances, full wall semantics verification, exact full count delta and cross-path agreement |
| B6 | Runtime invalidation enforcement, unknown layer state policy, service singleton/concurrent intake/HTTP boundary |
| B7 | Legacy root safe_bim_layer.py empty-readback false PASS and direct integration/write paths |

`executor.py`, `verify.py`, binding/journal/states/lock, recovery/reconcile/resume,
legacy root scripts, production Router, and capability results/schema are not
modified. **CreateWall and CreateOpening remain blocked for production.**

Stop after H1. Do not start H2 without a new instruction.
