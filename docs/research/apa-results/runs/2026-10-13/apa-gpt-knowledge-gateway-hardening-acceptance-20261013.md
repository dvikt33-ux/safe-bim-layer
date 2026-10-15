# APA GPT Knowledge Gateway — hardening, structural census and disposition (2026-10-13)

**Category:** EXECUTABLE_RESEARCH_POC / CI_VERIFIED / ADVERSE_NEGATIVE_TESTS_PASS / NOT_PRODUCTION_DEPLOYED.
**Source code:** [PR #69](https://github.com/dvikt33-ux/safe-bim-layer/pull/69), head `research/apa-knowledge-impact-poc-20261013`, base `research/apa-verified-results-hub-20261010`. No main/Archicad/PLN/APX changes or controller task/status updates. No merge.

## Final tested result on live GitHub CI
GitHub Actions [run 38327961036](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38327961036), Linux/Python 3.11 with optional MCP Python SDK v2.3.0, PyYAML 6.0.3 and tiktoken 0.14.0:
- **92/92 regression/negative tests PASS.** Includes genuine MCP v2 server `list_tools/call_tool`, real PR68 SHA-locked TDK source chain, exact real plan queries, field delta safety, source tamper, class anti-promotion, no writes.
- Real checkout had **91 tasks**, **173 registered artifacts** and **209 indexed Markdown files / 2142 sections**. Numbers are for the CI checkout, not universal branch counts.
- **304 structural lookup cases checked** with 0 deviations from registered PLAN metadata: 91 exact S-ID task requests, 173 exact ART-ID retrievals, and 40 two-artifact task-reference joins. Structural results are independently rechecked against the same plan records, **not human-adjudicated open-ended semantic search**.
- `mode=plan`: **18** potential tasks passed the read-only owner/claim/lease/dependency eligibility gate; returned a bounded shortlist of **5** with `total_eligible_tasks=18`. This is not dispatcher authorization or a task claim. Remote main/branch freshness is distinct from checkout file-hash freshness.
- Exact two-ART real graph query: matching shared task remains visible despite a compact **1259-character** output limit. Prior defect that URLs crowded out the shared task was fixed with shared-task-first and deferred URI lookup.
- Tokenizer `tiktoken o200k_base` proxy for same exact two-ART query: **77,829 tokens raw `PROJECT_PLAN.json` versus 359 tokens model-visible compact result**. Neither billed GPT-6 tokens nor full agent-token-cost or semantic quality claim; 216.8× ratio is for intentionally raw-plan vs already resolved compact response only.

## Adversarial defects found and corrected this pass

### A. Missing/out-of-date nonreturned documents (silent false-negative)
Prior FTS reader only byte-hashed the *returned top-K sources*; a newly added document, a deleted one or an unrelated edited document could go unnoticed, so retrieval could incorrectly show zero matches from a stale corpus.

**Correction:** `sections.py` now persists a disposable manifest with explicit source roots, file paths, byte sizes and mtime_ns for all indexed files. Before SQL search it compares the current allowlisted source list/stat signatures; changes fail closed as `STALE_INDEX`. For each returned section it still reads source bytes and compares SHA256. Does not pass the manifest/document bodies to GPT.

**Limit:** file stat checking is not a cryptographically complete rehash of every non-returned file on every query; an adversary preserving size/mtime outside selected hits requires repo commit pinning/independent rebuild verification. The manifest is intentionally inexpensive locally and makes no unsupported global attestation claim.

### B. Index cache could counterfeit a snippet while original file SHA still matched
Prior system checked the SHA of the original source file against the *cache's stored source SHA*, but did **not** independently attest FTS row section text/class/heading against the original file. An altered FTS row could display fabricated text that passed the source byte hash check.

**Correction:** selected FTS rows return internal `content` (never sent wholesale to GPT); the reader splits the original source into exact `(heading, line, body)` tuples and compares indexed text, line, heading and path-derived source class. Mismatch fails closed as `INDEX_TAMPERED`, with zero result excerpts. Negative tests mutate SQLite index `content` with a fake model command or incorrectly promote `OTHER_DOCUMENT` to `PROJECT_CONTROL`; both tests PASS while original Markdown remains unchanged.

### C. Planning mode had needless full-text searching
Research questions `что делать дальше` must first consult the controller plan, not infer next tasks from lexical matches in arbitrary old reports.

**Correction:** new deterministic `mode=plan` routes to the existing `PROJECT_PLAN.json` derived graph, filters unsafe occupied/claimed/leased/blocked tasks, computes prereq status, sorts by plan priority, returns compact candidates with `requires_claim=true` and `task_claim=NEVER_AUTOMATIC`. No FTS needed. Later audit caught candidate count wrongly reflecting the first 5 shown rather than the full 18 eligible: fixed `total_eligible_tasks` and separately reports `omitted_due_to_limit`.

**Limit:** candidates are checkout snapshot recommendations, not official latest remote scheduling. If a concurrent executor claims work after checkout, a refresh and controller CAS are still required.

### D. Multi-document join under short answer budget
Previously returned full long GitHub URIs **before** the only shared task; a short token budget omitted the most valuable link.

**Correction:** prioritise the shared task, defer full URL to exact ART lookup; real CI `REAL_SHARED_TASK_SURVIVES_BUDGET 3 1259` PASS. Graph edges labelled `COMMON_TASK_REFERENCE_NOT_SEMANTIC_DEPENDENCY`: no false normative calculations inferred.

## Reused upstream, not reinvented
TDK PR68 `compiled_blocks_primary_retrieval_reserve` already routes via exact project type, module, block and specific missing edge. The new read-only adapter verifies existing six pinned roof package files and the structural chain `roof_slope_length_m → ROOF-VENT-CHANNEL-TABLE-A2-001 → IZHS.ROOF.DETAILS → APA-P70.A02.S02` with quarantined `design_only` source. On a *synthetic* field value change it emits `RECHECK_REQUIRED_NOT_RECOMPUTED`, **never a numeric engineering answer**.

No proof of official SP legal applicability, user's actual PLN field value, or an approved calculation. Neither the graph nor keyword FTS is a second normative authority.

## Audit boundaries and release gate

**Audited in this development pass, not independently reviewed by another agent/person.** Structural tests and malicious-index tests are observed in GitHub CI. The following remain explicit NOT_VERIFIED / NOT_IMPLEMENTED:
1. Human-reviewed relevance/precision/recall of arbitrary Russian free-text queries and genuine multi-document contradictions (no independent 80+ semantic gold corpus);
2. total actual GPT-6 tokens including host schema, reasoning, retries, cached-prefix accounting and model-based index work (text tokenizer proxy only);
3. complete official clause → independently verified rule value → real project system/material → actual PLN → calculation → validation/test lineage;
4. access-control boundary for private/licensed source collections and current remote plan/branch freshness (local repo checkout source-stat and top-K SHA only);
5. installation/connection of local MCP `apa_retrieve` into the user's current ChatGPT or Archicad runtime; local stdio SDK interface was tested, not remotely installed.

**Disposition:** Research POC code and tests are ready for independent PR review; **do not merge into live controller, promote `DONE_PUBLISHED`, or claim production-ready token-optimal search**. The existing GitHub [task proposal](../../control/proposals/APA-CAND-20261013-knowledge-impact-gateway.md) must go through existing independent `TASK_REVIEW_V1` before project-plan admission. If the official reviewer discovers overlap with `APA-P50.A01.S01/S03`, refine scope rather than create duplicate authority.

## Related evidence
- [PR #69 implementation](https://github.com/dvikt33-ux/safe-bim-layer/pull/69)
- [Latest 92-tests PASS](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38327961036)
- [Real TDK lineage and 57-test tokenizer pilot](apa-pr69-pr68-real-lineage-token-benchmark-20261013.md)
- [MCP one-tool 79-test pilot and 359-token sample](apa-unified-gpt-mcp-retrieval-gateway-20261013.md)
- [Proposed independent task admission](../../control/proposals/APA-CAND-20261013-knowledge-impact-gateway.md)
