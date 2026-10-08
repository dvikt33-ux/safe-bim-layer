# Architectural AI checkpoint 30 — Architect Skill OS: instructions, evidence arbitration, memory and automatic model/tool routing

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Context carried forward

This checkpoint starts **after**:
- AC29-first architecture;
- HOT/WARM/COLD runtime;
- LIGHT/MEDIUM/HEAVY execution;
- CSE / VCE / ADG;
- normative graph and evidence chain;
- floor-plan/section/detail/documentation compilers;
- whole-system reuse audit;
- FLOORA / small-specialist training strategy.

The question in this pass:

**What instructions should the AI actually receive so that it behaves more like an architect, does not forget dependencies, uses the right tools automatically, and does not drown in one giant prompt?**

The strongest finding is that the answer is **not a mega system prompt**.

Several current open projects independently converge on:
- modular task skills;
- capability registries;
- explicit tool permissions;
- evidence contracts;
- shared project state;
- specialized reviewer agents;
- deterministic validation;
- human escalation;
- learning from validated trajectories.

---

# 1. ArchSight AIOS is highly relevant as an instruction/runtime governance reference

Repository:
`ArchSightLabs/archsight-aios`

Observed:
- Apache-2.0;
- package version observed: 1.7.0;
- explicit BIM/IFC/RAG/GraphRAG profiles;
- multi-host skill packaging for Codex, Claude Code, Gemini, OpenCode, WorkBuddy and others;
- local Knowledge Pack runtime;
- Capability Registry;
- evidence arbitration protocol.

This is not an architectural design engine.

Its importance is different:

**it already formalizes how domain AI instructions, tool permissions, evidence and multi-agent arbitration should be structured.**

## Evidence hierarchy

Its arbitration protocol defines a strong hierarchy:

- L0 — human hard constraints/authority;
- L1 — deterministic tool results;
- L2 — current project facts/configuration;
- L3 — structured knowledge / normative sources;
- L4 — specialist agent judgement;
- L5 — raw LLM reasoning.

This is extremely compatible with SBIM.

### SBIM adaptation

```
L0  architect/user locked intent + project brief + explicit approval
L1  deterministic geometry/solver/checker/readback result
L2  current AC29 project state / GUID / model revision / actual settings
L3  active norm + applicability + CSE/VCE/provider evidence
L4  architectural/specialist agent recommendation
L5  unconstrained language-model opinion
```

**Lower evidence must not silently override higher evidence.**

This directly addresses a recurring failure mode:
the LLM "thinks" a wall can move even though the actual model/solver/norm says it cannot.

---

# 2. Capability Registry is a better interface than "the agent has 700 tools"

ArchSight AIOS models capabilities with:
- ID;
- owner agents;
- allowed skills;
- authority level;
- input schema;
- output schema;
- evidence contract;
- blocking rules;
- human-escalation conditions.

This is the missing abstraction above our provider registry.

## Proposed SBIM Capability Contract

Example:

```yaml
id: ac29.wall.move
semantic_class: model_mutation
authority: L1
allowed_skills:
  - architect-repair
  - layout-adjustment
providers:
  - Archicad-MCP
  - Tapir
  - native_gap
input:
  wall_guid:
  displacement:
  anchor_policy:
  module_policy:
preconditions:
  - current_revision_matches
  - wall_exists
  - no_locked_design_intent
  - impact_cone_computed
evidence_required:
  - dry_run_plan
  - affected_guids
  - readback_fingerprint
blocking:
  - structural_envelope_invalid
  - hard_norm_violation
  - ADG_invariant_break
human_escalation:
  - massing_change
  - structural_system_change
```

This means the LLM does not choose among hundreds of raw commands.

It asks for:
`ac29.wall.move`.

The provider router resolves the concrete implementation.

---

# 3. DDC Skills proves that construction-domain instructions can be packaged as reusable skills

Repository:
`datadrivenconstruction/DDC_Skills_for_AI_Agents_in_Construction`

