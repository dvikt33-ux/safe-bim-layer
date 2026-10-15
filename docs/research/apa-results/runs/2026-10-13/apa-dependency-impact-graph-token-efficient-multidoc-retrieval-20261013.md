# APA — Provenance + Field Lineage + Incremental Impact Graph: token-optimal multi-document retrieval
2026-10-13 | SOURCE_RESEARCH + VERIFIED_APA_STRUCTURE + DETERMINISTIC_QUERY_PROBE + ARCHITECTURE_PROPOSAL

## Decision and limits
**New requirement**: GPT must combine dependent documents and exact facts, identify downstream changes, detect contradiction and stale evidence, and choose the next verifiable project action without reading an entire GitHub library. Primary metric: model-visible tokens / independently correct verified cross-document conclusion or actionable next task (including tool overhead, retries and any model-based indexing).

**Not implemented**: No live document index, graph database, MCP gateway, new automation, cross-doc field extraction, query quality benchmark, independent audit or plan claim has been deployed. Do not imply changes to main, PLN/APX, existing controller, its statuses or source evidence. This proposal extends [token optimal retrieval architecture](apa-token-optimal-retrieval-architecture-20261013.md); it is not a parallel plan controller and not a V2 publisher receipt.

## Pass A — Actual APA baseline and deterministic probe
Source pinned at inspection: [PROJECT_PLAN.json](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/PROJECT_PLAN.json), Git blob e6af8b67d2366ecf747c78caad250170ce11e734, rev 125.

Existing roles: 91 S-ID task records, 166 ART-ID artifacts, 16 topics; authoritative `PROJECT_PLAN.json` with `depends_on`, `related`, `inputs`, `evidence` and machine-generated `RELATIONSHIPS.md`. The report protocol/receipt source is immutable and has GitHub REST readback. These edges already form a **task execution DAG and cited-artefact connections**; they are not field-level formulas or normative applicability semantics.

Concrete probe executed by parsing whole plan *inside connected-tool programming*, returning only projection to model context:
- `ART-APA-RU-JUNCTION-NORMS` appears as input/evidence in **15** task records (not automatically 15 affected outputs).
- Minimal task row projection for these tasks: **1,683 characters**, versus **264,921** characters of full raw plan; ≈157.4× fewer characters for THIS query, with coverage limited to registered fields.
- `APA-P70.A02.S02` directly gates `APA-P70.A05.S01` and `APA-P70.A06.S01` via `depends_on`; reverse reachability yields 14 descendant task nodes, which indicates scheduling relationship, **NOT proved semantic impact** from changed norm text.
- A 15-task bulk mark as stale would be **unsound**: each task may rely on a distinct norm clause; the existing graph has no confirmed field-level dependency. This is the highest-priority missing data before auto-propagation.
- [TASK_PROPOSALS_AND_AUDIT.md](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/TASK_PROPOSALS_AND_AUDIT.md) requires independent review, CAS, test and readback before new project tasks; do not bypass it by automatically writing new tasks.

## Pass B — Relevant checked open-source techniques, not just attractive product names

