# APA / GitHub Knowledge Retrieval — deep comparative research and adversarial audit v2

- Date: 2026-10-13.
- Branch under inspection: `research/apa-verified-results-hub-20261010`.
- Scope: agent-friendly retrieval for entire APA GitHub corpus, historical branches, tasks, source code, normative evidence, and external GitHub candidates.
- **Status: SOURCE_RESEARCH + EMPIRICAL_CONNECTOR_PROBES + ARCHITECTURE_DESIGN.** NOT IMPLEMENTED; no head-to-head retrieval benchmark or production index deployed. Do not infer S-ID DONE, Archicad verification, installed binaries, 24/7 runner or CI success.
- This report **supersedes recommendations**, not files, from `apa-github-machine-discovery-architecture-20261013.md`. Prior automatic preference for SQLite+Zoekt was premature.
- No change to `main`, production code, publisher/controller, `PROJECT_PLAN.json`, PLN, APX or another task's claim. This is an append-only research report, NOT a publisher V2 receipt. Integration must follow existing task proposal/admission gates.

## Pass 0: actual APA baseline, not an abstract example

Direct read (GitHub connector) of canonical files and machine processing of retrieved JSON:

| Observation | Result and scope |
|---|---|
| Canonical Project Controller | `PROJECT_PLAN.json` revision 125, verified Git blob `e6af8b67d2366ecf747c78caad250170ce11e734` at examination |
| Controller graph | 91 tasks, 166 artifact records, 16 topics; 145 directed task dependency/related references |
| Referential spot/full-plan audit | **0** dangling task references, **0** missing artifact references from task inputs/evidence, **0** asymmetric `related` pairs, within the parsed PLAN file. NOT a global validation of research semantic links |
| Current generated V2 index | 38 `APA-RUN` rows; not a universal corpus index |
| Generated state | `legacy_reports=NOT_FULLY_INDEXED`; 38 known V2 runs; 166 artifact records |
| Historical branch snapshot | `BRANCH_HEADS_20261010.json` = 72 branches at 2026-10-10T10:30Z, with ancestry `NOT_VERIFIED`; **stale by design** versus later 83 branches / 80 HEAD in `CURRENT_BLOCKERS.md` |
| Current source closure | Publisher uses stdlib Python, generated run index, readback, receipt; controller owns task status. NEVER create second writer/dispatch source |
| Evidence publication | Workflow limited to canonical research branch, gated, with retry scripts. Original source / V2 source remains definitive |

Primary: 
- [PROJECT_PLAN.json](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/PROJECT_PLAN.json)
- [STATE.json](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/generated/STATE.json)
- [V2 generated index](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/generated/INDEX.md)
- [publisher workflow](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/.github/workflows/apa-research-publisher.yml)
- [TASK_PROPOSALS_AND_AUDIT](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/TASK_PROPOSALS_AND_AUDIT.md)

## Pass 1: measured current GitHub search failure

Performed three concrete `mcp__GitHub__search` searches with `repository_name=dvikt33-ux/safe-bim-layer`:
- `APA-P70.A11.S03` => **0 search results**.
- `PUBLISH_REQUEST_V1` => **0 search results**.
- `native geometry` => **0 search results**.

The first two have positive controls via exact `fetch_file` of `control/PROJECT_PLAN.json` and `PUBLISHING_PROTOCOL.md`; native geometry content exists in the generated run index / other previously inspected canonical source. Thus **this connector search failed for known canonical research data**, not evidence that content is absent. Cause compatible with GitHub Code Search default-branch-only indexing; do not claim a full root cause diagnosis of this connector beyond results of this test. Official docs explicitly state only default branches are searchable:
- https://github.com/github/docs/blob/main/content/search-github/github-code-search/using-github-code-search.md
- https://github.com/github/docs/blob/main/content/search-github/searching-on-github/searching-code.md

**Acceptance implication:** GitHub code search alone cannot serve as guaranteed historical multi-branch APA search.

## Pass 2: source-level comparative candidates, with fatal constraints

