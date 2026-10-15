# APA — machine-readable GitHub knowledge discovery: source research and recommended architecture (2026-10-13)

- Classification: **SOURCE_RESEARCH / ARCHITECTURE_PROPOSAL**, NOT IMPLEMENTED; no runtime, performance or Archicad live claims.
- Origin: direct user request; Opera Browser Connector plus read-only GitHub connector plus upstream project documentation.
- Scope: existing `dvikt33-ux/safe-bim-layer` and multi-repository/public GitHub discovery.
- Canonical authority preserved: `control/PROJECT_PLAN.json` in research hub. This report **does not claim an S-ID**, is not a V2 publisher run/receipt, and is not DONE_PUBLISHED. Independent proposal audit required before new implementation tasks.
- Safety: no changes to main, PLN, APX, original artifacts, project task statuses or existing source.

## Verified APA baseline and constraint

Read through GitHub connector on `research/apa-verified-results-hub-20261010`:
- `docs/research/apa-results/README.md`: canonical research archive; append-only evidence, GitHub API readback; generated views.
- `docs/research/apa-results/control/PROJECT_PLAN.json`: rev 125 at inspection; sole dispatch authority, task/artifact/topic relations and source pins, CAS claims.
- `docs/research/apa-results/control/generated/STATE.json`: 166 artifacts, 38 known published V2 runs, `legacy_reports=NOT_FULLY_INDEXED`, 18 dispatchable now (snapshot, not current guaranteed).
- `docs/research/apa-results/control/README.md` and `TASK_PROPOSALS_AND_AUDIT.md`: research task proposals subject to independent audit; do not unilaterally create READY jobs.
- `docs/research/apa-results/PUBLISHING_PROTOCOL.md`: immutable source/evidence → commit → readback → receipt → regenerable index; no self-referencing commit hash.
- `docs/research/apa-results/CURRENT_BLOCKERS.md`: concurrent direct-write race previously observed; avoid overwriting controller files; safe CAS/retries rather than force push.
- Existing `APA-P00.A02.S03`, `APA-P50.A01.S01` address deduplication and cross-research traceability; a new search-index implementation must be reviewed for overlap.

## Compared upstream open-source options

