# APA — independent offline full sweep of PR #82 (2026-10-14)

**Task:** APA-P70.A11.S03 — independent verification only; no task claim or status mutation.

**Frozen production snapshot:** PR #82, commit `3ad9961ccb91c64e4ef5828f951f56f56b63daee`. 
**Isolation:** test branch `feature/apa-connected-independent-offline-20261014`, rooted at that exact SHA. The test branch changes CI/checks only, not any APA product code. Live Archicad/PLN/APX calls **0**.

## Actual independently executed tests

1. [Full Windows + Linux CI](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38587528008): **SUCCESS**, committed test-only workflow `bbc2a26e4d16545ab257349641db9557c1dfb8d5`.
   - Ubuntu: **730/730** discovered APA `test_archicad_*.py` tests PASS; **102/102** knowledge-graph tests PASS; **9-scenario** live-stdio-MCP *offline integration* smoke PASS; graph example/schema audit PASS; all test workflow PowerShell parse checks PASS; Python scripts and graph-tool compileall PASS.
   - Windows: equivalent full workflow SUCCESS, **730/730** APA and **102/102** knowledge-graph tests PASS, full schema/graph/PowerShell checks PASS.
   - These are **offline CI** results, not native Archicad live tests.
2. **Independent controller structural assertions** against published revision **156**: 91 tasks, task key/ID/status checks, all dependency targets present, acyclic task dependency graph, all active task claims have owner/lease/ref, **296/296 evidence references registered** in 272 artifacts, 21 candidate-catalog entries with valid target tasks. No errors detected. The in-progress A11.S03 owner/lease was preserved; no controller write.
3. **Independent JSON parsing:** exact PR82 snapshot had **77 JSON files**, **77/77 valid** using JSON.parse/fetch by exact source SHA.
4. [All-tracked-file static audit](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38588470112), test-only workflow `f994e388314ab671778eae5d3c6f3355216c7250`:
   - **167 Python .py files passed AST syntax**.
   - **77 JSON files parsed**.
   - **108 YAML files parsed**, but **three historical research YAML files were malformed**. Overall job **FAIL** — do not claim a global all-green sweep.

## Independently detected historical source-data issues

1. `docs/research/integration-candidate-matrix-v1.5.yaml`, lines **172–178**: `view_hierarchy` is introduced as a YAML sequence, followed by `escalation_only_if_unresolved_information: true` at the same child indentation. YAML parser rejects mixed sequence/map structure. A qualified fix should explicitly separate ordered steps from the additional boolean key.
2. `docs/research/integration-candidate-matrix-v2.1.yaml`, lines **91–104**: `repair_hierarchy_room_fit` likewise mixes sequence items with `require_lower_level_infeasibility_before_escalation: true` at the same child level. Requires normalized mapping/sequence representation.
3. `docs/research/layer-reuse-decision-matrix-v0.8.yaml`, **line 1**: embedded literal backslash-n sequences `\\n` in the first physical YAML line instead of actual line feeds. YAML scanner error. Must check provenance and preserve the original historical bytes when publishing a corrected derivative.

**Scope:** these are historical research documents, not observed runtime BIM regressions. Their machine-readable ingestion is unreliable until corrected; avoid using them as asserted validated YAML. Raw originals were not edited or deleted.

## Explicit boundaries

- No Archicad 29 host, installed APX/SDK, local authorized test PLN or C++ build is available to this independent offline test runner. Native geometry, roof edits, Stair, MEP connectivity, source engineering/structural adequacy, UI, and installed APX **NOT_RETESTED** here.
- Offline PASS applies to the **frozen PR82 product snapshot**, not to any subsequent live modifications by Work.
- The test branch is separate from PR82 and other Work development branches. `main/master`, original source YAML, PLN, APX and the controller task statuses remain unchanged.

## Recommended handoff

Work can incorporate these three factual YAML findings into existing APA-P70.A11.S03 / source-ingestion follow-up when relevant, without repeating 730+102 tests. Preserve original research files, add a corrected validated derivative or a provenance-safe repair in a separate PR. Keep native acceptance independent.

**Evidence:** CI Windows/Linux `38587528008` SUCCESS; static source audit `38588470112` FAIL (3 documented YAML); independent parsed plan revision 156; branch heads `bbc2a26e4d16545ab257349641db9557c1dfb8d5` and `f994e388314ab671778eae5d3c6f3355216c7250`.
