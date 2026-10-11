# APA — independent archive-71 traceability audit (isolated, no Work interference)

**Date:** 2026-10-12 (owner local date)  
**Mode:** GitHub read-only source assessment; documents added **only** to the separate branch `research/apa-archive71-traceability-isolated-gpt6-20261012`.  
**Baseline:** pinned canonical `deb98dee6cb489a628d78bb952cfa76896aa20c0`, `PROJECT_PLAN.json` revision **93**.  
**Relevant existing tasks:** `APA-P00.A02.S03` (PARTIAL), `APA-P50.A01.S01` (PARTIAL), `APA-P50.A03.S01` (READY), `APA-P70.A01.S02` (READY).  
**Task claim:** NONE. **Publisher V2 receipt:** NONE; a draft PR is not an immutable V2 publication.  
**Source:** [ARCHIVE_MANIFEST_20261011.json](https://github.com/dvikt33-ux/safe-bim-layer/blob/deb98dee6cb489a628d78bb952cfa76896aa20c0/docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/ARCHIVE_MANIFEST_20261011.json) and original [Tapir 1.5.9-era archive source commit](https://github.com/dvikt33-ux/safe-bim-layer/commit/c651035ddc77869fbc5a04bf23170b4f1188a9ab).  
**Machine result:** [ARCHIVE71_TRACEABILITY_GATES.json](ARCHIVE71_TRACEABILITY_GATES.json). Original files and current Work source code are *not* modified.

## 1. No duplicate archiving and no Work overlap

The canonical research branch **already contains all 71 source files, byte-identical**, under `docs/research/apa-results/source-archives/archicad29-tapir159-expansion-c651035d/`. The manifest, archive guide, [71-byte-exact publication receipt](https://github.com/dvikt33-ux/safe-bim-layer/blob/deb98dee6cb489a628d78bb952cfa76896aa20c0/docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-092155Z-source71-byte-archive/REPORT.md), and [Roof/Composite/Project Context report](https://github.com/dvikt33-ux/safe-bim-layer/blob/deb98dee6cb489a628d78bb952cfa76896aa20c0/docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-190658Z-roof-comp-context-map/REPORT.md) were read before this pass.

Parallel Work has a substantial active chain of PRs, notably [#51](https://github.com/dvikt33-ux/safe-bim-layer/pull/51) on native materials, composite/profile/surface edits and one Unicode GSM library object with user-local LIVE evidence. [Draft PR #49](https://github.com/dvikt33-ux/safe-bim-layer/pull/49) already covers the GDL factory source gap. Hence **no new GDL importer, Roof builder, composite writer, extra watcher, or Work-branch edit** is attempted or recommended as part of this isolated audit.

## 2. Measured traceability coverage

Direct JSON audit of the archive manifest against `PROJECT_PLAN.json` revision 93 gives:

| Measurement | Verified count |
| --- | ---: |
| Source MD/JSON entries in the archive manifest | **71** |
| Entries with one or more existing S-ID links | **70** |
| Entries with no S-ID | **1** (root `README.md`, informational index) |
| Entries whose *only* links are generic `APA-P70.A01.S02` and/or `APA-P50.A01.S01` | **29** |
| Higher-specificity routing **candidates** examined in this audit | **17** |
| Missing S-IDs among existing archive links | **0** |

All 70 linked source entries refer to controller task IDs that really exist. Therefore the issue is **routing precision, not missing files or orphaned source identifiers**. The 29 broad-only mappings are not invalid and should not be removed automatically.

## 3. Candidate routing matrix (review suggestions, never controller mutations)

| Pinned source file | Concern | Existing S-IDs to review for additional provenance routing | Priority |
| --- | --- | --- | --- |
| [`github_execution_job_v0_1.schema.json`](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/04_safe_bim_semantics/github_execution_job_v0_1.schema.json) | remote-job-admission | `APA-P40.A01.S01` (BLOCKED), `APA-P60.A02.S02` (DONE_PUBLISHED) | HIGH |
| [`DIRECT_GITHUB_EXECUTION_PASSES_161_170.md`](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/06_integration_audits/DIRECT_GITHUB_EXECUTION_PASSES_161_170.md) | remote-job-admission | `APA-P40.A01.S01` (BLOCKED), `APA-P60.A02.S02` (DONE_PUBLISHED) | HIGH |
| [`FINAL_TRANSPORT_SYNC_OUT_OF_BOX_AUDIT_AFTER_200.md`](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/09_final_audit/FINAL_TRANSPORT_SYNC_OUT_OF_BOX_AUDIT_AFTER_200.md) | transport-context | `APA-P40.A01.S01` (BLOCKED), `APA-P50.A03.S01` (READY) | HIGH |
| [`PROJECT_CONTEXT_BRIDGE_ARCHITECTURE.md`](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/06_integration_audits/PROJECT_CONTEXT_BRIDGE_ARCHITECTURE.md) | project-context-snapshot | `APA-P70.A01.S02` (READY), `APA-P50.A03.S01` (READY) | MEDIUM |
| [`AI_RESOURCE_EFFICIENT_ARCHITECTURE.md`](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/06_integration_audits/AI_RESOURCE_EFFICIENT_ARCHITECTURE.md) | resource-efficient-ai | `APA-P10.A03.S02` (READY), `APA-P50.A03.S01` (READY) | MEDIUM |
| [`INTERMEDIATE_AUDIT_UI_SANDBOX_AFTER_110.md`](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/06_integration_audits/INTERMEDIATE_AUDIT_UI_SANDBOX_AFTER_110.md) | undo-ui-sandbox | `APA-P50.A03.S01` (READY), `APA-P70.A01.S02` (READY) | MEDIUM |
| [`DEVELOPMENT_ACCELERATION_AUDIT.md`](https://github.com/dvikt33-ux/safe-bim-layer/blob/c651035ddc77869fbc5a04bf23170b4f1188a9ab/research/archicad29-tapir159/06_integration_audits/DEVELOPMENT_ACCELERATION_AUDIT.md) | development-priorities | `APA-P50.A03.S01` (READY), `APA-P10.A03.S02` (READY) | LOW |

The machine artifact contains exact Git blob SHA, source/archive paths, original S-IDs, suggested **additional** S-IDs, revision-93 task status, priority and reasoning for all 17 candidates. No `PROJECT_PLAN.json` task status, owner, lease, claim or evidence array was changed by this isolated branch.

## 4. Concrete acceptance risks discovered in the historical sources

**A. GitHub job transport is not runtime authorization.** The archived `github_execution_job_v0_1.schema.json` explicitly says its `signature` field is *reserved for future authenticated signatures, not required in v0.1*. The 161–170 execution research requires typed `SAFE_RECIPE` admission, separation from arbitrary `RAW_CODE`, fresh project hash and local authority. Current `APA-P60.A02.S02` (publisher plan claim gate) is `DONE_PUBLISHED`, but `APA-P40.A01.S01` (unattended authorized research runner) remains `BLOCKED`. Thus a source document or Slack event **cannot** be upgraded to permission for local BIM execution. The current Slack→SQLite user-local PASS certifies event import and deduplication, not remote-job integrity or native project writes.

**B. Cached context does not prove fresh model state.** Archived `project_context_snapshot_v0_1.schema.json` includes `snapshotId`, `rootHash`, Archicad instance and selected GUIDs; historical bridge research requires coherent model snapshot publication and fresh stale-plan checks. This is a **source-level candidate contract**, not a live installed bridge. Future `APA-P70.A01.S02` evidence synthesis should compare it with current SceneWriter and exact project identity; it must not start a second model watcher merely because historical notes propose one.

**C. Undo scopes differ.** The UI/Sandbox audit explicitly restricts “one stage = one native Undo item” to a custom C++ executor command scope; it does **not** prove that an arbitrary series of separate Tapir JSON calls is grouped into one Undo transaction. Historical private Safe BIM journaling is distinct from random-access restoration of the entire Archicad manual Undo stack. These remain integration guards for future UX, not claims about Work #51.

**D. Historical AI resource plan is advisory, not an executable dependency.** The archived 18-pass resource audit proposes `AI planner → validated typed plan → unload AI → native mutation/readback` so the local model does not compete with Archicad during critical writes. It contains no new machine benchmark for the current installed runtime. `APA-P10.A03.S02` (performance/cost comparison) and `APA-P50.A03.S01` (research synthesis) are appropriate existing review routes. **Do not launch another local LLM, change RAM/VRAM allocation, or interrupt Work** to validate the historical proposal.

## 5. Exact next steps after Work finishes

1. Reviewer of **existing** `APA-P50.A01.S01` / `APA-P50.A03.S01` can inspect the 17 candidate links for provenance routing, comparing against the *then-current* controller revision. Neither source S-ID memberships nor DONE claims may be changed just because this doc recommends a link.
2. For GitHub transport, test explicit job auth and model freshness as a separate security-bound source audit under the existing P40/P60 route. No new command producer or local listener is authorized by this report.
3. For context snapshot/Undo, compare existing native project identities and actual bounded Work receipts **after** Work's draft PR chain stabilizes. Reuse current code and avoid a second execution/monitoring stack.
4. If accepted by a designated controller auditor, integrate the traceability metadata in a short CAS-protected controller action with evidence; do not merge or auto-publish the draft research PR while Work is active.

## 6. Publication class and limitations

- **SOURCE_VERIFIED:** manifest counts, 70/71 coverage, all existing task IDs valid, 29 broad-only links, specific archived texts and pinned blob SHA, current task statuses at revision 93.
- **REVIEW_PROPOSAL:** 17 additional S-ID mapping candidates and prioritized follow-up gates.
- **NOT_VERIFIED:** actual current project-snapshot service, authenticated remote job intake, native Undo grouping across Tapir calls, current local AI resource savings, archival narrative's universal technical validity.
- **NO MUTATIONS:** `main/master`, canonical `research/apa-verified-results-hub-20261010`, Work PRs #34–51, `PROJECT_PLAN.json`, publisher inbox, Archicad, PLN, APX, Socket Mode and local SQLite remain untouched by this branch.

**Merge status:** DRAFT ONLY. The report is a standalone handoff for a later reviewer; it does *not* make `APA-P00.A02.S03` DONE, issue a V2 `DONE_PUBLISHED` receipt, or certify current Archicad BIM behavior.