Observed:
- MIT;
- current README advertises 238 skills;
- BIM analysis;
- BIM validation;
- IFC/QTO;
- cost;
- 4D/5D;
- generative design;
- agent orchestration;
- digital twin;
- construction workflows.

The useful lesson is not that all 238 should be installed.

It is the packaging pattern:

```
skill/
  SKILL.md
  instructions
  examples
  tool requirements
  guardrails
  output
```

The current `generative-ai-design` skill explicitly treats generative AI as:
- option generation;
- deterministic quantification;
- cost/carbon scoring;
- human selection/refinement.

The current `ai-agent-orchestration` skill explicitly requires:
- shared data spine;
- human checkpoints;
- deterministic validation;
- idempotent agent actions.

These principles should be adopted.

---

# 4. HarnessBIM's memory model is almost exactly what a long-running architecture agent needs

HarnessBIM separates memory into:

## Working memory
Current:
- brief;
- open issues;
- immediate plan;
- recent changes.

## Episodic memory
Historical trajectories:
- task;
- proposed operation;
- tool execution;
- verifier outcome.

## Semantic memory
Durable project facts:
- selected structural system;
- façade concept;
- grid;
- material palette;
- design decisions;
- current rules.

## Procedural memory
Validated reusable skills:
- operations that already worked;
- parameterized;
- versioned;
- tested.

This is much better than "load the whole old chat".

### SBIM mapping

```
WORKING
  active change request
  dirty cone
  local context

SEMANTIC
  DDR
  ADG
  CSE
  VCE
  rule applicability
  project constants

EPISODIC
  candidate A/B/C
  accepted/rejected changes
  previous failures
  readbacks

PROCEDURAL
  verified ACP/Favorite recipes
  provider actions
  validated repair patterns
  documentation recipes
```

Raw chat history should never be the authoritative state.

---

# 5. HarnessBIM's skill promotion pattern is directly useful

The current design proposes:

```
agent-generated operation
        ↓
passes verifiers
        ↓
generalize
parameterize
name
document
test
        ↓
skill registry
```

Future work then retrieves the proven operation rather than regenerating it.

This is especially valuable for AC29 because the same actions recur:

- create exterior composite wall;
- place module-safe opening;
- generate wet-core stack;
- create associative drawing;
- publish AR subset;
- adapt approved detail;
- move partition with area recomputation.

### SBIM rule

A successful one-off action is **not** automatically a skill.

Promotion requires:
- deterministic readback;
- regression fixture;
- validity envelope;
- provider/version identity;
- side-effect declaration;
- rollback path.

---

# 6. Agentic BIM Team gives a useful discipline-agent pattern — and also shows what NOT to do

Repository:
`louistrue/agentic-bim-team`
License: MIT.

The architecture is:
- architect agent writes/modifies IFC;
- structural/MEP/façade/fire agents are read-only reviewers;
- reviewers emit BCF;
- architect repairs;
- iterate.

This separation is good.

## Good pattern

**One design owner; many reviewers.**

Specialist reviewer agents:
- do not independently rewrite architecture;
- produce issues/evidence;
- attach affected GlobalIds;
- provide a proposed fix;
- send the issue back to the design owner.

This prevents concurrent agents from fighting over the same geometry.

## Weakness visible in the current prompts

The current architect prompt contains many hard-coded example dimensions and simplified assumptions.

Examples of risk:
- rectangular building as default;
- fixed sample wall thicknesses;
- fixed staircase assumptions;
- literal U-values/fire ratings;
- coarse room/core requirements.

This proves that **a detailed role prompt is still not architectural intelligence**.

Rules and dimensions must come from:
- project state;
- active regulation;
- CSE/VCE;
- specialist tools;
- project ADG;

not from permanent prose in the prompt.

---

# 7. Proposed architecture: no mega-prompt

The Architect AI runtime should assemble a small prompt for each action from six layers.

