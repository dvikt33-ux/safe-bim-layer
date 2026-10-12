# APA machine retrieval — implemented read-only graph and multi-document POC, observed CI and adversarial audit
Date: 2026-10-13. Written to canonical APA research hub while actual code remains reviewable in **[draft PR #69](https://github.com/dvikt33-ux/safe-bim-layer/pull/69)**, head `research/apa-knowledge-impact-poc-20261013` targeting `research/apa-verified-results-hub-20261010`.

## Truthful status
**CODE IN GITHUB / REAL CI PASS / NOT MERGED / NOT PRODUCTION INTEGRATED.** This is an actual implementation with executable tests and proof from CI on a real APA checkout, **not** a theoretical report; it is also NOT a verified cross-document normative reasoning service or an authorized new task. No main, published controller, tested product code, PLN or APX changes; no paid API. PR is draft; merge and any plan/task admission require independent review. This report itself is not a V2 publisher receipt.

## Deliverables in PR #69
- `tools/apa_knowledge_graph/graph.py`: derived read-only task/artifact inverse graph; exact ID/task, potentially affected tasks (not proven), scheduling descendants; explicit typed field lineage for declared scope-matched edges. Rejects stale plan cache when `--verify-plan` supplied; refuses to overwrite source.
- `tools/apa_knowledge_graph/multidoc.py`: bounded join across 1–16 ART IDs, relation type **CITES_ARTIFACT_ONLY**, duplicate elimination, matched-task count and source-version uncertainty.
- `tools/apa_knowledge_graph/delta.py`: compare two plan snapshots / field value snapshots and propose minimal candidate impacts. Never changes status.
- `tools/apa_knowledge_graph/sections.py`: SQLite FTS5 section index over explicit local Markdown roots. Top-K excerpt character ceiling, Markdown heading/line, local SHA-256 source byte readback, safe query parsing, labels `RESEARCH_RUN`, `PROJECT_CONTROL`, `ARCHIVED_SOURCE`, `OTHER_DOCUMENT`, class selection to prevent report/primary-source confusion.
- `tools/apa_knowledge_graph/tests/`: tests on actual plan and negative synthetic field-lineage cases. New isolated read-only PR workflow in `.github/workflows/apa-knowledge-impact-poc-ci.yml`.
- `tools/apa_knowledge_graph/README.md`: commands, boundaries, upstream alternatives, observed acceptance and remaining blockers.

## Evidence of actually run tests and exact quantities
- Initial run [38320136500](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38320136500): **24 offline tests PASS**; real plan readback and two source task/artifact queries PASS.
- Expanded run [38320696467](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38320696467): **43 tests PASS**; section index of **204 Markdown documents / 2,113 sections**; source-byte SHA-256 matches returned fragments.
- Scoped/quality fix run [38320830932](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38320830932): **45 tests PASS**; 204 files/2113 sections; explicit `PROJECT_CONTROL` filtering passed the real `кровли` query, returning only a roadmap section. **Not a claim of normative source applicability**.
- Actions build checkout was plan **revision 126** with 91 tasks and 166 artifacts. Query `ART-APA-RU-JUNCTION-NORMS` yielded **15 reference candidates**; response limited to top five with omitted count 10 and proper `POSSIBLE_IMPACT` marker.
- Multi-document real join `ART-APA-RU-JUNCTION-NORMS` + `ART-APA-CSE-RESEARCH` yielded **18 total tasks citing either source, one task citing both**, with 5 bounded result cards. Both source URIs point to **moving feature branch**, therefore reported `UNPINNED_OR_UNVERIFIED_URI`.
- Separate direct current GitHub plan comparison rev 125, blob `e6af8b67d2366ecf747c78caad250170ce11e734`, versus rev 126, blob `bfdef0d7653ff40bef9d402888f3ff27ced0e15e`, found exactly **one changed task** `APA-P70.A11.S03`: `status=PARTIAL→IN_PROGRESS`, `owner`, `lease_until`, `claim_ref`; **0 changed artifact records**. Correct processing: scheduling/claim update only, no derived normative recalc or automatic task duplication. Do not interfere with active claim.
- All these are **functional and data-volume results**, not measurements of billed GPT-6 tokens, global search recall or full corpus coverage.

## Adversarial audit: what failed and was fixed
1. **Original naïve broad lexical query `кровли` returned a research evaluation report before any authoritative norm**. The keyword match was technically valid, but relevance/trust for an engineering answer was wrong. **Fix in POC:** explicit provenance class and query-side class filter; query that needs official SP must first verify authoritative source exists. Failure remains **NOT SOLVED** for unseen norm editions / Russian morphology or semantic ranking, so do not say the search engine has normative intelligence.
2. Index staleness could otherwise give a convincing wrong result. **Fix:** compare `PROJECT_PLAN.json` hash against current plan for exact task query (`--verify-plan`), and original source SHA-256 against source bytes for top-K Markdown search. This checks bytes, NOT norms' legal force.
3. Wrong normative impact from mere task-to-document reference. **Fix:** label references `POSSIBLE_IMPACT`; validated test that no `REFERENCES` edge propagates as proven field dependency. Scheduler `depends_on` stays separate from data lineage.
4. Trust escalation from arbitrary input lineage remains an OPEN issue: `SOURCE_VERIFIED` on a supplied edge only checks metadata shape and syntactically pinned 40/64-hex `source_revision`, not independent source semantic/byte attestation. POC returns `runtime_evidence_readback=NOT_PERFORMED`; production must reject forged trust and use independent audited receipts.
5. Cross-project IZHS/MKD/TRC edges prohibited in POC; a valid general/shared rule needs explicit independently reviewed applicability before broadening.

## Parallel higher-quality alternatives investigated
- [Bazel Skyframe](https://bazel.build/versions/8.5.0/reference/skyframe) uses reverse reachability and **change pruning**; its logic should guide our document/field impact, not automatically launch a whole build system.
- [Nx affected](https://nx.dev/docs/features/ci-features/affected) warns that scheduling `dependsOn` alone is **NOT enough** to prove changed inputs affect a task; exact consumed inputs and outputs matter. Confirms our conservative design.
- [DVC params](https://doc.dvc.org/command-reference/params) compares specific nested parameter keys in YAML/JSON/TOML, useful pattern for safe field-level recomputation without swapping current publisher.
- [OpenLineage column lineage](https://openlineage.io/docs/spec/facets/dataset-facets/column_lineage_facet/) distinguishes `DIRECT` value derivation from `INDIRECT` filter/ordering dependencies; useful to avoid false propagation from plain document citation.
- [Graphiti](https://github.com/getzep/graphiti) and [LlamaIndex PropertyGraphIndex](https://developers.llamaindex.ai/python/framework/module_guides/indexing/lpg_index_guide/) are **credible ready-made graph/retrieval alternatives**, not ignored. Their ordinary LLM extraction/query and/or embedding calls must be counted in TOTAL GPT token budget and benchmarked; the default `SimpleLLMPathExtractor` and `LLMSynonymRetriever` in LlamaIndex illustrate hidden inference costs.
- [Kuzu](https://github.com/kuzudb/kuzu) is **archived since 2025-10-10**. A prior assumption that a Kuzu-backed product was an obviously safe long-term Windows deployment choice was premature.
- Candidate FTS backend is a local lexical baseline, not selected as final winning architecture. Compare Qdrant/LanceDB hybrid and local reranking only using the same pinned corpus, true sources, recalls and **model-visible tokens per CORRECT sourced answer**.

## Precise next acceptance, not generic research
1. Independently audit PR #69 for data-access controls, source provenance and untrusted edge status. Fix any high-risk false attestation before merge.
2. Create verified lineage for **one complete real chain**, e.g. one exact norm clause (official edition) → parameter → calculation → design/Archicad rule → test → S-ID, with actual source-revision readback. No invented norm numbers.
3. Execute a controlled **same-question A/B**: GitHub raw docs vs compact graph/FTS vs hybrid embedding+rerank vs ready-made graph retrieval. Measure end-to-end correctness, hidden indexing LLM tokens, model-visible input/tool/output tokens, false impacts/missed links and time. No performance winner yet.
4. For task admission, inspect overlap with `APA-P50.A01.S01/S03` and `APA-P00.A02.S03`, use current `TASK_PROPOSAL_V1` and independent `TASK_REVIEW_V1` protocol. `PROJECT_PLAN.json` must remain sole task authority.
5. Do not mark any S-ID `DONE_PUBLISHED` or merge PR on this report alone. Owner/CI review is separate.

Source of truth links: [PR #69](https://github.com/dvikt33-ux/safe-bim-layer/pull/69) / [POC code README](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-knowledge-impact-poc-20261013/tools/apa_knowledge_graph/README.md) / [read-only CI](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38320830932).
