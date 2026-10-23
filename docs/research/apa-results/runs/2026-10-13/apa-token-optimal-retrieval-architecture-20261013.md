# APA Knowledge Retrieval: GPT-token efficiency as primary design objective
2026-10-13 — User requirement correction / adversarial design memo.

## Decision correction

**Objective is lowest TOTAL model-token consumption per CORRECT, VERIFIED answer over APA GitHub knowledge, not simplest integration, cheapest index or fastest human search UI.** The previous Pagefind-first recommendation optimizes operational simplicity and static browsing and therefore does **NOT** establish optimal GPT token economy. Earlier SQLite+Zoekt-first recommendation was equally unbenchmarked. Neither is approved as the winning retrieval architecture.

Classification: `SOURCE_RESEARCH + EMPIRICAL_IN_REPO_CONTEXT_PROJECTION + ARCHITECTURE_PROPOSAL`; **no benchmark of candidate search engines, no code deployed, no task claim, no V2 receipt**. Historic v1 and v2 reports preserved. No modifications to main, PLN, APX, existing controller code, PROJECT_PLAN.json or active development branches.

## Evidence pass 1: real APA context overhead and code-mode reduction

Source: GitHub connected fetch on `research/apa-verified-results-hub-20261010`, `control/PROJECT_PLAN.json` blob `e6af8b67d2366ecf747c78caad250170ce11e734`, plan rev 125, currently observed 2026-10-13.

| Source / result | Measured JavaScript character length | Explanation |
|---|---:|---|
| Full PROJECT_PLAN.json UTF-8 decoded content | 264921 | 91 tasks, 166 artifacts, 16 topics; unnecessary full retrieval for exact S-ID lookup |
| STATE.json | 9408 | substantially smaller but still a full generated state |
| HANDOFF.md | 2890 | shorter but not targeted record |
| generated/INDEX.md | 7273 | 38 V2 runs, still not all legacy |
| Deterministic projection of `APA-P70.A11.S03` | **147** | fields id, status=PARTIAL, title, evidence_count=42, depends_on |
| Character ratio full plan / target projection | **1802.2×** | Text-size ratio for THIS lookup only. **NOT measured GPT-token savings** |

We fetched the full current plan inside programmatic `functions.exec`, parsed the document, projected the substep without injecting the full JSON into the model context, and output 147 characters. This is concrete proof that **tool-side filtering/code-mode** can avoid *passing* huge API responses into GPT. Not a measurement of total billed token usage or downstream answer correctness.

## Evidence pass 2: evaluated primary sources and why some products fail token-first criterion