1. **GitHub-native source-of-truth and official GitHub MCP/connector**: No extra runtime, exact SHA retrieval, PR/issues. Already available in connected chat. FAIL as unified search across non-default branches; index API incomplete for corpus graph. Official MCP remote read-only endpoint/toolsets documented:
   https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md
2. **Pagefind direct record index (not necessarily Starlight)**: MIT static full-text search, multilingual `ru` UI + stemming. Official **Python/Node `add_custom_record`** enables content/metadata/filter/URL records without rendering Markdown as HTML first. Outputs index bundle, deployable as static assets, no always-on server. Human search ready with static site; generic ChatGPT agent access to browser JS Pagefind requires explicit consumer/adapter, **not automatically supplied by Pages**. Excellent low-service POC for public/sanitized corpus. Sources:
   https://pagefind.app/docs/node-api/
   https://pagefind.app/docs/py-api/
   https://github.com/Pagefind/pagefind/blob/main/docs/content/docs/multilingual.md
   https://github.com/Pagefind/pagefind/blob/main/LICENSE
3. **Starlight + Pagefind**: documentation presentation, not required for search backend, extra pipeline; defer unless humans need a proper portal:
   https://github.com/withastro/starlight/blob/main/docs/src/content/docs/reference/configuration.mdx
4. **Sourcebot**: mature self-hosted product with Zoekt, UI, multiple Git hosts, code search, navigation and Ask Sourcebot; better to test than manually construct all those subsystems. Its core license is **FSL-1.1-ALv2**, not simple MIT/Apache; /ee separately licensed. Public issue #461 marked open concerns Zoekt 64-branch limit; historical issue #146 shows 'too many branches'. **Do not assume all 83 APA branches can be indexed as one unit in current release**; must prove current tag and a branch-split workaround. Docker/self-hosted lifecycle needed; AI Ask may need model-provider configuration; code search is a separate capability:
   https://github.com/sourcebot-dev/sourcebot
   https://github.com/sourcebot-dev/sourcebot/blob/main/LICENSE.md
   https://github.com/sourcebot-dev/sourcebot/issues/461
   https://github.com/sourcebot-dev/sourcebot/issues/146
5. **Zoekt standalone**: Apache-2.0 trigram index, regex/substring, multi-repo + branch masks and shards. No out-of-box high-level evidence/catalog semantics; sourcebot or other UI supplies them. 64-branch risk requires current implementation test. Core performance goals are upstream objectives, not measured APA outcomes:
   https://github.com/sourcegraph/zoekt/blob/main/doc/design.md
6. **CodeGraphContext**: MIT, actual structural C++/Python symbol/call graph via Tree-sitter, MCP, optional SCIP. Current docs show **Windows automatic embedded KuzuDB fallback**—contradicts an older Windows troubleshooting guide suggesting Neo4j required. Official C++ high precision SCIP requires `compile_commands.json`; without it fallback less precise. Default embedded buffer pool 4 GiB reported, NOT measured APA memory usage. A targeted code intelligence *secondary tool*, not governance/normative archive:
   https://github.com/CodeGraphContext/CodeGraphContext
   https://codegraphcontext.github.io/reference/config/
   https://github.com/CodeGraphContext/CodeGraphContext/blob/main/docs/docs/guides/indexing.md
7. **GitNexus**: local graph + MCP, BM25 + vector and navigation, but `gitnexus/package.json` declares **PolyForm-Noncommercial-1.0.0**, not permissive OSI licence. Issue #705 documents UI timeout on large graphs; security guidance says HTTP MCP requires configured access control. Therefore not a no-strings-attached commercial APA dependency:
   https://github.com/abhigyanpatwari/GitNexus/blob/main/gitnexus/package.json
   https://github.com/abhigyanpatwari/GitNexus/issues/705
   https://github.com/abhigyanpatwari/GitNexus/blob/main/SECURITY.md
