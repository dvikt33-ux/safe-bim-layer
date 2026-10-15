# APA: real PR68/TKD dependency trace + token-visible retrieval benchmark (2026-10-13)

Status: **CODE_AND_REAL_SOURCE_CI_PASS / NOT_MERGED / NORMATIVE_NOT_VERIFIED / GPT6_BILLING_NOT_MEASURED**.
Research continuity: [read-only graph and Markdown section POC PR #69](https://github.com/dvikt33-ux/safe-bim-layer/pull/69); implementation branch `research/apa-knowledge-impact-poc-20261013`, base canonical research hub. No main/product branch edits, PLN/APX writes, norm-status promotion, new runtime engine or project-plan task status changes. This report is not a V2 publisher receipt.

## Discovery correction — existing TDK already has the essential retrieval architecture

Direct GitHub read of PR #68 pinned head `29aa06a6e9bbef0d991bea922e1ad4101ab29bdd`:
- [TDK machine retrieval_policy.yaml](https://github.com/dvikt33-ux/safe-bim-layer/blob/29aa06a6e9bbef0d991bea922e1ad4101ab29bdd/vendor/tdk-normative-roof/01_Normative_Base/_Machine/retrieval_policy.yaml) explicitly uses **`compiled_blocks_primary_retrieval_reserve`**. When the exact compiled block is available, runtime should not read full machine rules/evidence; only unresolved/stale edges trigger tightly bounded retrieval.
- [Exact IZHS route](https://github.com/dvikt33-ux/safe-bim-layer/blob/29aa06a6e9bbef0d991bea922e1ad4101ab29bdd/vendor/tdk-normative-roof/01_Normative_Base/_Machine/routes/objects/residential.izhs.yaml) selects `architecture.details`, `IZHS.ROOF.DETAILS`, with no MKD/TRC/parent class fallback.
- [Existing roof compiled block](https://github.com/dvikt33-ux/safe-bim-layer/blob/29aa06a6e9bbef0d991bea922e1ad4101ab29bdd/vendor/tdk-normative-roof/04_Code_Generation/blocks/residential.izhs/IZHS.ROOF.DETAILS.yaml) declares nine allowed SP17 rule IDs, explicit dependencies, guards and `design_only`.
- [Machine roof rule file](https://github.com/dvikt33-ux/safe-bim-layer/blob/29aa06a6e9bbef0d991bea922e1ad4101ab29bdd/vendor/tdk-normative-roof/01_Normative_Base/_Machine/rules/roofing_2026.yaml): rule `ROOF-VENT-CHANNEL-TABLE-A2-001` lists `derived_values.required_inputs=[roof_slope_length_m, roof_slope]`; its source locator says СП17 Appendix A Table A.2. It is a *declaration of required inputs*, **NOT** a new numeric calculator or verification of a current governing norm.
- [Existing normative source lock](https://github.com/dvikt33-ux/safe-bim-layer/blob/29aa06a6e9bbef0d991bea922e1ad4101ab29bdd/vendor/tdk-normative-roof/SOURCE_LOCK.json) pins upstream TDK commit `67f17d407d14aebb091daaf79f11c10178b87440` and exact SHA256 / Git blob of selected files, with `authoritativeUse=false`.

**Consequence:** prior speculation that APA should invent an independent normative vector/global graph layer was a poor default. Existing TDK already implements the highest-value token-saving routing principle. Our PR #69 complements it with **cross-document source→value dependency→APA task projection and impact**; it does not replace existing routes, guards, norms, or publisher.

## Implemented and observed

[Source-locked adapter](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-knowledge-impact-poc-20261013/tools/apa_knowledge_graph/machine_adapter.py) is Python, read-only:
1. Reads **exactly six** files from SHA-pinned PR68 head via GitHub REST: existing lock; exact IZHS route; release whitelist; roof compiled block; block catalog; roofing rule file.
2. Validates each Git blob hash, SOURCE_LOCK SHA256 for five files, exact route/project class, exact compiled block and both independent rule allowlists.
3. Produces machine-readback evidence chain `roof_slope_length_m → ROOF-VENT-CHANNEL-TABLE-A2-001 → IZHS.ROOF.DETAILS → APA-P70.A02.S02`. The final APA S-ID is a verified *artifact/PR trace*, not an engineering calculation dependency.
4. On synthetic value change `10→12` returns `RECHECK_REQUIRED_NOT_RECOMPUTED`, no norm authority or engineering acceptance. Query input is synthetic; no user PLN was read.
5. Rejects unpinned or unallowlisted refs, cross-class mixing, missing/changed source bytes, missing rule, fake promotion, missing PR68 artifact or unrelated parameter globally marked unaffected.

**Real GitHub Actions source-readback run:** [38323012649](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38323012649): 56/56 offline regression tests PASS, exact six-file REST readback PASS and correct non-numeric impact card.
**Tokenizer run:** [38323164778](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38323164778): 56/56 tests PASS, exact source readback PASS and measurable tokenizer proxy. **Additional token-safety test:** [38323265836](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38323265836): 57/57 tests PASS. Newer README-only run [38323294225](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38323294225) SUCCESS.

## Measured context size, *not model billing*

Same precise input-change question; compare text that **would** be passed directly to GPT versus compact rule/task impact card. Measured by `tiktoken==0.14.0` `o200k_base` proxy, from exact CI job logs:

| Context delivered to model | UTF-8 bytes | `o200k_base` tokens |
|---|---:|---:|
| Raw APA plan + six source files | 342,057 | 92,866 |
| Raw six selected source files only (realistic scoped but unfiltered raw) | 62,137 | 16,861 |
| Prevalidated compact impact response | **393** | **100** |

For this question, scoped-but-unfiltered raw text vs compact card: 168.61× fewer tokenizer-proxy tokens. Large naive-library baseline vs card: 928.66× fewer. **These are deliberately two baselines, NOT observed GPT-6 end-to-end savings**. Code-mode processing and source validation still occur outside the GPT context; runtime/time/API counts, tool definitions, cache hits, routing errors, retry cost, normative correctness and model reasoning are excluded. The easy exact lookup is not evidence hybrid engine ranking is solved.

## Parallel comparison/audit

- Existing TDK `compiled_blocks_primary_retrieval_reserve` is stronger than generic RAG for an already known normative operation: exact type/module/field routing and no semantic expansion into inappropriate scope.
- [DVC params](https://dvc.org/doc/command-reference/params) and [OpenLineage column lineage](https://openlineage.io/docs/spec/facets/dataset-facets/column_lineage_facet/) are useful *algorithms/metadata contract* for parameter-change tracking; do not install a second writable task controller.
- [Graphiti](https://github.com/getzep/graphiti) and [LlamaIndex PropertyGraphIndex](https://developers.llamaindex.ai/python/framework/module_guides/indexing/lpg_index_guide/) still warrant A/B for unseen natural-language question routing, but their LLM graph extraction can consume tokens, introduce unverified dependencies, and cannot supersede normative scope/quarantine. **No A/B benchmark performed here**.
- [tiktoken](https://github.com/openai/tiktoken) documents `o200k_base`; it is an external approximation, not confirmed current GPT-6 accounting.
- Adversarial cases passed in POC: when rule input unchanged, no propagation; irrelevant field is UNKNOWN globally; missing/changed lock or route blocks; cross-class fallback forbidden; task-owner and evidentiary statuses are not automatically altered.

## Fresh blockers and next work, with explicit correctness guard
- This demonstrates a **real *structural* dependency**, not yet an authoritative field-to-calculation-to-actual-PLN verified chain. Need exact normative effective edition and official text, independent source readback, actual roof material/system and measured roof inputs; current sources remain design_only/quarantined.
- PR68 head is a **pinned historical snapshot**, not a statement that PR68 remains latest or merged. Source changes should be diffed by full SHA; never silently auto-upgrade a norm edition.
- A full user natural-language retrieval benchmark must test unknown IDs, multiple conflicting documents, missing reverse edges, current-vs-old legal editions, exact profile IZHS/MKD/TRC, code symbol references, task claim races and category leakage. Report actual token usage, not only text proxy.
- PR #69 is **draft and not merged**. Integration into ongoing APA work requires independent review and task-governance through `TASK_PROPOSAL_V1 → TASK_REVIEW_V1 → PROJECT_PLAN.json` CAS. Candidate likely overlaps existing `APA-P50.A01.S01/S03`; do not auto-register.
- Next concrete vertical slice: one verified approved numeric calculation *when real source+project inputs exist*, plus exact dependent output/test and full negative false-impact benchmark. If unavailable, keep `NOT_VERIFIED` and use actual machine-source trace without fictitious values.

**Do not change any existing PLAN status as a result of publishing this research.**
