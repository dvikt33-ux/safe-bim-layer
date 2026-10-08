# Architectural AI checkpoint 28 — agent skills, evidence arbitration, incremental computations

Date: 2026-10-08
Status: RESEARCH / CODE-INSPECTED, NOT AC29-VERIFIED
Current implementation target: Archicad 29 ONLY.
Branch: feature/working-archicad-mvp
Precedents: checkpoints 20-27, AC29 HOT/WARM/COLD and LIGHT/MEDIUM/HEAVY.

## Executive finding

Three additional areas that appeared custom have existing substantial reusable building blocks:

1. **Architectural/construction agent skill libraries** (DDC Skills and ArchSight AIOS).
2. **Typed capability registry, evidence-bound tool arbitration and locally compiled knowledge packs** (ArchSight AIOS).
3. **Incremental compute/dependency engines** (incr, Salsa, Differential Dataflow).
4. **Durable workflow engines for COLD jobs** (Hatchet; other options Temporal/Kestra).

These do NOT prove a ready autonomous architect. They may replace generic SKILL scaffolding, capability execution contracts and dependency evaluation runtime. Our unique work is still the architectural causal semantics, source applicability, project intent and AC29 link/transaction.

## Finding A: DDC Skills for AI Agents in Construction

Repo: https://github.com/datadrivenconstruction/DDC_Skills_for_AI_Agents_in_Construction
Public README currently claims 238 skills, though repo topic/description/search snippets use 221. This count discrepancy must not be treated as a technical capability.
Repo has 1,026 files in main Git tree (observed). Categories span:
- BIM-Analysis including clash, validation, IFC QTO;
- IFC/DWG/RVT conversions and ETL;
- information quality and IDS;
- cost, CWICR multilingual work items, 4D/5D;
- documentation and automated workflows;
- project/business operations.

### Source-code quality audit — crucial caveat

The `bim-clash-detection/SKILL.md` includes an illustrative nested element-pair loop with AABB intersection tests. It is NOT precise BIM solid-geometry clash verification. If used as the final clash engine, it could give geometric false positives and O(N*M) pair-scan costs.

The `ids-checker/SKILL.md` defines a homegrown Python IDSRequirement/checker over element dictionaries. This is NOT evidence that the example implements full buildingSMART IDS 1.0 XML semantics or passes the buildingSMART IDS conformance/validation tests.

Therefore:
- Use DDC skills as workflows, inspiration, extraction/QTO/ETL examples and possible automation templates.
- Prefer IFC-native IfcTester, native Archicad collision and proven Solibri/Tangl for actual BIM validation.
- Do not install every skill or treat "238" as 238 independently tested tools.
- Specific scripts require license, external binary and performance audit.

Classification: METHODS_AND_SKILLS_REFERENCE; selective code reuse only after tests.

## Finding B: ArchSight AIOS

Repo: https://github.com/ArchSightLabs/archsight-aios
License: Apache-2.0 (repository LICENSE read).
Main repo tree: 509 entries observed.

### Existing artifacts directly overlapping with our planned work
- `runtime/capability-registry.json`: typed inputs/outputs, allowedSkills/ownerAgents, status, evidenceContract, blockingRules, humanEscalation.
- `runtime/capability-adapters.json`: local stdio MCP mapping and tool names.
- `governance/arbitration-protocol.md`: Claim/Evidence/Tool Result/Decision, evidence precedence, fact vs inference, fail/hold/review, no false claim of tool execution.
- `runtime/agent-routing.md` / `runtime/skill-routing.md`: role ↔ skill ↔ task ↔ workflow split.
- `docs/v1.5.0-knowledge-pack-runtime.md`: compile source records, standard register, clause map, entity/relation map, queries/evaluation into local Knowledge Pack.
- `knowledge.norm_lookup` local reference MCP:
  * status: found/not_found/conflict/inapplicable/error;
  * citations;
  * applicability: applicable/not_applicable/need_context;
  * sourceVersion.
- `repo.architecture_health_scan` implemented connector from a project analyzer, with reproducibility and fingerprinted evidence.