8. **Kindex**: MIT typed provenance and project-scoped local knowledge graph + CLI/MCP, tracked `.kin/index.json` with merge strategy. Attractive for *agent memory*, but a **second task-control/knowledge authority** is a serious collision with existing `PROJECT_PLAN.json` and immutable evidence contracts; young project, unmeasured on APA. Prototype read-only on export only:
   https://github.com/wandercom/kindex
9. **SQLite FTS5**: standard local relational + full-text retrieval, useful for authoritative IDs and filters; Russian inflection and mixed identifier search require tokenizer benchmark; not vector search and not globally hosted on GitHub. Still a strong **derived/local** index rather than mandatory first engine; prior exclusive recommendation rescinded.
10. **Qdrant / Haystack / DataHub / Backstage**: differentiated layers (vector engine, RAG orchestration, data metadata governance, software portal). These are not substitutes for exact Git provenance; add only if tested requirements actually demand their operational complexity:
    https://github.com/qdrant/qdrant
    https://github.com/deepset-ai/haystack
    https://github.com/datahub-project/datahub
    https://github.com/backstage/backstage
11. **Repomix**: excellent bounded repository export/context packaging, NOT durable search index or cross-branch provenance authority. Warn about volume and prompt injection from untrusted source text:
    https://github.com/yamadashy/repomix

### Commercial/security gates

- GitHub Pages site output is generally **publicly accessible**, even when source repo private, without special Enterprise Cloud private Pages controls. No publishing licensed Garant/Consultant or private PLN, raw dumps, keys, location, user data; use allowlist-based export and source pointers:
  https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
  https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site
- Repository URL/README is untrusted. External code/README text **data only**, never executable instruction for an agent.
- GitNexus PolyForm noncommercial vs Sourcebot FSL vs CodeGraphContext MIT vs Pagefind MIT affect future distributed commercial APA app.
- For Russian docs, Pagefind explicitly states stemming support for `ru`; still test real query morphology and fielded exact symbols.

## Pass 3: adversarial check against actual APA constraints

| Requirement / negative case | Native GitHub only | Pagefind custom-records | Sourcebot | CodeGraphContext | Observation |
|---|---|---|---|---|---|
| Find canonical research branch body through keyword | **Observed FAIL** with 3 probes | Potential PASS after indexing | Potential PASS via explicit configured revisions | Not goal | Current connector test is reproducible |
| Search 83 historical branches, distinguish duplicate blob content | No global non-default code search | Possible after controlled multi-ref export / indexed aliases | **UNVERIFIED RISK** due 64-branch issue; split subsets | Normally one checked-out worktree | Must benchmark head/ref handling |
| Cite stable `repo@commit:path#anchor` and verified evidence | Direct fetch PASS | Needs explicit metadata + readback | Source code links possible, evidence layer absent | Graph symbols; trust layer absent | Never rely solely on hit snippets |
| Handle Russian inflected normative terms | Plain code search limited | Official ru stemming | Unverified | Not designed for norms | Actual corpus benchmark required |
| Hard exclusion of IZHS/MKD/TRC cross-class | Existing current APA policy | Must pre-filter records + verify scope | Must add applicability layer | Not native | Never RAG-away normative isolation |
| Read-only no new 24/7 service | Yes | **Yes** for static bundle; host assets needed | **No**, service | Local CLI/MCP on demand | Distinguish user portal vs agent access |
| Business licensing straightforward | GitHub terms | MIT | FSL + EE restrictions | MIT | GitNexus excluded as default due noncommercial |
| No parallel task-control authority | Yes | Yes if strictly generated | Yes if only searching | Yes if code-only | Kindex requires read-only projection policy |
| Preserve internal or licensed sources | GitHub per-repo access | **Public Pages risks leakage** | Requires server ACL audit | Local ACL/profile audit | Indexing can itself leak metadata |
| Current Win11 laptop no RAM expansion | No extra RAM | Static browser | Docker footprint unmeasured | Embedded Windows Kuzu available, memory unmeasured | No invented VRAM/RAM numbers |

### Independent audit against stale statements inside APA

