# Architectural AI checkpoint 05 — compiled project kernel, adaptive depth, existing AEC systems, multi-model AI

Date: 2026-10-07
Status: intermediate research checkpoint; not final implementation spec.
Branch: feature/working-archicad-mvp.

## Core change

The system should operate in multiple computation depths rather than choosing between one enormous analysis and one permanently lightweight mode.

The recommended architecture is:

PROJECT COMPILER -> DESIGN RUNTIME -> DEEP RECOMPILER -> RELEASE AUDITOR

The expensive work is front-loaded and converted into a compact, versioned Project Knowledge Bundle (PKB). Interactive work then evaluates deltas against that compiled kernel. If a local change exits a previously verified validity envelope, the runtime escalates automatically to a deeper level instead of continuing with stale assumptions.

This is analogous to a compiler plus an incremental runtime, not an LLM rereading the entire project and standards corpus on every edit.

## L0 — Project Compilation / Bootstrap Research

Expected duration may be tens of minutes to hours. This is acceptable and should be explicit.

Inputs:
- site, jurisdiction, date and historical/protection context;
- brief, occupancy, capacities and program;
- existing BIM/project state;
- normative sources;
- construction systems/material modules;
- major structure/MEP/fire strategies;
- detail/system/product libraries;
- architectural intent.

Outputs:
- project classification;
- normative dependency closure;
- resolved normative versions/applicability;
- Active Project Rule Pack;
- project graph skeleton and stable entity IDs;
- construction-system domains and modular lattices;
- room/program/equipment requirement sets and substitution sets;
- structure/MEP/fire concept constraints;
- critical-detail applicability matrix;
- external + internal design-intent invariants;
- repetition strategy;
- spatial indexes;
- dependency indexes and SCCs;
- cache seeds;
- audit baseline;
- Validity Envelopes for compiled conclusions.

The L0 result is the Project Knowledge Bundle, not a prose report.

## L1 — System / Phase Recompile

Run when a change invalidates one or more compiled assumptions.

Typical triggers:
- building function/classification changes;
- jurisdiction/date/context changes;
- protected historic/site regime changes;
- floor count/height crosses a threshold;
- fire strategy/core/fire-compartment change;
- primary structural system changes;
- primary facade/envelope system changes;
- major MEP strategy changes;
- construction module changes;
- critical detail family changes;
- Active Rule Pack changes.

Recompile only affected project partitions where dependency evidence permits it.

## L2 — Interactive Design Runtime

Target: sub-second to a few seconds for ordinary local changes.

Pipeline:
event delta
-> project revision
-> affected entity/property set
-> impact cone
-> relevant spatial neighbors
-> active rules whose inputs changed
-> cheap deterministic guards
-> local solver / candidate overlay
-> intent delta
-> optional architect-level LLM decision
-> validated BIM diff
-> commit/read-back.

L2 is allowed only while all relied-upon Validity Envelopes remain true.

## L3 — Deep Audit / Release Gate

Run at milestones, before major commits/releases, and after high-risk changes.

May include:
- complete graph consistency;
- full normative pack audit;
- IFC independent validation;
- full clashes/distance/IDS;
- detailed structural checks;
- detailed daylight/energy/thermal calculations;
- MEP calculations;
- cross-view consistency;
- full exterior/interior architectural-intent audit;
- quantity and documentation consistency.

## L4 — Normative Refresh

Separate event class:
normative source/version diff
-> normative dependency cone
-> changed normalized rules
-> Active Project Rule Pack delta
-> bound project parameters
-> project impact cone
-> local/system redesign if current state became invalid.

## Validity Envelope — key safeguard against light-mode drift

Every compiled conclusion must record:
- conclusion/assumption ID;
- predicate/result;
- exact inputs/dependencies;
- accepted ranges/conditions;
- source versions;
- project revision;
- invalidates list;
- escalation level;
- last verified timestamp/revision.

Example:
"current corridor rule pack is valid while occupancy classification, fire strategy, story count, building height band and source editions remain unchanged."

If an edit stays inside the envelope, use cached conclusion.
If it crosses the envelope, L2 cannot silently continue: escalate to L1/L3.

This prevents accumulated hidden mistakes.

## Audit debt / confidence ledger

Track unresolved or stale states:
- UNKNOWN solver results;
- provisional assumptions;
- stale rule bindings;
- unverified details;
- deferred deep analyses;
- repeated local workaround chains.

The runtime may remain interactive while debt is below policy thresholds and does not touch hard constraints. Crossing a risk/debt boundary triggers deeper analysis.

Do not use one universal numeric threshold; calibrate by benchmark and discipline.

## Existing systems — what not to reinvent

### dRofus
Current official documentation provides an Archicad add-on for:
- program/requirements data;
- Archicad Zone <-> dRofus Room linking;
- Archicad Object <-> dRofus Item linking;
- equipment/item lists and occurrence comparison;
- bidirectional synchronization/validation.

It can link many Archicad element types including doors, windows, walls, curtain walls, slabs, electrical equipment, lighting, columns, beams, roofs, morphs, shells, skylights, railings and stairs.

