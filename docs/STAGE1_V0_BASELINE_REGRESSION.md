# Stage 1 — v0 baseline regression

**STAGE 1: PASS** (live run, 2026-10-05).

Execution commit: `f8b82ed3008c4669faf1424958b30f43aa4b5d92` on the unchanged v0 path from baseline `565ea2e0414a14bedbca09999690d7b97f877fa3`.
Evidence branch: `work/stage1-v0-regression`, based on `chatgpt/closed-loop-orchestrator-v1`.

Tested open PLN: `NativeGeometry_Full_Test_20261004.pln`. Full identity is in the report and native identity responses. Archicad 29 build 3000 RUS; Tapir 1.5.10; localhost port 19723.

| Iteration | Automatically selected source GUID | Created GUID | Length, m | Joint distance, m | Elements |
| --- | --- | --- | --- | --- | --- |
| 1 | F69C0FEC-34FF-4982-8CE8-127D7DAED89D | B18F8EA4-8D47-4FAE-9373-E830DBEA3CF4 | 1.0 | 0.0 | 5300 → 5301 |
| 2 | B18F8EA4-8D47-4FAE-9373-E830DBEA3CF4 | CE093166-FF7B-420E-B991-1D0CE0D5CCAE | 0.5 | 0.0 | 5301 → 5302 |

Both created Walls were physically created and observed in post-mutation native dumps. Home story is 0; tolerance is 1e-7 m. Planner status is PLANNED; executor and read-back are PASS for both iterations.

Iteration 2 obtained a new live dump and automatically chose the first created GUID. The scratch runner compared this selection with iteration 1 before invoking the baseline adapter; the adapter then performed its own fresh planning read and execution. No source GUID was supplied manually. The resulting identity equality is machine-checked in the report. No manual model corrections, cleanup, or retries occurred; both Walls remain in the live model. No PLN save command was issued.

## Acceptance criteria

All required criteria C01–C18 are PASS; required FAIL = 0, NOT_VERIFIED = 0. The JSON report records expected, actual, verdict and evidence for every criterion.

## Evidence

- [Machine-readable report](../outputs/closed-loop-stage1/v0-regression-report.json)
- [SHA-256 manifest](../outputs/closed-loop-stage1/evidence-manifest.json)
- [Iteration 1](../outputs/closed-loop-stage1/iteration-1/summary.json)
- [Iteration 2](../outputs/closed-loop-stage1/iteration-2/summary.json)
- Native CreateWalls request/response pairs, planner requests, compact source/created read-back witnesses, identity responses and metrics are committed alongside the report.
- Full normalized dumps and native dump responses (~100 MB each) are retained locally at the exact paths and hashes in the manifest. They are excluded locally through `.git/info/exclude`, and are not available from GitHub alone.

## Code and Git discipline

No runtime code changes were required. `git diff 565ea2e0414a14bedbca09999690d7b97f877fa3 -- scripts archicad-addon` is empty. Main remained `72e9be15ac3b943d7b6f0c46eaa45aa5798d56bc`. The original dirty checkout was preserved. Only evidence and this completion note are committed.

## BACKLOG / NOT PART OF STAGE 1

Stage 2 and later stages require independent audit and a separate task. No orchestrator, new BIM capability, UI, refactor or optimization was implemented. There are no open Stage 1 blockers.
