# APA — executable unified GPT retrieval gateway + modern MCP v2 adapter: measured outcomes
Date: 2026-10-13 | Classification: IMPLEMENTED_IN_DRAFT_PR + REAL_CI_PASS + INDEPENDENT_AUDIT_PENDING
Source code: [draft PR #69](https://github.com/dvikt33-ux/safe-bim-layer/pull/69), branch `research/apa-knowledge-impact-poc-20261013`, ONLY targeting canonical `research/apa-verified-results-hub-20261010`.

## Problem and source-backed correction
The previous implementation had separate commands (graph, FTS section search, artifact join, field-change adapter). This requires agent orchestration and more tool descriptions than necessary. The user needs one bounded, provenance-preserving access point, and must not analyze the entire GitHub library before determining the next action.

Solution in PR #69:
- [gateway.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-knowledge-impact-poc-20261013/tools/apa_knowledge_graph/gateway.py): **single read-only context-retrieval interface**, prioritizes exact S-ID/ART-ID direct lookups, graph joins of several ART-IDs, scoped SQLite FTS5 Markdown section search and read-only task candidates. Current PLAN snapshot hash checked on each call, source byte SHA-256 of retrieved top-K sections checked, `max_chars` budget and non-truncated citations enforced. `mode=normative` NEVER asserts official/legal authority from a local document label.
- [mcp_adapter.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-knowledge-impact-poc-20261013/tools/apa_knowledge_graph/mcp_adapter.py): optional **one-tool local stdio MCP server** using official stable `mcp==2.3.0` Python SDK v2, with modern `MCPServer` API. Defines `apa_retrieve(query, mode, source_class, limit, max_chars)`. Source paths are operator-controlled process arguments and **never model-controlled tool inputs**. The process has no write tools, no public HTTP service, no direct rule-status changes and no BIM writers.
- [test_gateway.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-knowledge-impact-poc-20261013/tools/apa_knowledge_graph/tests/test_gateway.py): scoped multi-document search, ART intersection, limited outputs, stale index, path boundary, hostile query, missing IDs, claim/lease-safe potential task suggestions.
- [test_mcp_adapter.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-knowledge-impact-poc-20261013/tools/apa_knowledge_graph/tests/test_mcp_adapter.py): genuine official MCP SDK tool discovery and `call_tool` invocation, no model path inputs, no source changes and freshness gate.

## Verified real CI, not just a design proposal
- GitHub Actions [38326739252](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38326739252): **71 tests PASS**, first integrated gateway version.
- [38326877256](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38326877256): read-only real query execution PASS.
- [38327026352](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38327026352): **78 tests PASS**, including genuine MCP v2 list_tools/call_tool against prepared plan/section fixtures; real APA checkout plan revision **127** in this run (up from earlier rev 125/126; user concurrent development untouched).
- [38327181425](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38327181425): **78 tests PASS** and explicit validation that the shared task survives multi-document budget; details below.
- Last claim/lease safety test added in subsequent commit; its independent Actions result must be checked before calling that change CI PASS.

### Real correctness problem caught, and fixed before release
The first real join `ART-APA-RU-JUNCTION-NORMS ART-APA-CSE-RESEARCH` found 18 tasks mentioning at least one input and **one task mentioning both**, but when constrained to 1,600 characters it emitted both verbose source URLs and **omitted the only shared task**. This defeated the user objective even though lookup returned PASS: counts alone cannot tell GPT *which* task joins the documents.

**Fix:** the shared task card takes precedence, URLs are late-resolved only by exact ART-ID lookup, and source cards retain ART-ID, unpinned status and source-verification metadata. Assertions require the shared task to remain visible in a 1,600-char real APA CI query, while no task, source version or negative authority state is silently invented. [Run 38327181425](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38327181425): `REAL_SHARED_TASK_SURVIVES_BUDGET 3 1259`, i.e. **three returned cards, 1,259 characters including a newline**.

### Reproducible tokenizer proxy (separate from answer quality)
Using `tiktoken 0.14.0 / o200k_base` for precisely the above two-ART query, the real CI printed:

| Payload | Proxy tokens |
|---|---:|
| Unfiltered full `PROJECT_PLAN.json` from the same CI checkout | **77,829** |
| Fully assembled compact two-artifact join response | **359** |

This is a **216.79× text-token ratio for the exact query and two stated payload choices**. It is NOT actual GPT-6 billed tokens or a fair head-to-head search engine benchmark: (a) the full-plan baseline is intentionally unfiltered, (b) prompt tool-schema load, cache, retries, tool execution, LLM reasoning and quality/errors are excluded, (c) exact known ART-IDs are a simpler case than ambiguous Russian natural language, (d) separate required source resolution may add tokens later. The output budget constrains characters (not guaranteed GPT tokenizer units).

## Security, provenance and performance caveats
- Every indexed source excerpt is untrusted data; PR must undergo independent prompt injection / data authorization review before any GPT host install.
- Repo path labels `PROJECT_CONTROL/RESEARCH_RUN` are NOT official legal document attestation. Normative answer returns leads with `NOT_VERIFIED_OFFICIAL_SOURCE`.
- Existing TDK compiled-block exact routes from [PR68](https://github.com/dvikt33-ux/safe-bim-layer/pull/68) remain the primary normative route. No second normative engine, no global norm scan.
- `GITHUB_PROJECT_PLAN_ONLY` identifies the **checkout plan snapshot**, not automatically the current GitHub remote head. After a new authoritative plan commit, derived caches must rebuild or return `STALE_INDEX`.
- Current `next` mode yields potential candidates with dependency and claimed-state guards; it NEVER replaces the official controller's dispatcher, updates task status or issues a claim. The extra lease-flag guard is intentionally conservative even for expired leases.
- Local stdio MCP is **implemented/tested in CI**, but NOT connected or installed on the user's own ChatGPT client, Windows computer, Archicad add-on, or external host. The MCP host must support local stdio server processes and permissions. No claim of automatic ChatGPT plugin installation or cloud availability.
- Markdown corpus in prior run: **204 docs, 2,113 sections** from scoped research archive; not a library-wide or user normative primary-source completeness guarantee.
- Important future A/B: known-ID vs new semantic query, Russian morphology, cross-class norm applicability, multi-document contradictions, exact pinned source resolution, current/expired task leases, private/licensed source ACL, top-K diversity, genuinely verified complete source→value→calculation→BIM→test chain, and full GPT-6 total usage (if measurable).
- MCP v2 provenance: [official Python SDK 2.x](https://github.com/modelcontextprotocol/python-sdk), [MCP v2.3.0](https://pypi.org/project/mcp/2.3.0/) and [modern stdio support](https://py.sdk.modelcontextprotocol.io/). MCP model-facing tool schema should remain stable to preserve caching.

## Acceptance / next work, without unauthorized main/task writes
1. PR #69 remains DRAFT until independent review of source/provenance, root privilege, content injection and CI quality. No merge into product branches based on research-only tests.
2. **Source trust and retrieval coverage are the next correctness bottleneck**, not adding another vector database. Review one real authoritative numeric chain before any plan/PLN writes.
3. Run >=80 manually adjudicated APA multi-doc/impact queries across raw GitHub, exact graph+FTS, and candidate hybrid reranker, reporting total model tokens per correct answer. Benchmarks above are a narrow proof-of-mechanism only.
4. Existing research [TASK_PROPOSAL_V1](../control/proposals/APA-CAND-20261013-knowledge-impact-gateway.md) awaits independent `TASK_REVIEW_V1`. Do not alter `PROJECT_PLAN.json`, `IN_PROGRESS` claims, controller dispatch, main, PLN or APX.

**Artifact itself is source-backed research persistence with GitHub readback, not a V2 publisher receipt; no S-ID is made DONE here.**