Conclusion:
Evaluate dRofus as an optional Requirements/Rooms/Equipment subsystem or at least as a reference architecture. Do not reimplement mature room-program/equipment workflows without comparison. It does not replace our normative causal graph, structural/MEP/detail impact graph, intent preservation or AI transaction engine.

### Hypar
Hypar Functions explicitly declare Model Dependencies and Model Outputs and can be composed into workflows. It is a useful precedent for dependency-based generative design and early spatial computation.

Conclusion:
Study/optionally use as a candidate-generator or reference. Do not make it the Archicad runtime core.

### TestFit
Useful as rapid feasibility/generative candidate source. It does not replace detailed project causality or Russian normative reasoning.

### BHoM
Open-source, software-agnostic AEC object model plus Push/Pull adapter framework. Core objects span architecture, engineering, environment, geometry and planning.

Conclusion:
Study object/adapter patterns and semantics before inventing every schema ourselves. No current Archicad adapter was verified in this pass, so do not adopt as a hard integration dependency yet.

### buildingSMART bSDD + IDS
bSDD supplies stable semantic class/property identifiers and relations/dependencies. IDS is suitable for machine-readable information requirements.

Conclusion:
Use for semantics/interchange where applicable; neither is a substitute for Russian legal/normative rule logic or geometric compliance.

### Solibri / BIMcollab
Independent QA/checking layers are valuable release auditors. Solibri's current Developer Platform supports custom rules and automation.

### HuskyBIM for Archicad 29
A current commercial/free connector was found that exposes hundreds of Archicad 29 tools through MCP and supports read/create/modify/delete plus attributes, classifications, layouts, issues, stories and properties.

Conclusion:
This is the most important "do not reinvent blindly" discovery in this pass. Evaluate it as:
- API-coverage benchmark/reference;
- rapid tool-surface experiment;
- possible auxiliary MCP adapter.
Do NOT replace our deterministic project engine with it: its documented workflow lets an AI client directly call Archicad tools and explicitly requires review; it does not provide our project/normative/intent causal kernel.

## Archicad repeated-floor strategies

Official Archicad 29 documentation confirms:

### Edit Elements by Stories
Provides quick copy of elements from one story to another without redrawing them.

Use when:
- initial replication is desired;
- copied floors are expected to diverge independently.

This is an authoring convenience, not a persistent semantic dependency graph.

### Hotlink Modules
Archicad specifically recommends Hotlink Modules for repetitive building structures such as hotels/offices with identical rooms. Updating the source can update all placed instances, and Model Compare can show changes.

Use when:
- a room/unit/floor really is a repeated module;
- linked propagation is desired.

Caution:
Placed Hotlink elements cannot be individually edited while they remain part of the Hotlink.

### Our own Stack Constraints
Use when floors must remain aligned for selected systems but also permit controlled exceptions.

Define per subsystem/entity:
- INDEPENDENT_COPY;
- HOTLINK_MODULE;
- STACK_CONSTRAINT;
- MULTI_STORY_NATIVE.

Do not blindly copy or link entire multi-story buildings.

## Multi-model AI fabric

No one model should be used for every task.

### Cloud lead reasoning
Use GPT-5.6 Sol High for:
- high-risk architectural synthesis;
- competing valid alternatives;
- intent conflicts;
- cross-discipline escalation;
- final explanation/decision over deterministic evidence.

### Local deep compiler candidate: Qwen3.8-Flash-Next via Strata
Current Qwen3.8-Flash architecture:
- 125B main parameters;
- 6B activated/token;
- additional 51B N-gram embedding parameters.

This explains the roughly 176/177B total figure sometimes quoted when counting the N-gram table.

Current Strata documentation:
- optimized for Qwen3.8-Flash-Next on consumer hardware;
- OpenAI/Anthropic-style localhost API;
- heterogeneous GPU/RAM/SSD placement;
- 48GB RAM: Q2_0 or IQ2_XS recommended/fits;
- 8GB NVIDIA is supported by current project materials but is below the more comfortable GPU tier, so speed must be benchmarked.

Best role on the target 48GB/8GB development machine:
- L0 Project Compilation;
- long-document synthesis/extraction;
- independent critique;
- private/offline-ish local reasoning;
- long tasks where minutes are acceptable.

Do not put it in the default interactive L2 loop before benchmarks.

### Local interactive candidates
A/B benchmark:
- Qwen3.5-35B-A3B: 35B total, ~3B activated/token; current official model card supports multimodal input and long context.
- Qwen3.5-27B: dense 27B; common GGUF quantizations are about 13.5GB Q3_K_M / 16.7GB Q4_K_M.

Serve through llama.cpp or another OpenAI-compatible local server. Choose empirically by Russian architectural reasoning quality, structured tool-call reliability and latency.

### Retrieval models
- Qwen3-Embedding-0.6B;
- Qwen3-Reranker-0.6B.

Use for candidate retrieval from project knowledge, precedents, details and normative text.

Never treat vector similarity as normative authority. Exact rule/provenance selection remains structured/deterministic.

