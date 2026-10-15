# APA — research branch integration: verified token-saving GPT knowledge gateway
Date: 2026-10-13
State: **MERGED_INTO_CANONICAL_RESEARCH_HUB / CODE_READBACK_VERIFIED / NO_PRODUCTION_INSTALL**
Canonical research merge: `64cec581b257b209a097556ae19d498e53631ba1` (PR #69 squash merge).
Original PR: https://github.com/dvikt33-ux/safe-bim-layer/pull/69
Repository: `dvikt33-ux/safe-bim-layer`. Branch: `research/apa-verified-results-hub-20261010`.

## What was actually delivered
- `tools/apa_knowledge_graph/{graph,delta,multidoc,gateway,sections}.py`: read-only source-derived graph for task/artifact IDs, bounded multi-source joins, scheduling versus semantic-lineage separation, SHA/manifest-verified section FTS, explicit value change impact and deterministic next-action triage using real `PROJECT_PLAN.json`.
- `tools/apa_knowledge_graph/machine_adapter.py`: pinned PR68/TDK source lock, exact IZHS compiled roof block routing and declared rule inputs; no unproved numeric normative compliance. The existing TDK route is reused instead of a second normative RAG authority.
- `tools/apa_knowledge_graph/mcp_adapter.py`: official MCP 2.3.0 **one-tool `apa_retrieve` stdio server**, source classes (default only PROJECT_CONTROL and RESEARCH_RUN) controlled by operator, max output characters controlled by operator. No model-selected paths or filesystem writes. NOT installed/connected to current ChatGPT.
- `tools/apa_knowledge_graph/bootstrap.py` and **`Setup-APA-Knowledge.cmd`**: one-command Windows setup of derived user cache at `%LOCALAPPDATA%\APA\Knowledge`, no source document, branch, controller, PLN/APX modifications. Prints local MCP launch arguments for compatible operator-managed MCP client, does not register any host automatically.
- `benchmark_retrieval.py` and tests: direct A/B baseline weighted heading BM25 on same 100 anchored source queries and 304 source-registry structural probes.
- GitHub Actions CI includes both Linux and Windows Python 3.11 and actual user-facing CMD execution.

## Last independently observed automated runs
[Final two-platform CI 38329224160](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38329224160):
- **Linux: 102 tests PASS** (GitHub Actions).
- **Windows: 102 tests PASS**; bootstrap via Python and actual `Setup-APA-Knowledge.cmd` PASS; Windows native index + query PASS, explicit UTF-8 stdout handling fixes former cp1252 console output issue.
- Real plan registration test: **91 task IDs + 173 artifact IDs + 40 two-document join cases = 304/304 exact structural tests PASS**, checked against PLAN data from same checkout, not an independent human semantic gold corpus.
- Current CI data had **91 tasks, 173 registered artifacts, 209+ Markdown sources / 2152+ sections**, as indexed from its specific checkout. The authoritative plan is changing concurrently; do not infer current plan version from earlier reports.

### Search quality experiment (same input corpus/questions)
100 sampled real Markdown document headings, identical fixed queries, top-5 **document recall**:
- Plain BM25 baseline: **94/100**.
- New nine-times heading-weighted BM25: **100/100**.
- Median latency ~21.02 ms vs 20.79 ms in last sampled Linux environment, cache and runner dependent.
This is *source-derived heading self-retrieval*, NOT open-ended natural language understanding or independent norm source relevance. Missing documents outside indexed roots are out of scope. This result justified ranking change without adding a vector DB.

### Token proxy: known two-artifact join
In GitHub Actions query `ART-APA-RU-JUNCTION-NORMS ART-APA-CSE-RESEARCH`:
- Full raw current plan: **77,829 o200k_base tokenizer tokens**.
- Compact source/task relation response: **359 o200k_base tokenizer tokens**.
- Shared task is included under hard 1,600-character budget; no-long-URI truncation vulnerability.
This is **not** actual billed GPT-6 token consumption; no tool-schema, prompt-cache, reasoning, retry, index LLM or unverified semantic recall expenses counted. No generalized 217x performance claim.

## Security and audit defects fixed, measured as test cases
1. A short budget previously dropped the very task connecting two documents. Shared task goes first; full URLs are deferred exact-ART lookup.
2. Source byte SHA previously didn't attest SQLite index body. Now FTS snippets/heading/line/class must match original source bytes; poisoned FTS rows return `INDEX_TAMPERED`.
3. New/deleted/changed documents not among top hits previously went unnoticed; repo-file path/size/mtime manifest now returns `STALE_INDEX` (top-K still gets SHA byte readback). Same-size/same-mtime adversarial changes outside top-K remain uncovered without immutable git-index attestation.
4. Default MCP source class could include archived data; operator-owned allowlist now blocks `ARCHIVED_SOURCE` and `OTHER_DOCUMENT` unless explicitly allowed. This is class gating, not a full multiuser/ACL security framework.
5. Windows `cp1252` source read and JSON stdout errors found and fixed; actual Windows command tested, not merely Linux.
6. FTS output now chooses a best matching section per distinct file so a dense report does not monopolize top-K.
7. `mode=plan` requests do not run full text search, never issue claims and report total eligible candidate count separately from displayed top 5.

## Completed research-only boundary, what's *not* claimed complete
- No merge to `main`, product integration branch, native Archicad add-on or working PLN; no task status or claim updated by this work.
- No proof of official SP text applicability or reviewed numeric formula / actual BIM model readback; source rule remains `design_only` and `NOT_VERIFIED`.
- No automatic ChatGPT plugin/MCP installation on the user's Windows host. The user or an authorized computer-use process must register local stdio MCP server in a compatible client; tool was tested in CI only.
- No independent code review was submitted/approved as separate actor, although code was merged into **research-only** hub after full two-platform CI and developer's adversarial audit. **Production admission requires independent audit and project-governance checks.**
- No 80+ human-judged *semantic* benchmark or actual GPT-6 end-to-end billable token A/B across approaches. Source-title 100/100 must not be misreported as open-ended search quality.
- No automatic multi-document semantic field-level impact inference; only reviewed declared/typed links may be asserted, otherwise `UNKNOWN` / `RECHECK_REQUIRED`.

## Actual user-side entry point
From a Windows clone of the canonical research branch, run `tools\apa_knowledge_graph\Setup-APA-Knowledge.cmd`. This builds the source-derived indexes and prints a valid optional MCP stdio command using the installed Python; `mcp==2.3.0` is needed only in a compatible local client environment. Unlike running source tools in CI, this requires local clone and explicit user permissions. **Do not imply it is currently running or installed on the user's machine.**

Research artifacts: [preceding structural hardening](apa-gpt-knowledge-gateway-hardening-acceptance-20261013.md), [source-locked field dependency](apa-pr69-pr68-real-lineage-token-benchmark-20261013.md), [initial one-tool MCP gateway](apa-unified-gpt-mcp-retrieval-gateway-20261013.md). Candidate task admission: [TASK_PROPOSAL_V1](../../control/proposals/APA-CAND-20261013-knowledge-impact-gateway.md) remains unaccepted.