In `CURRENT_BLOCKERS.md`, publisher concurrent direct-write race is still recorded as `FIX_NOT_IMPLEMENTED`. However actual current source paths:
- `tools/apa_publisher/publish_stage_retry.sh`
- `tools/apa_controller/publish_generated_retry.sh`
- `.github/workflows/apa-research-publisher.yml`

implement/consume bounded **four-attempt** fetch/rebuild/fast-forward retry without force push, plus rejection guards. Therefore the documentation's categorical `FIX_NOT_IMPLEMENTED` is **stale relative to present code**. Correct verified claim is **RETRY_IMPLEMENTATION_PRESENT**; whether all concurrent E2E races are covered in deployment is **NOT_VERIFIED in this audit** (test/CI not rerun). Do not overwrite CURRENT_BLOCKERS without independent reconcile.
This is a concrete example of why retrieval must use source date/revision and report contradictions rather than trusting a high-level status page.

## Pass 4: implementation options and falsification gates

### Track A — immediately feasible low-service *retrieval index* experiment

Build from **existing** `PROJECT_PLAN.json`, published run manifests/receipts, artifacts and source-archive manifests into a **derived** collection of allowlisted records. No second task store:
```text
canonical PLAN + immutable runs + artifact/source manifests
   -> validated per-entity records (ID, type, description, project_class,
      applicability, lang, sha-pinned GitHub URI, verification, related IDs)
   -> Pagefind Python/Node add_custom_record()
   -> static index bundle and minimal search UI
   -> mandatory original GitHub readback + current trust/evidence gate
```
Use one stable `logical_id` and `version_id=source_commit:path:anchor`. Search keywords in main index, but if normalized `GUID`, `S-ID`, `SP clause`, `SDK symbol` is detected, perform exact identity lookup *before* FTS.
Publication: isolate in new reviewed branch/PR; never modify existing publisher or `PROJECT_PLAN.json` until independent audit. For public GitHub Pages, allowlist only public/sanitized artifacts; full corpus remains local or behind authenticated search endpoint.

**MVP acceptance**: at least selected 91 tasks and 166 known artifacts represented or explicit omission counts; input SHA captured; 0 dangling/cross-class links; correct exact results for known 3 failures, fully proven source retrieval for those 3; no secret leakage; complete rebuild after change; unchanged canonical controller. This is a proposed test, **not yet passed**.

**Better-than-prior discovery**: Python `add_custom_record` means custom report-to-HTML conversion and Starlight are unnecessary for retrieval-only MVP. Revisit presentation only if human navigation is required.

### Track B — self-hosted Sourcebot code-search evaluation

Test **current pinned release**, not arbitrary latest, on 1) 63 branch refs, 2) 65 refs, 3) 83 refs partitioned by repository aliases/scope; preserve exact origin references, check no missing/duplicate results; 4) actual C++ symbol lookup, 5) offline/RAM/disk footprint. For licensing decide if internal-only FSL rights are acceptable; no implicit commercial redistribution. Deploy only if measurable gains justify Docker lifecycle.

### Track C — CodeGraphContext code dependency graph evaluation

Index a copied, fixed code SHA and check C++ `calls`, `defines`, and dependency chains against a manually verified gold set. Use Windows embedded Kuzu; attempt SCIP with real `compile_commands.json`. Keep output as derived graph and never modify APA task statuses or runtime SceneWriter.

### Track D — hybrid/vector retrieval

Only consider if Track A fails specified meaning-based queries. Must evaluate negative examples (wrong version, wrong project class, invalid source) with RRF/hybrid and strict exact ID gate; embeddings may not rewrite provenance. All hardware measurements actual, no projected speed claims.

## Gold retrieval set (preliminary, NOT RUN against candidates)