## Unified Model Gateway

The design engine should call a common internal interface:

Request:
- task_class;
- risk;
- latency_budget;
- privacy;
- modality;
- max_context;
- required_structured_schema.

Router selects:
- NO_LLM/deterministic;
- small local retrieval/classification model;
- interactive local reasoning model;
- deep local Qwen3.8 worker;
- cloud lead reasoning.

All models consume the same structured Project Knowledge Bundle slices, not independent ad-hoc project memories.

## Dual-model critical review

For high-impact decisions:
1. deterministic engine proves hard constraints and gathers evidence;
2. primary architect model proposes/chooses;
3. optional independent local/cloud model critiques;
4. primary decision is accepted only with deterministic hard-rule PASS.

Do not use majority voting of LLMs as evidence of code compliance.

## Neural benchmark before adoption

Benchmark candidates on our actual tasks:
- Russian SP/GOST clause extraction into schema;
- cross-document reference classification;
- room-program normalization;
- equipment substitution;
- impact-cone explanation;
- Archicad tool-call JSON generation;
- architectural plan/image understanding;
- facade/interior intent comparison;
- identifying hidden cross-discipline consequences;
- recovery from intentionally seeded BIM errors.

Measure:
- exactness/groundedness;
- structured-output validity;
- tool-call correctness;
- hard-rule hallucination rate;
- Russian architectural vocabulary;
- latency;
- RAM/VRAM;
- prompt ingestion speed;
- tokens/sec;
- recovery after invalid candidate.

Select by Pareto quality/latency/resource fit, not parameter count.

## Recommended first software evaluation order

1. Keep/build the performance-first native Archicad event kernel from checkpoint 04.
2. Install/evaluate HuskyBIM in an isolated test Archicad setup as a capability reference, not as project authority.
3. Evaluate dRofus workflow/cost/trial before implementing room/equipment requirement management from scratch.
4. Install Strata and benchmark Qwen3.8 Q2_0/IQ2_XS on the target machine.
5. Install llama.cpp and A/B test Qwen3.5-35B-A3B vs Qwen3.5-27B quantizations.
6. Add Qwen3-Embedding-0.6B + Reranker for local retrieval.
7. Decide which external products become dependencies only after integration and performance tests.

## New MVP artifact: CompiledProjectKernel

The first real "brain package" should serialize something like:

- project_profile;
- normative_closure_hash;
- active_rule_pack;
- rule_trigger_index;
- entity_schema/version;
- dependency_skeleton;
- spatial_index_snapshot metadata;
- construction_systems;
- module_lattices;
- room_program;
- equipment_substitution_sets;
- critical_detail_matrix;
- exterior_intent;
- interior_intent;
- repetition_strategy;
- validity_envelopes;
- audit_baseline;
- source_version_manifest.

Interactive runtime never needs to reread all standards while this package remains valid.

## Gate before adding graph "muscles"

Do not expand the full graph families until:
- Project Compiler produces a reproducible PKB;
- Validity Envelopes exist and automatically escalate when crossed;
- interactive runtime works only from deltas;
- revision/stale protection passes;
- local/cloud model routing is benchmarked;
- repeated-floor strategy is explicit;
- external products have been evaluated against our requirements rather than duplicated by assumption.


## Additional audit finding — HuskyBIM is closer to our Archicad execution problem than expected

Current HuskyBIM documentation (October 2026) states that its Archicad 29 connector exposes about 733 tools and covers element read/create/modify/delete, attributes, classifications, layouts/drawings, BCF issues, stories and properties.

This means our research program should include a formal capability-diff:

`OUR BRIDGE CAPABILITY MATRIX vs HUSKYBIM CAPABILITY MATRIX`.

Questions to test:
- geometry fidelity for Walls/Doors/Windows/Slabs/Roofs/Stairs/Curtain Walls;
- batch semantics;
- read-back evidence;
- transaction/undo grouping;
- observer/change-event support;
- access to element memos, material bindings, host links and result geometry;
- ability to expose tools to a model/router other than its default Claude workflow;
- latency and payload sizes;
- reliability on a large real PLN.

Until those tests exist, HuskyBIM is neither rejected nor made authoritative.

## Additional audit finding — use a model gateway rather than hard-wiring model vendors

LiteLLM is a current open-source OpenAI-compatible model gateway/router with a unified interface, retries, fallbacks, load balancing and caching.

Potential role:
`Design Engine -> internal Model Gateway -> local/cloud model endpoints`.

This allows the architecture to keep stable logical model roles such as:
- `architect-deep`;
- `architect-fast`;
- `norm-extractor`;
- `critic`;
- `embedding`;
- `reranker`;

while the actual backing model can be replaced after benchmarks.

Important:
- deterministic task routing policy remains ours;
- do not use semantic response caching for agentic/normative decisions without strict safeguards;
- exact project/rule cache keys should include project revision, rule-pack hash and relevant dependency fingerprints.

LiteLLM is an optional infrastructure candidate, not a required MVP dependency. A small custom gateway may remain simpler until more than two or three model endpoints are actually in use.