## Layer A — Constitution

Very short, stable rules:

1. AC29 current project is source of live BIM truth.
2. Never invent dimensions, norms, materials or solver results.
3. Hard constraints outrank preference.
4. Preserve ADG invariants.
5. Before custom code, run reuse/capability search.
6. Mutations require impact analysis + readback.
7. Use cheapest authoritative semantic source first.
8. If evidence is insufficient, mark `NEED_VERIFY`.
9. One change may invalidate many dependent facts.
10. Documentation is derived from verified model state.

This layer should stay small.

## Layer B — Project State

Dynamically retrieved:
- brief;
- site;
- program;
- current revision;
- active DDRs;
- ADG;
- CSE/VCE;
- current floor/core/grid;
- relevant rule set.

Only relevant fragments enter context.

## Layer C — Task Skill

Examples:
- `architect-change-wall`;
- `architect-place-opening`;
- `architect-layout-space`;
- `architect-select-system`;
- `architect-repair-conflict`;
- `architect-section-need`;
- `architect-detail-need`;
- `architect-publish-package`.

Each skill gives the procedure for exactly one class of decision.

## Layer D — Capabilities

Only the semantic capabilities required by the skill.

Not all Tapir/Husky/Archicad-MCP commands.

## Layer E — Evidence

Actual:
- relevant AC29 facts;
- rule citations;
- solver outputs;
- precedent retrieval;
- prior accepted decisions.

## Layer F — Output Schema

Strict structured response:
- proposed action;
- affected entities;
- expected impact cone;
- required checks;
- provider call;
- acceptance/readback criteria;
- status.

---

# 8. Proposed Skill Contract

Every SBIM skill should contain:

```yaml
skill_id:
version:
purpose:
applicability:
non_goals:

required_context:
  project_facets:
  norm_domains:
  design_intent_facets:

allowed_capabilities:
forbidden_capabilities:

preconditions:
hard_invariants:
strong_preferences:
weak_preferences:

procedure:
  - step

repair_order:
stop_conditions:
human_escalation:

output_schema:

postconditions:
  - deterministic_readback
  - coverage_signature_update
  - decision_record_if_needed

promotion_requirements:
  - regression_test
  - validity_envelope
  - provider_version
```

This should be machine-readable where possible.

---

# 9. Skills should be hierarchical, not flat

A flat list of 200–700 tools is poor context.

Recommended hierarchy:

```
ARCHITECT
│
├── ANALYZE
│   ├ program
│   ├ topology
│   ├ impact
│   └ precedent
│
├── DESIGN
│   ├ massing
│   ├ core
│   ├ layout
│   ├ structure-envelope
│   ├ construction-system
│   └ facade
│
├── MODIFY
│   ├ wall
│   ├ opening
│   ├ stair
│   ├ equipment
│   └ dependent-element
│
├── VERIFY
│   ├ normative
│   ├ spatial
│   ├ structural
│   ├ MEP
│   ├ fire
│   └ design-intent
│
└── DOCUMENT
    ├ view-need
    ├ dimension
    ├ detail
    ├ schedule
    └ publish
```

The router first chooses a **skill family**, then a skill, then 3–5 semantic capabilities.

This matches the existing SBIM tool-context strategy.

---

# 10. Agent roles should be reviewers/owners, not theatre

Do not create twenty personas merely because multi-agent sounds sophisticated.

Recommended minimal ownership:

## Architect Orchestrator
Owns:
- project synthesis;
- architectural decisions;
- change selection;
- ADG preservation;
- final repair choice.

## Normative Specialist
Owns:
- active-source applicability;
- conflicts;
- rule evidence.

## Structural Reviewer
Owns:
- structural envelope/evidence;
- no direct architectural mutation.

## MEP Reviewer
Owns:
- routes/shafts/service constraints;
- no direct architectural mutation.

## Fire/Egress Reviewer
Owns:
- fire/egress checks;
- no direct architectural mutation.