### Important caveat

ArchSight AIOS is not an Archicad live geometry executor, a Russian normative authority, or a production architectural-code checker. Its built-in structural examples are scoped demonstration checks, not full structural compliance. It must not replace qualified technical verification.

### Best application to our project

Reuse specific concepts/schemas (respect Apache license):
- `CapabilityRegistry` should not be an invented free-form AI tool list.
- Every capability must report authoritative inputs, output schema, evidence, applicability, version, permission and failure mode.
- TOOL RESULT can block changes even when LLM says they are fine.
- Runtime skills should be task-specific: Architectural Program, CSE System Selection, Wall Move, Opening Placement, Impact/Repair, Documentation Compilation, Russian Norm Lookup.
- Our Russian normative compiler stays an independently versioned authority; ArchSight-style Knowledge Pack is a supporting local retrieval format only if it passes provenance/applicability tests.
- Support dual outcome PASS / FAIL / UNKNOWN / NOT_VERIFIED rather than allowing missing evidence to imply PASS.

Classification: REUSE_CONTRACT_AND_GOVERNANCE_PATTERN, TEST_LOCAL_REFERENCE_RUNTIME.

## Finding C: incr for the HOT/WARM dependency recalculation

Repo: https://github.com/Anyesh/incr
License: Apache-2.0. Rust crates `incr-compute`, `incr-concurrent`; Python binding in PyPI.

README/source API:
- input nodes and derived queries;
- dynamic dependency recording;
- marking dependents dirty on input update;
- lazy demand-driven recompute;
- early cutoff when recalculation yields unchanged result;
- incremental collections/operators such as filter, join, pairwise, aggregate;
- batch stabilization/observers;
- local and concurrent variants.

README reports microsecond/nanosecond benchmark figures vs Salsa. These are author benchmarks and NOT an AC29 latency benchmark. Small repo footprint/limited adoption: risk maturity.

### Strong fit

BIM value propagation:
- moved wall -> two zone boundaries -> measured clear area;
- area -> set of rule results;
- rule status -> project validity status;
- roof geometry -> detail interfaces;
- host window -> derived jamb/lintel/sill records.

Early cutoff should suppress redundant dependent work when input changes do not affect derived/normalized values.

### Hard limits

incr is NOT:
- architectural semantic graph ontology;
- constrained geometric optimizer;
- normative rule-language processor;
- AC29 event observer;
- Archicad write transaction engine.

Use only as a compute substrate beneath typed SBIM graph edges.

### Comparison candidates

1. `incr`: direct Python/Rust bridge, emerging maturity.
2. `salsa-rs/salsa`: established incremental query system with Rust API.
3. `TimelyDataflow/differential-dataflow`: mature low-level incremental collection processing, greater engineering complexity.
4. Plain Python NetworkX+dirty cache: simplest baseline. Benchmark always included.

DO NOT select engine solely from upstream microbenchmarks.

## Finding D: durable COLD workflows

Repo: https://github.com/hatchet-dev/hatchet (MIT).
Provides:
- background jobs;
- durable state and retries;
- event triggers/webhooks;
- Python SDK;
- rate/concurrency controls;
- worker pool;
- task monitoring/replay.

Potential role: scheduled HEAVY compliance, IFC snapshot conversions, CFD/FEA/LCA, document publication or provider failures.

But for SOLO AC29 MVP this may be unjustifiably operationally heavy (Postgres, worker service).
Choice should be made against:
- single local process;
- in-process queue;
- SQLite jobs;
- standard Windows Task Scheduler;
- existing Speckle Automate for model publications.

Decision: DEFER DURABLE SERVER UNTIL REAL FAILURE CASE / ASYNC LOAD PROVES NEED.

## New rule: evidence and execution maturity

Previous matrices sometimes used PASS for a vendor's public claim, which can be confused with independent verification.

