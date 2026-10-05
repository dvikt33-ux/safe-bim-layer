# Stage 2 — offline orchestrator skeleton

Starting point: Stage 1 `27fc10267e71d1cd4f8322fe1d3c334e2cef1b4c` (VERIFIED / PASS).
V0 baseline: `565ea2e0414a14bedbca09999690d7b97f877fa3`.
Working branch: `work/stage2-orchestrator-skeleton`.

## Working user scenario

From the repository root, using Python 3.11 and the standard library:

```powershell
python -m closed_loop.demo --output work/stage2-demo-new-job.json
python -m unittest discover -s tests_stage2 -v
python -m tests_stage2.verify --output work/stage2-verification-new-run
```

Use a new output path for each run. Existing job evidence is preserved and cannot be restarted implicitly. The runner has no Archicad connection, live executor adapter, command dispatcher or automatic stage progression. Every injected component must declare `offline = True`, and observations/results must identify fixture/offline provenance. The supplied mocks perform only in-memory operations. This interface marker is an injection contract, not a sandbox for arbitrary Python code.

The demo receives one goal and acceptance contract, observes an initial fixture, asks the typed planner for one action, records the mock execution, obtains a separate read-back fixture, computes the audit and finishes VERIFIED. This verifies Stage 2 orchestration behavior, not physical BIM creation.

## Components and contract

- `closed_loop/models.py`: Goal/Job, acceptance contract, typed Action, planner/executor results, observation/facts, per-criterion audit, iteration and evidence records.
- `closed_loop/orchestrator.py`: separate Observer, Planner, Executor and ReadBack protocols; legal transitions; required-criterion decision; explicit iteration limit; persisted JSON job.
- `closed_loop/auditor.py`: factual evidence comparison. Numeric scalar checks use absolute tolerance; other JSON values use exact JSON equality. A missing check is DATA_MISSING. Unsupported/unretained evidence cannot yield PASS. Supplied NOT_VERIFIED, DATA_MISSING, CONFLICT and BLOCKED_BY_TRANSPORT facts keep that verdict even when their numeric value matches the expected value.
- `closed_loop/mocks.py`: deterministic fixture interfaces with call counters.
- `examples/closed-loop-stage2/acceptance-contract.schema.json`: machine-readable input contract. Runtime also enforces unique IDs and finite JSON values.

Each input criterion contains `id`, `required`, `check`, `expected`, optional `tolerance` and `correctable`. Actual, verdict and evidenceRefs are computed in audit results; callers cannot supply PASS as fact provenance. A correctable FAIL is explicit contract input, not a guess by the orchestration layer.

The Job stores goalId, original specification, acceptance criteria, state, iteration, timestamps, observed model identity/hash, actions, audit history, finalStatus, terminal reason and execution provenance. Each iteration stores stateBefore, observation, plannerDecision, executorRequest, executorResult, readback and auditResult. Incomplete fields remain null on a blocked/unknown attempt; the terminating transition retains the reason. Observation evidence payloads are retained inside the snapshots, so references are inspectable. Inputs to injected interfaces and their returned snapshots are copied to prevent later mutation of retained evidence.

The JSON snapshot is saved before the mock execution call, after each transition, and on terminal decisions. It retains the full ordered evidence trail. Stage 2 does not implement restart/resume or reconciliation.

## State machine and decisions

`RECEIVED → OBSERVING → PLANNING → EXECUTING → READING_BACK → AUDITING`

| Condition on required criteria / result | Decision |
| --- | --- |
| Every required criterion PASS, recomputed from retained read-back | VERIFIED |
| Only correctable FAIL remains | REPLANNING → PLANNING (REPLAN decision) |
| DATA_MISSING | WAITING_FOR_DATA |
| NOT_VERIFIED, CONFLICT, BLOCKED_BY_TRANSPORT, uncorrectable FAIL | BLOCKED |
| Executor result is ambiguous, or read-back unavailable after an attempted mock mutation | UNKNOWN_OUTCOME |
| Iteration limit reached with unresolved criteria | BLOCKED |

Evidence deficiencies take precedence over corrective replanning. Optional criteria remain visible in the audit but do not close the required gate. Executor PASS without mandatory read-back cannot finish VERIFIED. A read-back for another model identity is blocked.

All terminal states reject outgoing transitions and repeated run calls. UNKNOWN_OUTCOME has no automatic retry or retry/resume API. Illegal transitions, including BLOCKED → VERIFIED, are rejected before state changes. VERIFIED recomputes the latest audit against retained read-back and the original contract before accepting the transition.

## Verification and evidence

**STAGE 2: PASS — offline only.**

The deterministic test suite covers the working scenario, all declared legal graph edges, all illegal edges, all terminal states, every auditor verdict, replanning on new fixture state, iteration exhaustion, missing evidence, missing read-back, executor timeout, malformed interface results, identity mismatch, numeric tolerance, contract validation, preserved snapshots and persistence before execution. Network access is forbidden in the end-to-end fixture tests.

The saved acceptance run contains 33 passing tests and 8 scenarios:

- [Verification report](../outputs/closed-loop-stage2/acceptance/stage2-verification-report.json)
- [Unit test output](../outputs/closed-loop-stage2/acceptance/unit-tests.txt)
- [Working demo job](../outputs/closed-loop-stage2/mock-job.json)
- The same verification folder contains full job trails for VERIFIED, REPLAN, NOT_VERIFIED, DATA_MISSING, CONFLICT, transport failure, UNKNOWN_OUTCOME and iteration-limit scenarios.

Stage 1 evidence is retained unchanged. No new live Archicad call or mutation was made. Existing scripts, native add-on and v0 runtime files are byte-identical to Stage 1; the preserved Stage 1 live PASS is not represented as a new live run.

## BACKLOG / NOT PART OF STAGE 2

Stage 3 live integration requires a separate task. Live adapters, reconciliation/resume, deeper stale-model/no-progress handling, new BIM intents/types, UI, normative rules and performance work remain outside this implementation. There are no open Stage 2 blockers.
