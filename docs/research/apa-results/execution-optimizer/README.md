# APA execution optimizer — Fast Downward (preview-first)

**Status:** adapter committed for review, not installed into the running local APA
source folder, not enabled as an automatic router, and not LIVE-tested against
Archicad. The external solver package *was* installed and smoke-tested locally
by the user in `%LOCALAPPDATA%\APA\planner-venv` on Windows (Python 3.11,
`unified-planning==1.3.0`, `up-fast-downward==0.5.2`).

## Boundary

The new `scripts/archicad_execution_optimizer.py` is the **decision-only**
adapter. Every alternative must already be specified as an ordinary
source-qualified BIM Graph workflow accepted by existing
`DynamicCommands.prepare_workflow`, using reviewed native commands only.
Each candidate declares a positive **total estimated completion time in ms**,
native API call count, and a cost-evidence reference. Those estimates are
untrusted input and require independent calibration; the selector cannot
establish their truth just from the supplied string.

The installed Fast Downward engine solves a cost-optimal one-step choice
among these **complete strategy alternatives** and returns the selected
strategy. Ties are resolved by native call count and stable index. It does
NOT automatically discover strategies, interpret construction drawings,
produce BIM geometry, plan an arbitrary multi-action domain, or grant
execution permission. Those extensions require separate source contracts.

Host APA imports no `unified_planning` dependency. It invokes
`planner-venv/Scripts/python.exe` in a restricted worker subprocess.
On solver failure: FAIL CLOSED (no heuristic fallback and no native write).

Selected strategies are prepared again via
`archicad_project_accelerator.prepare_native_task(schemaVersion=apa-native-task/1)`.
A separately explicitly authorized
`archicad_project_accelerator.run_optimized_native_task()` uses the **same
old** `run_native_task -> DynamicCommands.run_workflow -> SceneWriter` path.
No competing Archicad writer, transport, implicit model save, automatic retry,
or mutation of an active PLN is added.

## Python integration entry point

```python
from archicad_project_accelerator import prepare_optimized_native_task

intent = {
    "schemaVersion": "apa-native-optimizer/1",
    "request": "Create a source-qualified set of repeated timber studs",
    "strategies": [
        {
            "id": "copy_batch",
            "graph": {"operations": [
                # Existing typed BIM Graph steps, source-qualified and
                # schema validated against the actual APA catalog.
            ]},
            "estimatedCostMs": 1307,
            "nativeCallCount": 1,
            "costEvidenceRef": "USER_NATIVE_MOVE_BDD_150_COPIES_20261016"
        },
        # At least one independently supported competing graph with
        # its OWN measured/estimated completion-cost evidence is required.
    ],
}
preview = prepare_optimized_native_task(router, intent)
# Inspection only. Do not call run_optimized_native_task without separate,
# source-qualified write authorization and configured SceneWriter scopes.
```

The price above is the measured **native transport time of 150 copies**,
not a measured end-to-end price of a different workload: real estimates
must include full verification and be workload normalized. No second
strategy's price has been independently measured yet.

## Local installation / activation status

Installed solver path: `C:\Users\Admin\AppData\Local\APA\planner-venv\Scripts\python.exe`.
Do **not** pip-install the solver into the existing Archicad MCP Python.
The new adapter code currently resides **only in this GitHub branch**;
the working local APA scripts remain unchanged until deployment.
Do not modify `main` or the Archicad work PLN as part of deployment.

## Tests

`tests/test_apa_execution_optimizer.py` checks that a synthetic batch
strategy beats repeated individual calls using a real Fast Downward solve,
that an alternative with fewer calls can still lose on time, fail-closed
behavior for unknown operations/missing evidence/solver failure, and the
original APA preview + run path. All example pricing is explicitly
**synthetic test data**, not a production benchmark.
