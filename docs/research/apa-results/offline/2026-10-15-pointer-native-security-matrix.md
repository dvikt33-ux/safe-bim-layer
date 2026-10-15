# APA continued parallel offline tests — native request contracts, result pointers, cross-domain graph, Shell C++ source gates

Status: CI_RETRY_RUNNING / PASS_NOT_YET_VERIFIED. Initial [Actions #38736049083](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38736049083) identified 32 rejected-input cases not rejected by the production JSON Pointer planner. Patched the existing planner and runtime resolver to reject relative pointers, invalid RFC 6901 escape sequences and noncanonical array indexes. Full verification requires a new JUnit readback.

Based on draft PR #102 code head `2e93c10925a3c5d9ffc90a2b578cdb4c2f4e43d6`. Separate isolated branch. Existing Windows 12-way x 2-worker runner automatically discovers `tests/test_*.py`.

New tests target actual source contract validators (192), result JSON Pointer escaping and local-only typed result workflow (128), combined Opening/Navigator/assembly dependency graphs (64), C++ Shell class/contour serialization **source inspection only** (16). Total 416 planned tests (existing: 1922; candidate full matrix: 2338), including 16 direct runtime JSON Pointer resolver regressions.

Fail-closed policy: malformed pointer encodings and ambiguous identities must be rejected without Archicad transport. If a defect is found, keep original failed CI evidence; patch the smallest existing adapter and rerun. Do not add an additional geometry executor, writer, or scheduler. C++ source inspection is not an SDK compilation or runtime test.

All new cases are synthetic offline or source-only; not a verified Archicad Shell BREP. Publish separate full JUnit evidence to the canonical research hub via draft PR pending independent audit. No main or active PR branch updates.