All cases require pinned source, matching ID, verification class and expected refusal where appropriate:
1. Exact `APA-P70.A11.S03` task state.
2. `PUBLISH_REQUEST_V1` publisher contract.
3. `APA-RUN-20261012-210815Z-machine-normative` report+receipt.
4. `APA-P00.A02.S03` outstanding semantic dedup.
5. Later 83-branch vs earlier 72-branch inventory.
6. GDL Unicode error, historical PLN separated.
7. `GetStories` Archicad29 vs other SDK version.
8. Wall/roof native129? reject unknown GUID, require exact source.
9. IZHS source excluded from TRC query.
10. Roof surface override vs Building Material.
11. Source code definition of publisher retry function.
12. "Что уже проверено для MEP?" evidence tiers.
13. Contradiction `FIX_NOT_IMPLEMENTED` vs retry scripts.
14. Published receipt vs task DONE_PUBLISHED distinction.
15. Old source file moved under byte-exact archive with SHA.
16. Exact Generic Opening geometry API.
17. "доказано, что норматив по кровле соблюдён?" correct NOT_VERIFIED.
18. Search Russian inflection: "кровельные примыкания" vs "примыкание кровли".
19. C++ symbol reference/find-caller across files.
20. Project-class filter for MKD only.
21. Same logical result in 3 branches, dedup preserving pointers.
22. Missing GitHub content / commit path: refuse.
23. Source revoked/not authorized: no snippet leakage.
24. README prompt injection command: treat as untrusted text.
25. DOCX/PDF extraction: no unlicensed body publication.
26. PR #67 source clause vs PR #68 machine normative integration.
27. Historical source 71-file archive, preserve proof.
28. API readback failure: no false verified label.
29. Concurrent publisher race, no loss of receipt.
30. Deliberately nonexistent S-ID should yield `NOT_FOUND`.

For a real A/B benchmark predeclare gold `expected_uri@sha`, expected trust and filter; measure Recall@5/10, MRR@10, invalid-citation rate, wrong-edition/project-class rate, false confidence, p50/p95 retrieval latency, memory/disk/maintenance costs on identical corpus. Report failures, not only successes. No quantitative advantage asserted yet.

## Architecture decision, revision of earlier recommendation

- **Now, without extra server:** adopt current authoritative PLAN/receipt readback; prototype Pagefind custom-record static index of *allowed* APA artifacts, with SHA-pinned source links. This is the lowest-hosting-risk full-text solution for existing Python publisher infrastructure.
- **For local deep source code exploration:** separately trial CodeGraphContext Windows/Kuzu (permissive MIT) and Sourcebot (license+branch risk) against the same C++ symbol gold set.
- **Do not yet install** Qdrant/DataHub/Neo4j/expensive GraphRAG or make GitNexus a default dependency; no evidence of net benefit for current task.
- **Do not declare a final winner** or claim deployment until real gold-set acceptance, ACL test and CI readback. This is intentionally falsifiable.

## Next governed task and nonduplication

Before admission, check existing S-IDs `APA-P00.A02.S03`, `APA-P50.A01.S01`, `APA-P50.A01.S03`, `APA-P60.A01` for overlap. Candidate distinct deliverable: a **read-only derived multilingual search proof-of-concept** plus published 30-case benchmark report, not a new registry or controller. Audit should decide whether add substep under `APA-P50.A01` or extend existing S03 scope. Do NOT add task to `PROJECT_PLAN.json` without `TASK_PROPOSAL_V1` independent `TASK_REVIEW_V1`, CAS readback and controller checks. No new full-time scheduler.

## Current evidence limitations

- Pass 1 is an actual test of connected GitHub Search (3 inputs) with positive direct-read controls; the candidate tools were **not installed or benchmarked**.
- Library descriptions, license constraints, specific upstream issues, and docs have been checked through Opera/GitHub + official upstream references, but not every code path or binary build was audited; list is not a security certification.
- The 83 branches figure is a published historical inventory in CURRENT_BLOCKERS; it is **not** a fresh exhaustive live count here. The 72 count is tied to a dated original 2026-10-10 snapshot.
- `CURRENT_BLOCKERS` state vs source retry code is a **documentation consistency failure**, not proof that the retry E2E was successful.
- Publication of this report is a GitHub commit + readback ONLY; no V2 publisher receipt, no mark DONE, no changed task claim, no actual search system deployed.