## Documentation Compiler
Owns:
- derived drawing/document state;
- no independent redesign.

The reviewers return:
`Claim + Evidence + Affected entities + Severity + Suggested repair class`.

The Architect Orchestrator decides among feasible repairs.

---

# 11. Evidence-driven conflict arbitration

Example conflict:

- Architect wants to move wall 300 mm.
- Structural reviewer says span becomes invalid.
- ADG says façade unchanged.
- Room program improves.
- Normative specialist says both positions legal.

Decision order:

1. L1 structural tool result blocks invalid span.
2. Generate alternative repair candidates.
3. Filter by hard rules.
4. Preserve ADG invariants.
5. Rank remaining candidates by disruption + preference.
6. Escalate only if no candidate satisfies hard constraints.

Never:
"architect agent has higher rank than structural agent".

Authority belongs to evidence, not persona.

---

# 12. Model routing should be automatic

Checkpoint 29 established:
small local specialist models can outperform huge general models on narrow structured tasks.

HarnessBIM independently uses capability-aware routing.

Recommended routing:

## Frontier/cloud reasoning model
Use for:
- ambiguous brief;
- major design tradeoff;
- novel failure;
- cross-domain synthesis;
- research;
- explaining options to user.

## Small local specialist
Use for:
- task classification;
- retrieval query rewriting;
- candidate layout generation;
- repeated repair-class proposal;
- information-obligation classification;
- detail retrieval ranking;
- simple semantic extraction.

## Deterministic tool
Use for:
- geometry;
- numeric optimization;
- code checks;
- structure;
- energy;
- MEP;
- quantities;
- publication.

The user should not manually select the model in normal work.

---

# 13. Context must be compiled, not dumped

Never send:
- 100 MB Model Dump;
- all norms;
- all skills;
- all project history;
- all tools;

to every model invocation.

The runtime should compile a **Context Capsule**.

Example:

```yaml
task: MOVE_PARTITION
target:
  guid:
  floor:
nearby:
  rooms:
  openings:
  structure:
  equipment:
constraints:
  hard:
  ADG:
  module:
current_metrics:
  areas:
  span:
impact_summary:
relevant_rules:
capabilities:
```

This is the neural equivalent of the Fast Project Compiler.

---

# 14. Tool failure must be first-class

No skill may interpret missing evidence as pass.

Required statuses:

- PASS
- FAIL
- NEED_VERIFY
- NOT_APPLICABLE
- TOOL_ERROR
- BLOCKED_INPUT
- STALE

If a structural solver crashes:
status is not PASS.

If a norm cannot be resolved:
status is not "probably okay".

If readback differs from plan:
mutation is failed.

---

# 15. Instructions need regression tests

This is an important result from both ArchSight and HarnessBIM.

A prompt/skill is software.

Every critical architectural skill should have:
- fixture;
- expected capability calls;
- forbidden calls;
- expected hard-gate behavior;
- expected output schema;
- failure examples.

Example:

`architect-place-opening` tests:

1. normal masonry wall -> legal candidate;
2. candidate collides with partition -> reject;
3. façade ADG axis broken -> reject/alternative;
4. minimum pier violated -> reject;
5. daylight shortfall -> search other size/family;
6. no normative source -> NEED_VERIFY;
7. write succeeds but readback wrong -> FAIL.

Do not trust a skill because the prose "looks good".

---

# 16. Proposed initial SBIM skill pack

Do not start with 238 skills.

Start with ~12 high-leverage skills:

1. `architect-project-bootstrap`
2. `architect-impact-analysis`
3. `architect-layout-space`
4. `architect-change-wall`
5. `architect-place-opening`
6. `architect-select-construction-system`
7. `architect-core-option`
8. `architect-repair-conflict`
9. `architect-preserve-design-grammar`
10. `architect-detail-need`
11. `architect-view-need`
12. `architect-document-publish`

Then add skills only when:
- repeated task exists;
- current generic skill causes measurable errors;
- promotion test exists.