Mandatory labels from now on:
- DISCOVERED: name/URL found.
- DOCUMENTED: vendor/repo claims capability.
- SOURCE_INSPECTED: implementation inspected.
- SANDBOX_TESTED: runs against synthetic/isolated project.
- AC29_TESTED: runs on current real Archicad 29 fixture.
- WORKFLOW_ACCEPTED: measured quality and performance meet project acceptance contract.
- BLOCKED/INCOMPATIBLE.

Separate properties:
- evidence_level;
- architectural_quality;
- AC29_read_write_scope;
- legal_applicability;
- license;
- cost;
- performance;
- reversibility.

No `REUSE_AS_IS` without AC29_TESTED where live authoring is required.

## Test INC-01 — local graph benchmark

Input: previously measured real AC29 dataset contains 5,296 BIM entities, 4 stories, 9,261 bodies; prior full dump ~105 MB / ~12.85s. These are existing project baselines, not benchmark results for incr.

Simulate:
A. Move one wall: update affected adjacent zones + area + geometric conflicts + spanning constraints + façade dependencies; other unrelated nodes must not recompute.
B. Move one equipment object: containment, clearances and fit; no artificial change to room area.
C. Resize one window: daylight, pier/module, façade group, relevant construction detail; do not invalidate all building areas.
D. Change one applicable Russian rule: invalidate all and only facts bound to exact rule revision; unrelated norms must remain valid.
E. Change a repeated/multistorey bearing wall: multiple stories, aligned dependent openings/slabs; intentionally broad cone.

Measure:
- number of invalidated nodes;
- number actually recalculated;
- missed dependencies (zero tolerance);
- stale or incorrect values (zero tolerance);
- P50/P95 local graph latency;
- peak resident memory;
- affected sheets/rules;
- cleanup after node deletion;
- early cutoff correctness;
- replay/rollback to initial state.

Compare incr, Salsa (if wrapper affordable), baseline graph cache and optionally Differential Dataflow.

Gate: choose only after correctness and P95 measurements; speedups must be measured against our actual model.

## Test CAP-01 — evidence-bound tool routing

One operation `MOVE_WALL_MODULE_SAFE`:
1. Skill interprets requirement with room size and chosen CSE/masonry grammar.
2. Tool reads exact GUID/geometry and source model revision.
3. Module optimizer produces valid candidates.
4. Capability result includes units, rule revision, evidence, provider, pass/fail/unknown.
5. Change planner previews affected elements.
6. User confirms transaction.
7. Writer modifies AC29; readback verifies.
8. If readback differs, mark fail/hold and recover.
9. Coverage Signatures propagate only after successful readback.

ArchSight model can supply the contract/permissions, not the wall solver.

## Test SKILL-01 — explicit skill effectiveness

Take 10 failures already known:
- internal wall through window;
- room area below requirement;
- unstacked wet areas;
- incompatible door swing;
- equipment clearance insufficient;
- fragmented unnecessary wall segments;
- façade rhythm damage after window resize;
- wall module drift;
- slab overspan;
- dependent detail not updated.

Compare:
- unstructured GPT prompt;
- a formal architect Skill + project facts;
- Skill + deterministic tools + readback.

Scoring:
- genuine pass under applicable requirements;
- no invented dimensions;
- count manual corrections;
- human minutes to verified usable result.

No skill is considered "trained architect" merely because instructions mention a check.

## Next steps

1. Do not code a HOT graph from scratch.
2. Build a small isolated INC-01 benchmark, then choose incremental substrate.
3. Borrow capability/evidence governance from ArchSight AIOS where licensing permits, rather than implementing free-form multi-agent arbitration.
4. Curate a tiny skill set (<10) tied to real tools; do not import the full DDC collection.
5. Continue AC29-first; no re-platforming or second BIM source of truth.
6. Keep bulk code work frozen pending reuse benchmark.

## Strategic conclusion

The most important change from this pass is NOT another impressive product count.

It is that both **AI engineering skills** and **incremental graph execution** have credible open implementations, while the code audit also exposed misleading capability names (AABB "clash" and simplified "IDS" checker).

This protects the project from the two opposite failure modes:
- writing everything from scratch;
- blindly adopting packages whose titles imply professional BIM capability they do not have.
