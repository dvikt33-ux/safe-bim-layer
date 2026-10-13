# APA Knowledge Impact POC — read-only, token-bounded, audited

**Status (2026-10-13): WORKING OFFLINE PROTOTYPE, NOT PRODUCTION/MERGED.**
Draft PR [#69](https://github.com/dvikt33-ux/safe-bim-layer/pull/69) targets only the existing research hub branch. Does not edit `main`, PLN, APX, existing publisher, controller, task claims or statuses. No API key, embedding model, server, new task controller, or external paid tool required.

This is an **execution of a useful first slice**, not just a research memo. It builds a derived index from the current `PROJECT_PLAN.json` and answers exact task, artifact impact, bounded multi-document join, task descendants and **explicit field-value change** queries through local Python. It does **not** claim to have extracted every semantic link in the GitHub library or to know real normative field dependencies automatically.

## Latest hardening acceptance (2026-10-13)

**[92 tests PASS / 304 real-PLAN structural queries / 209 Markdown files and 2142 indexed sections](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38327961036).** On a real checkout the evaluation resolved all 91 tasks, all 173 artifacts and 40 pairs of related artifacts against direct plan metadata, with no disagreements. This is not independent natural-language relevance evidence. The plan-mode query counted **18 potential unclaimed tasks**, offered five candidates, and never issued a claim. Source manifest now detects new, missing or stat-changed Markdown before search; selected snippets additionally require exact text/section/class byte-readback from the original file. Poisoned SQLite cached snippets and false source classification return `INDEX_TAMPERED` with **no excerpts**. This is integrity hardening, not a guarantee of legal/normative trust or global cryptographic rehash of every unreturned source.

The complete source-linked evidence, failure modes and required independent review are preserved in [canonical research hardening report](../../docs/research/apa-results/runs/2026-10-13/apa-gpt-knowledge-gateway-hardening-acceptance-20261013.md).

## Files

- `graph.py`: `build`, `task`, `artifact`, `descendants`, `field-impact`. Explicit normalized task/artifact reverse maps and revision fingerprint, source read-only; no implicit graph inference.
- `multidoc.py`: combine 1–16 documented artifact IDs; return only a small set of task cards, shared evidence refs, citation provenance flags and count of omitted results.
- `delta.py`: compare authoritative plan versions or field-value snapshots; report exact changed records / keys and only their candidate impacts.
- `sections.py`: build a disposable SQLite FTS5 **section-level** index for allowlisted Markdown roots, split documents by heading/line, search only top-K snippets, verify original source-byte SHA-256 before returning; tag result origin as `ARCHIVED_SOURCE`, `RESEARCH_RUN`, `PROJECT_CONTROL`, `OTHER_DOCUMENT`. **Class is a path label, not a normative approval**. Can scope by class.
- `tests/`: negative tests of cross-project-class contamination, proposed vs verified links, source pinned digests, stale index, cycle termination, content/value diff, authorization flags, no plan changes, CLI budgets, real APA plan regression.
- `.github/workflows/apa-knowledge-impact-poc-ci.yml`: read-only `pull_request` workflow, Python 3.11 stdlib, no token persistence, derived JSON in GitHub Actions temporary directory.

## Run in a checkout of this branch

```sh
python -m unittest discover -s tools/apa_knowledge_graph/tests -v

python tools/apa_knowledge_graph/graph.py build \
  --plan docs/research/apa-results/control/PROJECT_PLAN.json \
  --out /tmp/apa-knowledge-index.json

python tools/apa_knowledge_graph/graph.py task \
  --index /tmp/apa-knowledge-index.json \
  --verify-plan docs/research/apa-results/control/PROJECT_PLAN.json \
  --id APA-P70.A11.S03

python tools/apa_knowledge_graph/graph.py artifact \
  --index /tmp/apa-knowledge-index.json \
  --id ART-APA-RU-JUNCTION-NORMS --limit 5

python tools/apa_knowledge_graph/multidoc.py \
  --index /tmp/apa-knowledge-index.json \
  --artifacts ART-APA-RU-JUNCTION-NORMS ART-APA-CSE-RESEARCH \
  --max-tasks 5

# Content retrieval without reading every Markdown file into GPT:
python tools/apa_knowledge_graph/sections.py build \
  --root docs/research/apa-results --out /tmp/apa-sections.sqlite

python tools/apa_knowledge_graph/sections.py search \
  --index /tmp/apa-sections.sqlite --query "кровли" \
  --source-class PROJECT_CONTROL --limit 3 --max-snippet 160

# Different canonical plan versions:
python tools/apa_knowledge_graph/delta.py plan \
  --before old-project-plan.json --after new-project-plan.json --limit 10

# Exact field-level data needs an independently authored, reviewed
# APA_FIELD_LINEAGE_V1 and two APA_FIELD_VALUES_V1 snapshots:
python tools/apa_knowledge_graph/delta.py fields \
  --before old-field-values.json --after new-field-values.json \
  --index /tmp/apa-knowledge-index.json \
  --lineage reviewed-field-lineage.json --limit 10
```

On Windows, replace `/tmp/apa-knowledge-index.json` with a temporary JSON path outside the source repo. `--out` refuses to overwrite an existing file; create another temp filename for a rebuild. No plan/PLN writes. For the `task` query, `--verify-plan` rejects a stale derived index.

## Source-backed results, not invented benchmarks

An initial Actions execution [38320136500](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38320136500) for original POC commit **PASSED 24 tests** plus read-only real-plan build and two separate real-plan queries. Job logs report:
- Source canonical plan revision **126 at CI checkout**, 91 tasks, 166 artifacts (the earlier research memo saw rev 125).
- `ART-APA-RU-JUNCTION-NORMS` direct registered referencing tasks **15**; CLI with `--limit 5` returned 5 and `omitted=10`, all labelled `POSSIBLE_IMPACT`.
- Multi-document join `ART-APA-RU-JUNCTION-NORMS` + `ART-APA-CSE-RESEARCH` completed with `max_tasks=5`. Both are flagged `UNPINNED_OR_UNVERIFIED_URI` because their current URIs point to a moving feature branch.
- A later Actions run [38320696467](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38320696467) passed **43 tests**, indexed **204 actual Markdown files / 2,113 sections**, and read back bytes for returned hits. **Adversarial failure found**: for a broad query `кровли`, the first unfiltered hit was a research gold-query report, not a normative primary source. This motivated the subsequent source-class filtering; a later CI result must confirm the new filter.
- Latest scoped-search run [38320830932](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38320830932) **PASS: 45 tests**, 204 files / 2,113 sections; for `кровли` with `source_class=PROJECT_CONTROL` returned 1 roadmap section and did NOT return the previous research gold-set hit. This verifies provenance class filtering, **not normative correctness**.
- Independent GitHub source comparison: plan rev 125 blob `e6af8b67d2366ecf747c78caad250170ce11e734` vs rev 126 blob `bfdef0d7653ff40bef9d402888f3ff27ced0e15e` changed exactly one task `APA-P70.A11.S03` (status PARTIAL → IN_PROGRESS, owner, lease_until, claim_ref), zero artifact records. Only a scheduling-state delta, not a norm/calc invalidation.
- These are **observed functional checks**, not a corpus-wide semantic benchmark or measured billed GPT-token reduction.
- New stale-index and pinned-revision guards have been added after the first run; their separate CI result must be rechecked before calling the latest head PASS.

GitHub: https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38320136500

## Verified PR68 field lineage and tokenizer proxy (2026-10-13)

The **existing TDK normative compiled-block routing is reused**, not recreated. Relevant upstream, source-read and SHA-locked at PR68 HEAD `29aa06a6e9bbef0d991bea922e1ad4101ab29bdd`:
- `01_Normative_Base/_Machine/retrieval_policy.yaml` already requires `compiled_blocks_primary_retrieval_reserve` and prohibits a normative full-library scan.
- `residential.izhs.yaml` exact architecture/details route selects `IZHS.ROOF.DETAILS`, without MKD/TRC fallback.
- Existing Central release whitelist and `IZHS.ROOF.DETAILS` both name `ROOF-VENT-CHANNEL-TABLE-A2-001`.
- Rule declares required parameters `roof_slope_length_m` and `roof_slope`, but does **not** implement an approved numeric calculation.
- The source set is `design_only` and quarantined. `APA-P70.A02.S02` cites PR68 as an artifact; a task-artifact relationship is traceable, but this alone does not prove conformity or complete field-level propagation.

The new `machine_adapter.py` reads **exactly six pinned files** via GitHub REST (existing SOURCE_LOCK + exact route, release, block, catalog, rules), verifies each Git blob SHA-1 and five independent SOURCE_LOCK SHA-256 entries, then emits a minimal `APA_REAL_SOURCE_DEPENDENCY_CHAIN_V1`. It rejects unlisted paths, moving branch names, another building class, missing whitelist entries, tampered content or attempted normative authority promotion. It does not modify PR68 or `PROJECT_PLAN.json`.

Verified Actions [run 38323012649](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38323012649) **PASS 56 tests** and a real source GitHub byte readback. A simulated `roof_slope_length_m` change `10→12` outputs `RECHECK_REQUIRED_NOT_RECOMPUTED`, with `normative_authority=false` and `engineering_acceptance=NOT_VERIFIED`. Values 10 and 12 are **synthetic**, not measurements of a user's PLN.

Follow-up Actions [run 38323164778](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38323164778) **PASS 56 tests**. Using `tiktoken==0.14.0` and encoding `o200k_base` on the exact same machine-source probe:

| Model-visible *text payload comparison* | UTF-8 bytes | `o200k_base` proxy tokens |
|---|---:|---:|
| Raw APA plan + six exact upstream source files | 342,057 | 92,866 |
| Raw six exact upstream source files only | 62,137 | 16,861 |
| Correct compact impact answer payload | 393 | **100** |

This is a **text tokenization proxy**, NOT measured GPT-6 billed tokens or a head-to-head recall/latency benchmark. Tool schemas, hidden reasoning, indexing, retries, correction rounds and question-to-evidence recall are excluded. Compact response / raw source is ~169× fewer tokenizer-proxy tokens for this *particular precise question*; a normative legal claim would require primary source excerpts and may cost more. These ratios cannot be generalized to arbitrary corpus questions.

Reproducible CI example:

```sh
python tools/apa_knowledge_graph/machine_adapter.py \
  --index /tmp/apa-knowledge-index.json \
  --out /tmp/apa-real-machine-chain.json \
  --benchmark-plan docs/research/apa-results/control/PROJECT_PLAN.json \
  --change-field roof_slope_length_m --before 10 --after 12
```

The repository's existing `PyYAML==6.0.3` and independently chosen `tiktoken==0.14.0` are used **only for this optional PR68 adapter/benchmark**, not for the stdlib core graph/search or any model inference calls.

**Major missing gate:** A complete chain **official SP clause edition → validated normative calculation → project material/roof system → actual PLN field → engineering result → regression test** is NOT yet available. This first real chain verifies machine-source routing and declared parameter relationships, not numerical engineering semantics.

## One-tool GPT gateway and optional modern MCP adapter (2026-10-13)

The read-only `gateway.py` combines the graph and section index into a **single call**. The caller can use:
- `APA-P70.A02.S02`: exact task status and dependency IDs, **without a full plan/context dump**.
- `ART-APA-RU-JUNCTION-NORMS ART-APA-CSE-RESEARCH`: join **multiple registered documents** and show tasks referencing both. Reference is NOT field-level impact, and moving branch URIs remain explicitly unpinned.
- `кровли` with `--source-class PROJECT_CONTROL`: source-byte-verified snippets from bounded diverse documents, with repo-relative line/source paths and optional candidate task IDs. `mode=normative` may supply leads but will always report `NOT_VERIFIED_OFFICIAL_SOURCE`; a path category is never government-source attestation.
- `--mode next`: **potential** unclaimed tasks based on the checkout plan, not actual dispatcher priority or task claim.

Enforcement: one tool-side plan fingerprint comparison on EVERY query; source SHA-256 recheck on returned FTS hits; output capped `--max-chars 400..12000` without silently truncating a citation or declaring an unsupported claim. When budget cannot accommodate a complete minimum card, `BUDGET_TOO_SMALL` is returned and evidence is not fabricated. Repeated headings from the same document are deduplicated in the visible context. The index is a checkout SNAPSHOT; this does not prove the GitHub remote branch has not moved.

Example direct CLI in a current branch checkout:

```sh
python tools/apa_knowledge_graph/gateway.py \
  --index /tmp/apa-knowledge-index.json \
  --plan docs/research/apa-results/control/PROJECT_PLAN.json \
  --query "ART-APA-RU-JUNCTION-NORMS ART-APA-CSE-RESEARCH" \
  --max-chars 1600

python tools/apa_knowledge_graph/gateway.py \
  --index /tmp/apa-knowledge-index.json \
  --plan docs/research/apa-results/control/PROJECT_PLAN.json \
  --sections /tmp/apa-sections.sqlite \
  --repo-root . --query "кровли" --source-class PROJECT_CONTROL --max-chars 1800
```

Optional **official MCP Python SDK v2 adapter**, using `MCPServer` with **one tool `apa_retrieve`**: [MCP SDK v2.3.0](https://pypi.org/project/mcp/2.3.0/). This source is not an obsolete v1 FastMCP API. Do not install this extra dependency unless using an MCP-compatible local host.

```sh
python -m pip install mcp==2.3.0
python tools/apa_knowledge_graph/mcp_adapter.py \
  --plan docs/research/apa-results/control/PROJECT_PLAN.json \
  --index /tmp/apa-knowledge-index.json \
  --sections /tmp/apa-sections.sqlite \
  --repo-root .
```

Transport: **stdio only**, local host launches subprocess and owns the root/index paths. Tool arguments `query`, `mode`, `source_class`, `limit`, `max_chars` do not accept paths or write operations. This is **NOT already connected to this ChatGPT session**, and desktop/host configuration must independently support local MCP. No need to run a public HTTP endpoint for current POC. Neither the connector nor one registered tool magically enforces permissions beyond the local host's process rights.

Untrusted documents remain text data. No source content from the research index is allowed to instruct the model to execute commands, change plans, or promote a rule. `PROJECT_PLAN.json` is still the only task authority. If index/plan mismatch occurs, rebuild the derived index before retrying.

## Trust contract and known limitations

- `depends_on` means task *scheduling*, not a calculation or normative relation. `inputs/evidence` means the task *references an artifact*, not that a changed parameter actually invalidates the task.
- `SOURCE_VERIFIED` field edges are **declared in the supplied lineage file**. The current offline query validates edge shape, scope and pinned 40/64 hex source revision but does **not perform independent GitHub byte readback or semantic verification**. The result reports `runtime_evidence_readback=NOT_PERFORMED`. Do not load unreviewed AI-inferred edges as `SOURCE_VERIFIED`.
- For normative IZHS/MKD/TRC, no cross-class field edge is accepted in this POC. General rules shared between classes will need a separate explicit reviewed applicability contract.
- Empty field edges do **not** mean no impact; output is `UNKNOWN`. A linked document can be unreadable or superseded; retrieval must validate exact version, edition, permissions and facts before authoritative answers.
- `source_revision` in the lineage is a syntactically pinned digest; it is **not an attestation of its authenticity**. Production needs independent byte readback/receipt signatures before trusting links.
- No automatic propagation to derived documents and no automatic edit/claim/DONE. Existing `TASK_PROPOSAL_V1` → independent `TASK_REVIEW_V1` → CAS `PROJECT_PLAN.json` protocol remains untouched.
- The FTS lexical backend is **not** a normative source classifier: it distinguishes path classes and can filter reports out, but cannot attest official SP scope, effective editions, truth or Russian stemming. A zero-hit scoped query does NOT mean the regulation does not exist; it can be outside the GitHub checkout.
- No remote change watcher or public MCP HTTP endpoint exists; a **local stdio MCP v2 adapter** has passed tests, but is not installed or connected to this user's ChatGPT client. Run as an explicit operator-owned local tool only after host/security review.
- Index contains source URI and task title; do not serve it publicly unless access restrictions and licensed material controls are checked.
- Early raw-to-compact character ratios reported by prior research measure **text size**, not billed GPT tokens or retrieval quality. No final DB technology selection was made.

## Alternative approaches audited in parallel

| Open-source / standards | What improves this POC | Why not indiscriminately install it yet |
|---|---|---|
| [Bazel Skyframe](https://bazel.build/versions/8.5.0/reference/skyframe), [Nx affected](https://nx.dev/docs/features/ci-features/affected) | Correct **reverse dependency closure**, value-level change pruning, separation of execution-order vs true input dependence | Generic build graph does not know SP edition, legal scope, APA receipt provenance |
| [DVC params](https://doc.dvc.org/command-reference/params) | Track only nested YAML/JSON parameters a downstream stage reads | Replacing publisher/controller would add second authority. Borrow the algorithm, not task orchestration |
| [OpenLineage](https://openlineage.io/docs/spec/facets/dataset-facets/column_lineage_facet/) | DIRECT vs INDIRECT field propagation and exact input-to-output mappings | A field lineage schema **pattern**, not turnkey GitHub normative source verification |
| [Graphiti](https://github.com/getzep/graphiti), [LlamaIndex PropertyGraphIndex](https://developers.llamaindex.ai/python/framework/module_guides/indexing/lpg_index_guide/) | Rich temporal graph search, typed relations, optional embeddings + LLM extraction | Default extractors/query often invoke an LLM: may be more token-expensive, false graph edges must not overwrite verified provenance |
| [Kuzu](https://github.com/kuzudb/kuzu) | Fast embedded graph queries and prior Graphiti/CodeGraphContext backend | **Repository archived October 10, 2025**; not an appropriate unexamined long-term default for new APA infrastructure |
| SQLite or another actively maintained graph store, [Qdrant](https://github.com/qdrant/qdrant), [LanceDB](https://github.com/lancedb/lancedb) | Indexed graph and hybrid semantic retrieval for enormous corpus | Backend choice alone does **not** reduce GPT tokens if the API returns entire docs. First measure bounded retrieval and correctness |

**Audit correction:** A previous recommendation suggested Windows embedded Kuzu through CodeGraphContext as though this settled maintenance risk; it does not. Kuzu is archived. A prospective switch to a newer graph engine needs license/support and corpus token benchmark.

## Next hard gate before merge or scaling

1. Independent review of link provenance, untrusted `SOURCE_VERIFIED`, role permissions and source immutability; improve logic as failures are found.
2. Complete field-level lineage for 5–10 real docs in one narrow area (exact clause/attribute/formula/test/PR/S-ID), with source commit and human-reviewed relationship type, and validate value changes.
3. Benchmark on at least 80 grounded cross-document questions: correctness, stale-link rate, false impact/missed impact, raw vs model-visible input+output tokens including retries/tool schemas, p50/p95 latency. Same-corpus compare exact+graph only vs hybrid+reranker vs LLM-first graph.
4. Pass independent `TASK_PROPOSALS_AND_AUDIT.md` task admission without bypassing `PROJECT_PLAN.json` governance; do not merge into live publisher/controller as a side effect of creating PR.

**Go/no-go**: reliable verified evidence + minimal *total* tokens per correct answer wins, not shortest code or prettiest portal.