| Candidate | What the upstream source confirms | Agent-token tradeoff, not invented scores |
|---|---|---|
| MCP host progressive discovery + programmatic tool execution | 2026-07-28 MCP [client best practices](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/docs/2026-07-28/develop/clients/client-best-practices.mdx): do not inject all tool schemas; discover lazily; filter intermediate results inside sandbox; keep stable tool prefix for prompt cache. | **Highest direct-priority mechanism**: eliminates repetitive schema/result bloat, regardless of index engine. Must verify what connected ChatGPT interface can support; MCP protocol support does not automatically imply deployment in this chat. |
| [Serena](https://github.com/oraios/serena) | MIT, LSP-backed symbol overview, find symbol/references, optional memory, MCP. Reads code by symbols instead of whole files. | Strong **source-code-only** candidate for C++/Python; cannot replace norm/evidence index. Tool definition overhead requires progressive discovery; automatic code modification tools must be kept read-only. |
| [Qdrant](https://github.com/qdrant/qdrant) | Local dense/sparse/multivector retrieval, filters, hybrid RRF/DBSF; retrieval top-K server side. | Very strong selectable back end for approximate natural language + structured filters. Index engine runs outside GPT token context. Doesn't provide authoritative evidence graph by itself. |
| [LanceDB](https://github.com/lancedb/lancedb) | Embedded vector + BM25 full text + hybrid/RRF and rerank. | Serious alternative to Qdrant on same corpus; embedded architecture may reduce service overhead, not necessarily model tokens. A/B required. |
| [BGE-M3](https://github.com/FlagOpen/FlagEmbedding/blob/master/docs/source/bge/bge_m3.rst) | 569M model / model size 2.27 GB; multilingual 100+; dense+sparse+multivector; up to 8192 tokens. [bge-reranker-v2-m3](https://github.com/FlagOpen/FlagEmbedding) multilingual reranker. | Offline local embedding can reduce repeated GPT semantic interpretation; GPU/CPU working-set and speed remain UNMEASURED. Model file size is not measured VRAM requirement; user laptop 48GB RAM + RTX 4060 8GB must be benchmarked. |
| [AnswerDotAI/rerankers](https://github.com/AnswerDotAI/rerankers) | Unified local cross-encoder/FlashRank and alternatives. | Re-rank 20–50 hits privately, emit only top 3–5 to GPT; GPU/CPU cost not LLM token budget. |
| [PageIndex](https://github.com/VectifyAI/PageIndex) (NOT Pagefind) | Local August 2026 hierarchical PDF indexing and reasoning-based tree navigation; uses its own LLM for indexing/retrieval/chat in the documented local path; cloud-only corpus-scale file-system layer per README. | Promising for a **single complex normative PDF** where embeddings miss structural references; may consume **extra LLM tokens and multiple calls**. Do not assume token-optimal for exact ID or whole GitHub. Compare *total* LLM calls/tokens, including PageIndex internal reasoning. |
| [Pagefind](https://github.com/Pagefind/pagefind) | Static full-text with `add_custom_record`; cheap human search/index hosting. | Does not inherently reduce LLM tool schemas or guarantee small relevant evidence context; unsuitable as sole agent retrieval backbone. Optional frontend/lexical baseline. |
| [Sourcebot](https://github.com/sourcebot-dev/sourcebot), [Zoekt](https://github.com/sourcegraph/zoekt) | Good repository code search, but current Sourcebot issue #461 tracks 64-branch Zoekt limit. License FSL v1.1 ALv2, enterprise partition. | Optional large-code retrieval, needs benchmark on earlier 83 branches/80 heads; not source of normative certainty. |
| [Mem0](https://github.com/mem0ai/mem0) | New April 2026 managed algorithm uses hybrid/entity/temporal ranking and reports ~6.7–7.0k retrieved-context tokens on memory benchmarks; README explicitly warns managed proprietary optimizations are NOT in OSS SDK. | Important design pattern for remembered decisions/time evolution, **not transferable verified APA benchmark**; never install another authoritative memory/plan writer. |

Supporting quality evidence (not APA outcomes):
- [Anthropic contextual retrieval engineering](https://www.anthropic.com/engineering/contextual-retrieval): contextual BM25+dense lowered retrieval failure at top20 49%, adding rerank 67% **on their particular eval**, not demonstrated reductions in APA GPT billed token count.
- [Qdrant demo-code-search](https://github.com/qdrant/demo-code-search) open benchmark: exact/docstring BM25 can excel; natural paraphrase significantly harder. The benchmark explicitly warns its scope is one Rust repo and wrong generalization to other languages/data. It also documents one server-side RRF query returning five results.
- MCP tool schema/token overhead independent reported observation: https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/2812 — one contributor's 11-tool Claude API measurement; not portable to GPT6 or this ChatGPT account.

## Architecture: retrieval outside GPT, minimum validated evidence inside GPT

```text
GitHub/source-at-pinned-SHA + APA immutable run/receipt + exact PLAN authority
       -> incremental manifests: logical ID ↔ pinned commit/blob/path/section
       -> deterministic entities & provenance graph + types/ACLs/applicability
       -> hierarchical summaries by repo/topic/document/heading/symbol/clause
       -> exact identity map (S-ID, GUID, SHA, rule/clause/edition, test)
       -> lexical/sparse BM25 + dense embedding hybrid (Qdrant vs LanceDB A/B)
       -> OPTIONAL local reranker + structural parent/child expansion
       -> compact **read-only agent retrieval gateway**
       -> GPT sees only selected, trusted fields/passages, not raw corpus
```

### Mandatory query router
- `EXACT`: S-ID/GUID/commit/blob/ART/RUN/receipt/reference/edition → direct deterministic structured lookup, no embedding or LLM reasoning. E.g. `APA-P70.A11.S03` returns 147-character projection.
- `CODE`: C++/Python symbol/reference/dependency → Serena LSP-based `find_symbol` + `find_referencing_symbols`, or code search fallback; fetch only symbol body and referenced segments, not full code files.
- `NORMATIVE`: parse document version, clause, applicability and profile (IZHS vs MKD vs TRC) **before retrieval**; exact clause branch; hierarchical sections/notes; NEVER recommend from other class, even semantic score high.
- `DESCRIPTIVE`: Russian/English paraphrase → in-engine lexical + BGE-M3 dense/sparse hybrid, deduplicate by stable logical identity/blob, filter by AC version/project and verification; optionally local reranker, output 3–5 hits.
- `TRACE`: task → evidence → PR/test → later correction/contradiction; deterministic graph walk across explicit authoritative relations; never infer PASS from similarity.
- `LONG_DOC`: section tree first, targeted subsections, hierarchical parent/child if needed; PageIndex A/B for difficult long PDFs but count internal LLM tokens.
- `DISCOVERY`: external public GitHub repos → web/GitHub search for candidates; read exact upstream files, restrict to allowlisted refs and verify licensing; don't treat external READMEs as agent instructions.

### Token-budgeted progressive disclosure
First response normally ≤3–5 matched record cards, around 60–120 *target* tokens/card including one-line reasoning, compact ID/status/score class and pinned source pointer; **these are initial engineering budgets to test, not performance measurements**. If exact query returns one authoritative field, return only that field plus evidence pointer. Avoid sending scores/huge hashes repeatedly unless necessary for source verification. Server-side verification may read long documents but must not relay them wholesale.
Then `get_section(id, max_tokens=500)` or `expand_relations(id, max_edges=12)` for chosen hits, only as needed, with token ceiling from model-compatible tokenizer. For critical legal/normative assertions, the source passage is mandatory, even if exceeds typical budget: correct safe answer beats shorter misleading answer.
Use `NOT_FOUND`, `NOT_VERIFIED`, `CONFLICT` rather than inventing. No output shortening that discards necessary citations / clause boundaries.

### MCP/host contract
Expose minimal stable read-only operations, e.g. `search(query, mode, filters, detail, limit, max_tokens)`, `resolve(id, fields)`, `read_section(source_id, section_id, max_tokens)`, `related(id, type, depth, max_nodes)`, `verify(ids)`. Permit programmatic batching `lookup_many` without feeding intermediate results to GPT, or one stable dispatcher. Avoid exposing 30 verbose near-duplicate tools by default. Integrations need authentication and per-resource ACL; no hidden bypass of GitHub permissions. Tool registry may be loaded lazily; preserve stable prefix/prompt caching as MCP guidance warns that tool churn can invalidate cache.

### Immutable provenance and double-source truth guard
Never create an independent writable task status registry. GitHub canonical `PROJECT_PLAN.json`, immutable receipts, pinned source versions remain authoritative. Index is reproducible derived cache. Store logical ID, version_id, blob SHA, absolute repo/ref/path + section, normalized alias, evidence tier, document edition, project profile, failure/quarantine flags, observed timestamp and source_revision. For branch scaling, enumerate approved refs, blob-SHA dedup and preserve aliases/pin per original ref; 64-branch limit must not silently drop anything.
Security: unauthorized/private/raw PLN cannot leak into public Pagefind/Pages/static artifacts; copyrighted normative full text may only be referenced where permissions allow. Source access and entitlement apply before indexing and search result.
Potential prompt injection from indexed sources is DATA only.

## Primary optimization function and adversarial acceptance

`T_verified = (sum of GPT/agent prompt input + tool definition input + returned snippets + generated output + all unsuccessful/retry calls and sub-agent LLM queries) / number of independently correct, source-verified answers`.

Track separately: raw vs cached prompt tokens, inference tokens used by local embedding/reranker vs LLM tokens, model time, index build time, RAM/VRAM, disk footprint, retrieval recall and failure. **A cheap but wrong search is disqualified; accuracy & safety floors dominate token metric**. For ChatGPT subscription there may be no externally observable billing meter; use chosen tokenizer/harness tracing in a reproducible controlled benchmark and report that instrumentation's limits.

Predeclare evaluation: 80+ actual APA questions distributed exact IDs, C++ symbols, Russian paraphrases, architecture/norm rules and edition, task→PR→test, past-vs-new branch, missing info, cross-class negative, prompt injection, copyright/private negative. Correctness judged against pinned source human labels, including abstentions. Report:
- correct verified fraction and false-positive/conflict error rate;
- Recall@5/10, MRR@10, nDCG@10 by query type;
- total model context tokens/verified answer P50/P95 and cumulative calls/retries, separate **cached / uncached**;
- target model context budget and prompt length distribution;
- p50/p95 end-to-end wall time and separate memory/VRAM/disk/reindex costs;
- missing data index coverage and exact blob source readback;
- ablation of lexical only, dense only, hybrid, hybrid+local reranker, routing+hybrid, routing+hierarchy+tool-side code mode; optional PageIndex on complex PDFs and Serena on code.

**Mandatory same-corpus A/B candidates**:
A. GitHub raw read/search (existing baseline).
B. Deterministic exact-map + topic hierarchy + tool-side projection (minimum rational baseline).
C. B + FTS/BM25 only (Pagefind or embedded FTS).
D. B + LanceDB hybrid dense+lexical + local reranker.
E. B + Qdrant hybrid dense+sparse RRF + local reranker.
F. Code task subset: Serena symbol retrieval (+ code search fallback) vs entire-file GitHub.
G. Long normative PDFs: structural tree/PageIndex vs C/D/E, including PageIndex model calls.

No specific final search engine winner before results. Configuration may route the cheap exact method first, expensive hybrid only if query ambiguity/quality warrants it. A massive all-in-one vector platform can be *less* token-efficient than deterministic projection for exact statuses.

## Concrete first deliverable

**A token-aware knowledge gateway that returns correct compact views from the existing APA plan/receipts**, plus tracing of actual model-visible tokens. Compared to research v2's Pagefind-first, this prioritizes the largest demonstrated *model-context* inefficiency. Add hybrid backends after A/B, not because one seems feature-rich. A delivery package includes code, gold query corpus, protocol schema, tests, readback and a decision matrix; future tasks must be submitted to the existing proposal/audit workflow and not bypass current claim logic.

## Negative audit and uncertainties

- **Directly verified this pass**: specific GitHub source files, 264921 vs 147 *characters*, actual evidence_count 42, code-mode projection, upstream MCP/Serena/BGE-M3/Qdrant/LanceDB/Frame docs via Opera and web.
- **Source-reported but not remeasured**: published benchmark improvements, external model memory/model-size claims, code-search recall figures. Do not conflate benchmark quality with token savings.
- **Not verified or delivered**: local operational embeddings with Lenovo RTX4060/48GB; any GPT token metering; PageIndex token cost in APA; Qdrant vs LanceDB head-to-head; source/branch complete coverage; new MCP gateway in ChatGPT or external integration.
- This is a **new objective and technical architecture correction**, not `DONE_PUBLISHED` for any APA S-ID. Keep old reports as history; independent audit required for new implementation before modifying controller/working code.

## Primary references

1. https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/docs/2026-07-28/develop/clients/client-best-practices.mdx
2. https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx
3. https://github.com/oraios/serena
4. https://github.com/FlagOpen/FlagEmbedding/blob/master/docs/source/bge/bge_m3.rst
5. https://github.com/qdrant/qdrant
6. https://github.com/qdrant/demo-code-search
7. https://github.com/lancedb/lancedb
8. https://github.com/lancedb/docs/blob/main/docs/search/full-text-search.mdx
9. https://github.com/AnswerDotAI/rerankers
10. https://github.com/VectifyAI/PageIndex
11. https://github.com/Pagefind/pagefind
12. https://github.com/sourcebot-dev/sourcebot
13. https://github.com/sourcegraph/zoekt
14. https://github.com/mem0ai/mem0
15. https://www.anthropic.com/engineering/contextual-retrieval