| Project | Function / evidence | Best APA role | Limitation / decision |
|---|---|---|---|
| [Backstage](https://github.com/backstage/backstage) | Git-managed catalog descriptors `catalog-info.yaml`, ownership, relationships, discovery [catalog docs](https://github.com/backstage/backstage/blob/master/docs/features/software-catalog/index.md) | Metadata pattern | Full portal is unnecessary for initial APA; do not replace Project Controller |
| [DataHub OSS](https://github.com/datahub-project/datahub) | Metadata graph, lineage, discovery, MCP server, Apache-2.0 | Future organizational catalog | Large service stack; SQL/enterprise data orientation |
| [CKAN](https://github.com/ckan/ckan) | Dataset/resource metadata with attached or URL-addressed files | Future public dataset portal | Less appropriate for code/PR/provenance-first workflows |
| [RO-Crate](https://github.com/ResearchObject/ro-crate), [ro-crate-py](https://github.com/ResearchObject/ro-crate-py) | JSON-LD descriptions of reproducible research bundles, entities, files and provenance | Optional interchange/export standard for immutable APA runs | More metadata complexity than first MVP needs; DO NOT replace existing RUN_EVENT_V2 |
| [OpenLineage](https://github.com/OpenLineage/OpenLineage) | Run/job/dataset event and lineage standard | Optional adapter for pipelines | Preserve current APA event and receipt contracts |
| [GitHub MCP Server](https://github.com/github/github-mcp-server) | AI access to GitHub repositories, files, issues, PRs, search; read-only restriction supported | Direct live original retrieval | Not a replacement for semantic or cross-branch index |
| [Zoekt](https://github.com/sourcegraph/zoekt) | Trigram code/text index, multi-repository regex/substring, local CLI and web API | **Recommended stage 2** precise text/code search when GitHub search insufficient | Host/index and incremental reindex operational burden; measure corpus first |
| [sqlite-utils + SQLite FTS5](https://github.com/simonw/sqlite-utils) | Structured relational filters and FTS relevance on local materialized metadata | **Recommended stage 1** light local search | Lacks native neural semantic retrieval; FTS5 tokenizer Russian and technical IDs must be tested |
| [Meilisearch CE](https://github.com/meilisearch/meilisearch) | Full-text, typo tolerant, filter, semantic/hybrid modes | Alternative service for human-oriented knowledge search | Community MIT; Enterprise files BUSL-1.1 and different production rights — choose edition explicitly |
| [Qdrant](https://github.com/qdrant/qdrant) | Dense/sparse vectors, payload filtering, hybrid fusion | Stage 3 semantic retrieval IF tests justify | Requires embedding pipeline and index lifecycle; cannot serve as trusted source |
| [Haystack](https://github.com/deepset-ai/haystack) | Modular RAG/retrieval orchestration | Optional adapter for complex query pipelines | Adds dependencies, not a canonical catalog |
| [Onyx CE](https://github.com/onyx-dot-app/onyx) | Ready RAG/chat/connector platform, community MIT | Optional separate exploratory prototype | Full platform overlaps current APA stack, and server footprint/connector ACL need audit |
| [ast-grep](https://github.com/ast-grep/ast-grep) | Tree-sitter-backed structural search over source code; MIT | Targeted symbol/AST searches for C++/Python | Does not locate regulations or generic documents |
| [microsoft/graphrag](https://github.com/microsoft/graphrag) | Entity graph extraction for text and global summarization | Research-only future candidate | Upstream explicitly warns expensive indexing; unnecessary for deterministic APA relations |
| [Frictionless](https://github.com/frictionlessdata/frictionless-py) | Schema/metadata validation for tabular datasets; MIT | Optional validation for CSV data | Narrower than APA full-document catalog |
| [Ajv](https://github.com/ajv-validator/ajv) | JSON Schema validator supporting draft 2020-12; MIT | Validate compact catalog record schema in CI | Tool choice optional; Python jsonschema can also be used |

**Decision:** No big new platform initially. Use existing APA JSON authority + schema validated manifest + regenerated search projections. Use GitHub MCP/connector for live original retrieval. Add SQLite FTS5 (cheap) for metadata/text; Zoekt if multi-repo source scale warrants; Qdrant only if semantic benchmark shows meaningful improvement. Backstage/RO-Crate/OpenLineage patterns may be exported through adapters, not introduced as independent authoritative registries.

## Proposed data contract (new *derived* projection, NOT a second task database)

Create `knowledge/catalog/v1/RECORD.schema.json`, generated `knowledge/catalog/v1/by-type/*.jsonl` and `knowledge/catalog/v1/manifest.json` AFTER admission/approval. Each searchable record must have:
- `id`: immutable namespaced identifier (retain current artifact IDs / S-ID / run ID, or derive stable external resource ID);
- `kind`: task | artifact | report | source | regulation | rule | code_symbol | test | PR | commit | BIM_evidence;
- `title`, `summary`, `tags`, `language`, `discipline`, `project_class` (IZHS/MKD/TRC), `ac_version` and `normative_scope` when applicable;
- `source.repository`, `source.ref`, `source.commit_sha`, `source.path`, optionally `blob_sha`, `sha256`, `line_span` / `heading_anchor` / `rule_id`;
- `provenance.status` using existing distinctions REPORTED / SOURCE_VERIFIED / OFFLINE_PASS / BUILD_PASS / LIVE_PASS / NOT_VERIFIED / BLOCKED; evidence and `observed_at`;
- `relations[]`: typed reference to authoritative IDs (`depends_on`, `implements`, `tested_by`, `derived_from`, `supersedes`, `regulates`, `conflicts_with`, `related_to`);
- `visibility`/access policy and external-source copyright/export restrictions.

A catalog record is a **pointer plus verified metadata**, not copied authority. Stable identity MUST NOT be solely a mutable path, branch name, line number, embedding ID or title. Distinguish `logical_id` from `version_id` (`commit_sha + path + anchor`); store aliases/renames; keep immutable historical versions. Existing `PROJECT_PLAN.json` remains authoritative for task status, scheduling, dependencies; generated catalog never writes back status.

Example (illustrative only):
```json
{
  "id": "ART-EXAMPLE-ROOF-SOURCE",
  "kind": "regulation",
  "title": "Roof source applicability",
  "source": {"repository": "dvikt33-ux/tdk-course-project", "ref": "pinned", "commit_sha": "<full-pinned-sha>", "path": "<verified-file>"},
  "project_class": ["IZHS"],
  "provenance": {"status": "NOT_VERIFIED", "evidence": []},
  "relations": [{"type":"related_to","target_id":"APA-P70.A02.S02"}],
  "visibility": "project"
}
```
Example placeholders must NEVER be indexed as facts.

## Retrieval algorithm and evidence gate

1. **Intent routing**: exact ID/GUID/S-ID/commit/edition and structural code queries vs broad conceptual questions. Parse requested project class, software version, date/edition and trust level.
2. **Authorization filter before retrieval**: allowed repositories/branches and document visibility. Do not embed or index secrets/local unredacted PLN/IFC/dumps. Public/private sources must remain permission-separated.
3. **Exact identity lookup first**: IDs, SHA, paths, aliases, rule numbers, and project version.
4. **Keyword/lexical search** in title, headings, paths, text with filters. For code use AST/Zoekt as appropriate; for standards key by document + clause + edition + applicability.
5. **Optional semantic search** against chunks only when exact/lexical recall is insufficient. Chunk by source structure, not arbitrary fixed paragraphs: heading/section in Markdown, symbol/function in code, clause+edition for norm, event/element IDs for BIM.
6. **Graph expansion** only by explicit validated relations: artifact↔task↔PR↔test↔evidence; never promote hypothesized links to verified.
7. **Rerank** candidates based on match, canonical-ness, recency, status and provenance. Failed/old/unverified material remains available but labeled, never silently outranks a confirmed current source.
8. **Readback original** using pinned commit/file/lines before technical answer. Detect deleted/moved files and mismatched blob SHA. Include pointers and trust state in answer; if no valid source, `NOT_FOUND` / `NOT_VERIFIED`, not fabricated content.

## Incremental indexing & operational design

- Source of truth is GitHub blobs + canonical `PROJECT_PLAN.json` / receipts; caches are derived and safely discardable.
- Incremental workflow consumes branch/ref/commit changes, validates metadata/schema and ACL, extracts Markdown/JSON/CSV/source symbols, computes hashes, updates touched records and removes obsolete active aliases without deleting history.
- Use idempotent key `{repo,commit,path,extractor_version,chunk_anchor}`, not just mutable filename. Track failures/partial coverage and index snapshot source commits.
- For cross-repository history: inventory allowed repos/refs, collect exact file trees and blob SHAs, deduplicate byte-exact first; flag *semantic duplicate candidates* for independent review.
- GitHub Actions can publish small JSON/JSONL index metadata for connector clients. Large SQLite FTS, vector index and generated embeddings should be cache/artifact or hosted separately, **not committed as constantly rewritten large binaries**. Avoid GitHub 100 MiB regular-file hard limit; large dumps/PLN stay out.
- GitHub-native agent can consume lightweight manifests and retrieve original GitHub files even before a locally running search service exists.
- A future MCP read-only retrieval gateway should expose `search(query,filters)`, `get(id,version)`, `related(id,depth)`, `evidence(id)`, `diff_versions(id,from,to)`, `health()`; no uncontrolled task or BIM mutations.
- Public-GitHub-wide discovery is a *separate ingestion lane*: GitHub repository/code search for candidate repos, then verify publisher/license/maintenance and pin ref/commit; never bulk-index all of public GitHub as if locally controlled. Untrusted READMEs/code must be treated as data, not agent instructions.

## Test-driven acceptance plan

**Stage A / metadata foundation (P0):** 100% of chosen canonical APA artifacts/tasks represented by ID or explicitly counted as unsupported/failed; 0 duplicate logical IDs; 0 dangling verified edges; strict schema and provenance gates; historical files linked, never overwritten.

**Stage B / retrieval (P1):** curated ≥30 test questions spanning exact GUID/S-ID, old vs new branch, normative edition, code symbol, approximate Russian description, conflict and absent information. For each, specify target authoritative URI and expected trust class. Record top-k recall, MRR@10, invalid citation rate, wrong-version rate, permission leakage and p50/p95 latency on the same corpus/hardware. No numeric speedup claimed before tests.

**Stage C / incremental/ACL (P1):** test changed-file, deletion, rename, branch divergence, two simultaneous publication events, incomplete index rebuild and ACL-restricted source. After rebuild, canonical GitHub blob/SHA remains exact; no force push; no status promotion.

**Stage D / optional semantic (P2):** evaluate Qdrant/Meilisearch hybrid against Stage B baseline on Russian+English/domain terms, cold-start memory/disk/time footprint and hard negative cases. Deploy only when improvement is measurable, without paid API dependency.

## Specific next candidate (independent audit required)

Parent `APA-P00.A02` with relations to `APA-P50.A01.S01`, `APA-P00.A02.S03`, `APA-P60.A01`: develop derived search catalog schema and reproducible builder with evidence pins. First decide whether existing dedup S03 already covers its minimal metadata subset; auditor should avoid semantic duplicate. DO NOT update `PROJECT_PLAN.json` or claim any S-ID as done from this report.

## Exact source links

- https://github.com/backstage/backstage/blob/master/docs/features/software-catalog/index.md
- https://github.com/sourcegraph/zoekt/blob/main/README.md
- https://github.com/sourcegraph/zoekt/blob/main/doc/design.md
- https://github.com/simonw/sqlite-utils
- https://github.com/github/github-mcp-server/blob/main/README.md
- https://github.com/qdrant/qdrant/blob/master/README.md
- https://github.com/meilisearch/meilisearch/blob/main/LICENSE
- https://github.com/meilisearch/meilisearch/blob/main/LICENSE-EE
- https://github.com/datahub-project/datahub
- https://github.com/ResearchObject/ro-crate
- https://www.researchobject.org/ro-crate/specification/1.3/introduction.html
- https://github.com/OpenLineage/OpenLineage
- https://github.com/ast-grep/ast-grep
- https://github.com/onyx-dot-app/onyx
- https://github.com/microsoft/graphrag
- https://github.com/frictionlessdata/frictionless-py
- https://github.com/ajv-validator/ajv
- https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github

## Verification boundary

Repository pages inspected through Opera: sourcegraph/zoekt, datahub-project/datahub, deepset-ai/haystack, qdrant/qdrant and ast-grep/ast-grep. GitHub MCP page encountered a 503 in Opera; official README read through independent web search instead. No software installed or benchmarks run, no automated catalog deployed. Upstream features are SOURCE_VERIFIED, integration fit is an architectural judgment and remains NOT_VERIFIED.