| Source | Verified design element | Recommendation / rejection condition |
|---|---|---|
| [Graphiti](https://github.com/getzep/graphiti), [episodes](https://help.getzep.com/graphiti/core-concepts/adding-episodes) | Temporal fact validity, provenance/episodes, prescribed edge ontology, incremental graph updates; hybrid keyword+vector+graph retrieval; MCP. | Evaluate optional enrichment / temporal retrieval. **Not default authority**: source extraction calls an LLM and default quickstart requires a model key/database. Extra model tokens and erroneous inferred links must be counted. [Configuration](https://help.getzep.com/graphiti/configuration/llm-configuration) |
| [DVC pipeline params](https://doc.dvc.org/user-guide/pipelines/defining-pipelines) | Dependencies can point to **specific nested YAML/JSON parameter keys**, and invalidate only stages which read changed keys. [Reproduction](https://doc.dvc.org/command-reference/repro) can recompute affected descendants. | Model **fine-grained value dependencies and minimal re-evaluation**. Adapt mechanism; do not need to replace APA publisher with DVC by default. |
| [OpenLineage field lineage facet](https://openlineage.io/docs/spec/facets/dataset-facets/lineage/), [job lineage](https://openlineage.io/docs/spec/facets/job-facets/lineage/) | Explicit field-to-field transformations, DIRECT/INDIRECT semantics, individual output-target mapping and provenance. | Strong ontology pattern for value/paragraph/result links across docs; **do not infer all-inputs-to-all-outputs Cartesian edges**, which lead to mass false impact. |
| [Nx affected](https://nx.dev/docs/features/ci-features/affected) | Use Git diff + dependency DAG to identify changed and downstream targets instead of scanning/building every project. | Adopt **change-driven reverse traversal**, with conservative fallback if dependencies are incomplete. It does not validate norm legal applicability. |
| [Microsoft GraphRAG](https://github.com/microsoft/graphrag) | Global/local community retrieval; source admits LLM graph-indexing cost and project maintenance mode. | Research baseline on corpus synthesis, not default fact authority or cheapest-token path; global summaries risk hiding changed detail. |
| [Cognee](https://github.com/topoteretes/cognee) | Source refs, evidence associated with graph edges and explicit contradiction relations documented in repository (source [CLAUDE.md](https://github.com/topoteretes/cognee/blob/main/CLAUDE.md)). | Optional graph-memory research; test edge evidence and contradictory facts. No second task/status authority. |
| [LanceDB](https://github.com/lancedb/lancedb) / [Qdrant](https://github.com/qdrant/qdrant) | Hybrid lexical/dense and filtering, possible rerank prior to GPT. | Query-side **recall candidate retrievers**, secondary to exact ID + provenance/impact engine; A/B on same mixed normative/technical queries. |

Key audit: semantic vector similarity is *NOT* dependency, a mere document reference is *NOT* change propagation, a task `depends_on` edge is *NOT* a calculation derivation, and an LLM-extracted relation is *NOT* verified normative applicability.

## Pass C — typed graph design: four planes, one canonical source

### 1. Source and immutable fact plane
Nodes: `REPO_REF`, `DOCUMENT_VERSION`, `SECTION`, `FIELD`, `CLAIM`, `NORM_RULE_VERSION`, `PR`, `TEST_RESULT`.
Each carries stable `logical_id`, `version_id` = repo@commit:path#anchor or source blob hash, `content_sha256` (actual content, not guessed), `document_edition`, `project_class` (IZHS/MKD/TRC), `observed_at`, `valid_from`, `valid_to` where supported, `source_evidence_ref`, `verification`, `acl` and extractor version. Norm effective date must be verified independently; Git commit time is not legal effective date. A claim is never overwritten to represent a new version without history.

### 2. Calculation / semantic lineage plane
Typed directed edges, preserving what part of source changed:
- `DERIVED_FROM` for exact value/formula/expression, with `input_field`, `output_field`, units, conversion and transform version.
- `CONSTRAINED_BY` for design decision or element restricted by a verified clause with applicability conditions.
- `USES_PARAMETER` for specific area / population / height / building class, not merely whole document.
- `IMPLEMENTS` for code or BIM check implementing a requirement, and `TESTED_BY` for existing real test evidence.
- `SUPERSEDES` / `CONTRADICTS` for temporal conflicts with source attribution and independent confirmation state.
- `REFERENCES` / `MENTIONS` are weaker, **non-propagating** edges unless separately validated.

`edge` contract:
```json
{
  "from": "norm:edition-x:section-y:constraint-z",
  "to": "calc:project-IZHS:opening-clearance",
  "kind": "CONSTRAINED_BY",
  "scope": {"project_class":"IZHS", "archicad_major":29},
  "source_commit": "<actual SHA at indexing>",
  "source_anchor": "<exact section or machine field path>",
  "input_fingerprint": "<actual validated hash>",
  "transform_id": "validated_check:wall-roof:v1",
  "verified": false,
  "relation_status": "PROPOSED",
  "impact_policy": "REVIEW_REQUIRED"
}
```
This is a **schema illustration**, not a real norm or established edge. Proposed/derived edges cannot silently authorize a final conclusion.

### 3. Controller / execution plane
Read-only projection of existing `PROJECT_PLAN.json` and issued immutable receipts. Edges `depends_on`, `related`, `uses_artifact`, `produced_by_run`; never mutate `READY`, `PARTIAL`, `DONE_PUBLISHED` from retrieval graph. Retrieval may propose next tasks, but admission is through existing independent TASK_PROPOSAL_V1 / TASK_REVIEW_V1 with GitHub CAS and CI.

### 4. Search / context plane
Exact-ID map + topical hierarchy + verified field graph + hybrid BM25/embedding + optional reranker, all indexes **derived and disposable**, not new sources of truth. Retrieve a bounded **connected evidence subgraph** based on named entities and relations, not 20 flat chunks. Expand only source passages needed to substantiate conclusion; return compact fact bundles, conflicts and citations; fetch full source only on request or contradiction.

## Pass D — incremental document updates and impact propagation (no universal library rescan)

1. GitHub webhook/PR compares previous and current **pinned source** commits; detect changed paths then section IDs / structured field-value hashes. Avoid expensive model-based extraction on unchanged document versions.
2. Mark impacted **source nodes** and locate outgoing `DERIVED_FROM` / `USES_PARAMETER` / `CONSTRAINED_BY` verified edges with scope/edition gating. Compute reverse dependency closure only for affected targets; deduplicate affected nodes.
3. Separate outputs: `DETERMINISTIC_RECOMPUTE` (proven formula, approved pipeline), `VERIFY_REQUIRED` (norm/design change or uncertain relation), `NO_IMPACT_PROVEN` (confirmed unrelated), `COVERAGE_UNKNOWN` (missing field mapping). **Do not equate no discovered edge with no impact.**
4. Batch recompute pure safe derived summaries/fingerprints in topological order, store new version & new evidence pointers; existing accepted norm/version preserved until independently requalified.
5. Surface status as **read-only impact alert** with sources, old/new values, impacted docs/tasks/tests and recommended checks. Any actual document writing, BIM editing, task status change or scheduler priority update requires its own existing authorization process.
6. Cache by content SHA + field signature + dependency fingerprint + permission scope, and invalidate **only the minimal affected set**. Old revisions remain queryable for comparison; avoid leaking private content through global caches.

### Safety / audit conditions
- For legally binding/normative facts, `APPROVED` and applicability cannot be inferred from embeddings or LLM alone. Fresh government source editions, scope and effective dates must be checked.
- A changed doc may be a formatting-only change; distinguish raw hash from normalized/semantic field difference, but when uncertain mark `VERIFY_REQUIRED`, not clean.
- Dependence cycles allowed for `REFERENCES` but forbidden for acyclic computation stages unless special fixed-point semantics proven. Contradictory revision definitions result in `CONFLICT`, not merge.
- Cross-class IZHS/MKD/TRC hard wall, except where source explicitly authorizes shared general rule.
- Credential, private source and licensed normative content access must be enforced **before** indexing/result display. Do not put full commercial source text in public GitHub Pages.
- Open-ended graph traversal causes token explosion; require hard max depth, permitted edge kinds, hard max nodes, rule-scoped expansion and compact graph-level summaries.

## Pass E — what a real query needs to return
Illustrative only (values are not real normative numbers):
```text
question: "Изменился пункт СП о проёме. Что перепроверить и что сделать следующим?"
query mode: CHANGE_IMPACT + NEXT_ACTION
source: norm / verified clause / old SHA / new SHA
change: field <old> -> <new> | evidence source
direct affected: 2 verified formula nodes
indirect affected: 1 calculation, 1 drawing/check, 1 existing S-ID
uncertain: 2 references, VERIFY_REQUIRED, not silently propagated
not affected: 9 nodes (only when absence of effect actually proven)
action: existing eligible S-ID from latest PLAN if dispatch rules allow;
        else TASK_PROPOSAL candidate with independent review required
citations: pinned source and result/test receipts, status
expand: optional exact section fragments; GPT need not read the whole documents
```
The index must **precompute affected deltas** on source changes and store compact versioned impact reports so an ordinary query is cheap. If index freshness is unknown, answer must say so.

## Pass F — independent falsification / validation plan

Before calling this implemented or "best", conduct **joint** quality + model-token A/B tests:
- Multi-doc grounded tasks: 100+ questions across exact ID, two-document comparison, three-to-five-document joins, normative rule-version conflicts, value-level propagation, task readiness, code symbol→rule→test, deliberate missing edges, negative project_class, old vs current source, and cyclic references.
- Positive gold data manually linked to `repo@commit:path#anchor` + all dependent field edges; negative gold cases to catch broad false propagation.
- Variant A: naive GitHub full document fetch; B: exact + task/artefact graph; C: B + field-level lineage + precomputed impact; D: C + hybrid search and local rerank; E: C + Graphiti inferred temporal enrichments (count extraction/inference cost).
- Compare **total GPT model-visible tokens per CORRECT fully cited answer** including schemas, failed calls, follow-up reads and LLM-based indexing where used; P50/P95 latency, edge precision/recall, impact false-negative and false-positive rates, staleness/edition errors, memory/disk/index time, repo ACL correctness.
- Test concrete source data change, unchanged dependencies, two simultaneously changed upstream fields, stale branch, commit race, removed file, normalization-only edit, conflicting norm editions, missing old version, reverse source correction and cycles.
- Fail-safe: false-negatives in safety-critical normative impact are unacceptable; an `UNKNOWN` alert is safer than falsely certified `NO_IMPACT`. Production acceptance thresholds to be independently agreed before test (no invented achieved rates).

## Priority, without replacing project plan

The first vertical slice with greatest likely value is a **read-only graph source adapter + reverse artifact/task index + SHA-based change impact cards**, using current PLAN/receipts, then a **precise field lineage** prototype on 5–10 real mixed docs (one actual norm clause, one rule, one calculation, one validation, one S-ID). Benchmark before choosing Qdrant/LanceDB/Graphiti as default infrastructure. The existing TASK_PROPOSALS_AND_AUDIT protocol must decide whether this extends `APA-P50.A01.S03` / `APA-P00.A02.S03` or needs a new substep. No new S-ID or status change is proposed as already approved.

## Provenance of this research
Actual GitHub connected reads of canonical current `PROJECT_PLAN.json` and existing proposal protocol; direct artifact-to-task reverse scan and conditional task descendant traversal; upstream docs and official GitHub repositories visited via Opera and web. No library-wide benchmark, code deploy, repo grep, or field-level normative mapping conducted. Conclusions distinguish source-supported capability from recommendations and untested assumptions.
