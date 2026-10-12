---
schema: TASK_PROPOSAL_V1
proposal_id: APA-CAND-20261013-knowledge-impact-gateway
origin: technical
proposer_run_id: APA-KNOWLEDGE-PR69-SOURCE-CI-20261013
source_substep_id: APA-P50.A01.S01
proposed_parent_plan: APA-P50
proposed_action: APA-P50.A01
suggested_substep_id: APA-P50.A01.S04
work_key: token-aware-readonly-document-impact-gateway
title: "Подключить проверяемый граф влияния документов к компактному поиску GPT"
kind: INTEGRATION
priority: 0
depends_on: [APA-P50.A01.S01]
related: [APA-P50.A01.S03, APA-P70.A02.S02]
inputs: [ART-REGISTER]
outputs: ["Read-only search gateway with pinned field provenance and token benchmark"]
acceptance: "Pass independent negative source/ACL/source-class tests, at least one primary-source-verified field-to-calculation-to-task chain, 80+ predeclared questions, recall/false-impact metrics and model-visible tokenizer proxy; integration must not alter PROJECT_PLAN controller authority"
requires_approval: false
expected_mvp_benefit: "Reduce model-visible source context with exact scoped query routing, value-specific document impact and safe next-task suggestions; no claimed fixed token savings"
evidence_urls:
  - https://github.com/dvikt33-ux/safe-bim-layer/pull/69
  - https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38323265836
  - https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-13/apa-pr69-pr68-real-lineage-token-benchmark-20261013.md
risks: "Actual normative engineering acceptance remains NOT_VERIFIED; original data live/PLN absent; current token metrics use o200k_base proxy, not GPT-6 billing; candidate may be covered by existing P50.A01.S01/S03"
---

# Candidate only — independent review required

**Status: PROPOSED / NOT ADMITTED / NOT CLAIMED.** The linked PR #69 is draft research implementation; no runtime integration, main/PLN/APX write or owner claim is authorized here. The `source_substep_id` is the related existing research route, **not evidence that its status was claimed or completed by this action**.

## Explicit nonduplication question for auditor
- `APA-P50.A01.S01` is already PARTIAL and owns research-to-task/artefact/PR traceability.
- `APA-P50.A01.S03` is READY and owns synthesis of same-topic research, conflicts and unknown.
- `APA-P70.A02.S02` is PARTIAL and owns normative applicability, exact versions and NOT_VERIFIED gates.
- `APA-P00.A02.S03` already owns legacy evidence dedup.

If deliverables fit within existing S-IDs, mark **DUPLICATE** or narrow this proposal instead of creating another task. A new S04 only makes sense for independent, queryable **machine interface and measured token/quality acceptance**, distinct from the existing evidence catalogs. Don't create a parallel task dispatcher, publisher or normative evaluator.

## Proposed independently executable work
1. **P0 — Source graph correctness**: extend read-only PR #69 from current source→declared-input→block→S-ID verified structural path to one **fully verified** real field/result chain. Distinguish source bytes, official legal version, parameter dependence, calculation implementation, test evidence, normative authority and current PLN. Reject forged `SOURCE_VERIFIED`.
2. **P0 — Read-only retrieval interface**: expose a bounded MCP-compatible read-only adapter to the existing graph, source class and pinned section reader, with max depth/nodes/snippets/permission filters; keep current `PROJECT_PLAN.json` as only task authority and consult its latest version before task suggestions.
3. **P0 — Token/quality benchmark**: 80+ fixed questions with human-reviewed gold links, provenance, negative/missing-dependency/cross-profile cases; compare current GitHub raw, exact TDK compiled-block route, graph+lexical, and hybrid/re-rank if necessary. Count source-validation/context/API iterations and tokenizer proxy separately from true model-billed tokens.
4. **P1 — Incremental update**: source commit/field fingerprint diff to mark `RECHECK_REQUIRED` for *verified* dependent fields; no status changes/auto-document rewrites without independent review.

## Observable acceptance gates
- A real verified historical snapshot and follow-on change can be replayed by CI with SHA readback and deterministic expected affected/unaffected fields.
- Incorrect semantic propagation or missing provenance fails closed; changing plan claim/lease NEVER invalidates a normative calculation.
- No public leak of licensed/private documents, credentials, raw PLN, or unauthorized fields.
- Each AI query returns narrow, cited facts and uncertainty, not arbitrary excerpts, and output token budgets cannot omit essential evidence.
- Independently reviewed task admission uses TASK_REVIEW_V1 + CAS update + readback + controller tests if new task is necessary. Draft PR should remain unmerged pending review.

The proposal is intentionally not added to the executable plan by its researcher.