---

# 17. What can be reused immediately

## From ArchSight AIOS
Reuse/adapt:
- evidence hierarchy;
- Capability Registry schema concept;
- blocking rules;
- human-escalation model;
- Knowledge Pack validation/eval concept;
- task-scoped skill packaging;
- multi-host instruction packaging.

Do not import Chinese/regional engineering conclusions as project facts.

## From DDC Skills
Reuse/adapt:
- skill file structure;
- validation pipelines;
- generative-design loop;
- deterministic QA principle;
- idempotent action principle;
- cost/QTO/4D/5D skill patterns.

Do not install all skills into active context.

## From HarnessBIM
Reuse/adapt:
- memory taxonomy;
- skill promotion;
- capability-aware model routing;
- trajectory recording;
- verifier-as-training-signal;
- sandbox/permission model.

## From Agentic BIM Team
Reuse/adapt:
- one design owner + read-only specialist reviewers;
- BCF issue feedback loop;
- explicit affected GUIDs;
- issue descriptions with repair suggestions.

Do not copy hard-coded Swiss dimensional assumptions into permanent prompts.

---

# 18. New roadmap removals

Custom work is BLOCKED pending reuse audit for:

- generic agent-skill file format;
- generic evidence-arbitration philosophy;
- generic capability registry concept;
- generic multi-agent reviewer pattern;
- generic four-tier memory architecture;
- generic model router;
- generic prompt regression infrastructure.

What remains custom:

- SBIM architectural skill taxonomy;
- AC29 capability mapping;
- Russian evidence/applicability;
- ADG/CSE/VCE integration;
- architectural impact cone;
- disruption hierarchy;
- project-specific skill tests;
- Context Capsule compiler.

---

# 19. Practical experiment SKILL-OS-01

Implement **only one** skill:
`architect-change-wall`.

Test on a real AC29 file.

The runtime must automatically:

1. identify target wall;
2. retrieve adjacent rooms/openings/structure;
3. compile relevant hard rules;
4. retrieve ADG constraints;
5. compute impact cone;
6. generate only module-valid candidates;
7. call appropriate checker(s);
8. rank feasible candidates;
9. dry-run selected mutation;
10. execute;
11. read back;
12. invalidate affected coverage signatures;
13. explain what changed.

Compare with:
- one giant prompt with all project instructions.

Metrics:
- context tokens;
- latency;
- failed tool calls;
- unintended edits;
- hard-rule violations;
- human correction minutes.

Expected result:
skill-routed context should be both faster and safer.

---

# 20. Practical experiment EVIDENCE-01

Create one deliberate conflict:

- room needs more area;
- moving wall improves room;
- structural span becomes unacceptable;
- another low-impact equipment substitution exists.

Verify system behavior:

```
LLM preference: move wall
L1 structural tool: FAIL
        ↓
wall candidate rejected
        ↓
repair hierarchy continues
        ↓
equipment substitution selected
```

Success:
language-model preference cannot override deterministic failure.

---

# 21. Practical experiment MEMORY-01

Perform a design decision:

`north façade opening rhythm = 1500/1500/1800 family`.

Store it as:
- DDR;
- ADG invariant/preference;
- semantic memory.

Later request:
"increase daylight in room 212".

Verify:
- system retrieves façade grammar;
- does not independently widen one window to an arbitrary width;
- proposes grammar-compatible alternatives;
- if conflict remains, asks/records explicit supersession.

---

# Strategic conclusion

The next level of "teaching AI architecture" is not more prose in a system prompt.

It is a small operating system of:

```
stable constitution
+ project semantic memory
+ task-specific skills
+ capability contracts
+ evidence hierarchy
+ deterministic gates
+ specialist reviewers
+ compact context capsules
+ regression-tested procedures
+ validated learning trajectories
```

This is how the system can behave consistently across many long projects without carrying the entire architecture of the project inside one LLM context window.
