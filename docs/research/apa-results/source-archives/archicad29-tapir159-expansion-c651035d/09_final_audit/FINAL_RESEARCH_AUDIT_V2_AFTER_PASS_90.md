# FINAL RESEARCH AUDIT V2 — after project-acceleration pass 90

Objective:

> Make Archicad projects as fast as practical, minimize routine work, minimize failure probability, maximize useful functionality, and use AI only when it accelerates the workflow without stealing RAM/VRAM or control from Archicad/Twinmotion.

Baseline:

- Archicad 29;
- Tapir Additional JSON Commands 1.5.9 installed by the user;
- upstream research pinned to Tapir tag `1.5.9` -> commit `d0dbb11b13942e014661e1402b07958b70cd9dba`;
- Safe BIM safety/runtime line already exists and is treated as the trusted mutation kernel;
- no live Archicad write was performed by this research branch.

This V2 audit includes the later acceleration passes through 90 and supersedes the older broad final audit where they differ.

---

## 1. Final architecture decision

The highest-confidence system is a **deterministic Archicad project compiler/runtime**, not an autonomous LLM operating raw Archicad tools.

```text
CONTROLLED TPL / SEED PLN
        +
VERSIONED PROJECT PROFILE
        +
FAVORITES / LIBRARIES / ATTRIBUTES
        +
HOTLINK / GDL ASSET CATALOGS
        +
PARAMETERIZED PROJECT RECIPE
        |
        +---- known task ----------> deterministic compile
        |
        +---- new/ambiguous task --> on-demand AI planner
                                      |
                                      v
                               typed recipe draft
                                      |
                                      v
                           deterministic validation
                                      |
                                unload local AI
                                      |
                                      v
                           SAFE BIM DAG RUNTIME
                                      |
                         certified Tapir 1.5.9 ops
                                      |
                         exact receipts/readback
                                      |
                          incremental QA/docs
                                      |
                                 Publisher
```

The system becomes faster over time by capturing approved work into reusable data, not by asking AI to reinvent each project.

---

## 2. Source-confirmed facts that materially change Safe BIM development

### 2.1 Tapir 1.5.9 is a separate backend contract

1.5.8 -> 1.5.9 spans hundreds of upstream commits and major changes across creation/modification, project commands, common schemas, solid operations, libraries, favorites, documentation and Grasshopper wrappers.

Current offline house primitive code that pins `tapir-1.5.8.json` must not be treated as authoritative for the installed backend.

### 2.2 Tapir 1.5.9 actively fixes parameter-leak/default-state hazards

`CreateElementsCommandBase` reloads defaults per item and snapshots/restores Favorite-modified defaults. Upstream comments document live failures without this reset.

### 2.3 Native readback is stronger than the original Safe BIM assumptions

The research confirmed useful readback for:

- curved Wall fields including `arcAngle`;
- Roof details including single-plane angle/pivot data in 1.5.9;
- Mesh polygon Z data and topology;
- Morph body/origin/axes;
- Hotlink instance node/origin/transform information;
- SEO and Trim relationship state;
- MEP routes/nodes/segments/ports;
- Keynotes, Issues, Design Options, IFC identity and more.

### 2.4 Reuse is first-class Archicad functionality

Graphisoft explicitly supports:

- TPL templates carrying project preferences/settings/defaults;
- Favorites import/export across project/template sources;
- Hotlink Modules for repeated rooms/building structures;
- Publisher Sets for repeatable output;
- Keynotes/autotext for centralized annotations.

### 2.5 Important upstream hazards are now known

Examples:

- missing Favorite GDL content makes the Favorite unappliable;
- Hotlink relink can clear the project's Undo queue;
- story-structure differences during relink can damage dimensions/labels;
- story deletion deletes elements;
- notifications use non-durable callback delivery;
- point-pick blocks the JSON command queue while waiting;
- Teamwork reservation and manual locks are distinct mechanisms;
- multi-item Create arrays are unsafe as a timeout/reconciliation optimization.

---

## 3. Final speed strategy

### 3.1 Reuse before generation

Use the cheapest native reuse level that fits the task:

1. **TPL / seed PLN** — whole project standards and setup.
2. **Project Profile** — machine-readable verification of expected project flavor/resources.
3. **Favorite** — one element's settings/preset.
4. **Hotlink `.mod`** — repeated multi-element assembly.
5. **GDL/HSF library part** — repeated parametric custom object.
6. **Project Recipe** — repeated workflow/building archetype.

The largest time savings are expected here, not from reducing verification.

### 3.2 One write, many efficient reads

Production write policy remains:

`one physical mutation item -> durable returned identity -> exact reconciliation/readback`

Acceleration comes from:

- cached project/resource preflight;
- filtered `GetDetailsOfElements` fields;
- batched readback of independent exact GUIDs;
- dirty-set incremental QA;
- delayed documentation/publisher phases.

### 3.3 Patch exact elements instead of recreate/delete

Where Tapir offers exact-GUID Modify operations and identity can remain stable, prefer patch-in-place to preserve downstream references and reduce GUID churn.

### 3.4 Use native relationships rather than spatial imitation

Prefer:

- SEO links;
- Roof/Shell Trims;
- hosted Window/Door relationships;
- Design Option membership;
- Hotlink source/instance relationships;
- MEP topology;
- native Issue attachments;
- groups.

These are easier to verify and cheaper to update than repeatedly reconstructing equivalent geometry.

---

## 4. Final routine-minimization strategy

### 4.1 Teach-by-example

Architect manually configures a correct exemplar once.

Then capture as:

- Favorite for one element;
- Hotlink Module for an assembly;
- GDL part for one parametric object;
- Recipe for a workflow/archetype.

### 4.2 Selection-first editing

For existing projects:

`user selects exact Archicad elements -> Safe BIM receives GUIDs -> highlight/preview -> approval -> exact modify`

This is faster and safer than natural-language target discovery.

### 4.3 One approval form, not many dialogs

Batch missing human choices into one ScriptUI form. Point-pick is only for choices genuinely faster to click than type.

### 4.4 Room-program automation

Compile schedules/programs into Zones, names, numbers, categories, stamps and downstream labels/QA.

### 4.5 Documentation compiler

Generate documentation only after model milestones:

- sections/elevations/interior elevations;
- associative dimensions;
- labels/text/autotext;
- Keynotes;
- views/layouts/drawings;
- Publisher Sets.

Keep manual Drawing update mode during heavy design churn where appropriate; update/publish explicitly at the documentation milestone.

---

## 5. Final failure-minimization policy

Non-negotiable rules:

1. one physical mutation item per dispatch;
2. persist exact returned identity before dependent work;
3. no blind retry after possible dispatch;
4. geometry match is not ownership;
5. project identity check immediately before physical write;
6. operation-specific verifier, not generic command success;
7. notification is only a dirty hint;
8. AI cannot decide APPLIED/NOT_APPLIED/DONE/retry/ownership;
9. global/project operations use stricter policy than local element operations;
10. interactive operations use explicit WAITING_USER lifecycle;
11. multi-object topology operations use their own receipt/reconciliation model;
12. external output/publisher writes are explicit workflow nodes.

Recommended capability risk classes remain:

- `R0 READ_ONLY`
- `W1 EXACT_LOCAL`
- `W2 RELATION`
- `W3 REPLACE`
- `W4 GLOBAL`
- `W5 MULTI_OBJECT_TOPOLOGY`
- `I1 INTERACTIVE`
- `X1 EXTERNAL_OUTPUT`

---

## 6. Final functionality expansion plan

### 6.1 Immediate / high-confidence value

- Tapir 1.5.9 compatibility layer;
- broad read-only command integration;
- Project Profile;
- typed ProjectRecipe + DAG compiler;
- Favorites list/capture/use;
- Hotlink module placement/catalog;
- selection/highlight/ScriptUI UX;
- Zones;
- documentation generation;
- Keynotes/autotext;
- SEO/Trims;
- Design Options;
- native QA Issues;
- Publisher output;
- IFC identity/type/property reads.

### 6.2 Next certification wave

- corrected Arc/Mesh/Morph/Roof production primitives;
- object/library-part lifecycle;
- advanced document replacement/update operations;
- project-global resource changes under explicit policy.

### 6.3 Separate advanced topology program

- MEP routing/connect/repair;
- Teamwork production adapter if intentionally adopted.

MEP is particularly promising because readback exposes route/node/segment/port topology, but its write semantics belong to W5 rather than the ordinary W1 path.

---

## 7. Final Project Profile result

A first research JSON Schema now exists:

`research/archicad29-tapir159/00_master/project_profile_v0_1.schema.json`

It captures:

- AC29/Tapir compatibility;
- seed template/project identity;
- stories;
- libraries;
- Favorites and dependency fingerprints;
- attributes;
- Hotlink/GDL catalogs;
- documentation expectations;
- global-operation policy.

Production implementation should add validation/migration only after exercising this draft against real TPL/PLN projects.

---

## 8. Final AI architecture

### 8.1 AI is optional

Known tasks skip AI entirely.

### 8.2 AI process lifecycle

For ambiguous/new work:

1. resource broker evaluates whether local inference is appropriate;
2. start one model only;
3. one inference at a time by default;
4. use short context + progressive capability/schema discovery;
5. AI emits typed recipe only;
6. deterministic compiler validates/finalizes it;
7. unload/sleep/terminate local model;
8. physical BIM execution starts afterward.

### 8.3 Resource objective

Optimize for:

- user-visible planning latency;
- RAM peak;
- VRAM peak;
- unload/release latency;
- no meaningful Archicad/Twinmotion slowdown.

Raw tokens/sec is secondary.

### 8.4 Provider choice

Ollama and llama.cpp both remain viable candidates. Selection must be benchmark-based on the user's Legion. Provider choice does not change BIM authority.

---

## 9. Final development-acceleration architecture

Do not hand-write 190+ wrappers.

Use:

`pinned schemas -> generated DTOs/validators/read adapters -> capability registry -> hand-certified mutation semantics`

Add:

- automatic schema-diff report for new Tapir versions;
- progressive command discovery;
- fast offline/golden/property test tier;
- explicit live-probe tier;
- machine-readable evidence/risk/capability manifest;
- deterministic replay fixtures from real readbacks.

This should materially reduce both development time and regression risk.

---

## 10. Final end-to-end production pipeline

### PREPARE

1. open/create controlled TPL/seed project;
2. verify Archicad/Tapir/project identity;
3. load Project Profile;
4. verify stories/resources/libraries/Favorites/assets;
5. resolve exact stable resource IDs;
6. compile or retrieve ProjectRecipe.

### PLAN

7. deterministic recipe if possible;
8. otherwise on-demand AI -> typed recipe;
9. collect all missing user choices once;
10. freeze immutable DAG;
11. unload AI.

### MODEL

12. place native elements/Hotlink/GDL assets;
13. one mutation per dispatch;
14. persist exact receipts;
15. batch filtered readback;
16. execute relation operations only after dependencies verify.

### QA

17. use relations/bboxes/collisions/zone boundaries incrementally;
18. create/update native Issues only for actionable deterministic findings;
19. dirty only affected dependency branches.

### DOCUMENT

20. zones/Keynotes/autotext;
21. sections/elevations;
22. associative dimensions;
23. labels/text;
24. views/layouts/drawings.

### PUBLISH

25. explicit drawing updates where required;
26. Publisher Set output;
27. optional project save checkpoint;
28. final verification/report.

---

## 11. Final empirical work still required

Broad source research is now saturated. Remaining evidence must come from controlled implementation/probes/benchmarks:

1. Arc angle sign/orientation.
2. Single-plane Roof positive-side/pivot convention.
3. Corrected Mesh Z write/readback.
4. Morph body readback against the real 1.5.9 add-on.
5. Filtered read batch-size benchmark.
6. Hotlink placement/update timings and verifier fixture.
7. Favorite/TPL/Profile preflight timing.
8. Documentation phase timings.
9. GDL build/reload timing.
10. AI cold-start/unload/resource-interference benchmark.
11. MEP crash/timeout topology behavior before any production write enablement.

These are narrow empirical tasks, not reasons for another large documentation search.

---

## 12. Final implementation order for maximum project-time reduction

### P0 — must happen first

1. pin Tapir 1.5.9 schema/source;
2. add runtime version gate;
3. correct Arc/Mesh/Morph/Roof contracts;
4. independent offline re-audit.

### P1 — biggest productivity foundation

5. typed capability registry;
6. Project Profile implementation;
7. typed ProjectRecipe + deterministic DAG compiler;
8. reuse catalogs (Favorites/Hotlinks/GDL);
9. filtered batched readback/cache layer.

### P2 — fastest visible user gains

10. selection-first adapter;
11. highlight + ScriptUI one-shot approval;
12. Favorite teach-by-example;
13. Hotlink module teach-by-example;
14. room/zone recipe automation;
15. standard project archetype recipes.

### P3 — documentation and coordination

16. sections/elevations/dimensions/labels/text;
17. Keynotes/autotext;
18. native QA Issues;
19. SEO/trims;
20. Design Options;
21. Publisher pipeline;
22. IFC coordination reads.

### P4 — advanced systems

23. MEP topology adapter;
24. Teamwork adapter if it becomes a chosen workflow.

### P5 — optional AI optimization

25. AIResourceBroker;
26. local-provider benchmark/tuning;
27. progressive capability discovery UI/planner.

AI is intentionally not P0/P1 because known deterministic work should not depend on it.

---

## 13. Final verdict

### Can project production become much faster?

**Yes.** The research consistently points to reuse, deterministic compilation, incremental execution and delayed documentation as the major gains.

### Can routine work be reduced sharply?

**Yes.** Favorites, Hotlinks, GDL parts, Recipes, Zones, Keynotes, generated documents and Publisher cover a large amount of repetitive Archicad work.

### Can functionality be expanded far beyond the current dispatcher?

**Yes.** Tapir 1.5.9 exposes a broad AC29 surface including advanced modeling, relations, documentation, variants, coordination, MEP and project systems.

### Can this be done without increasing failure risk proportionally?

**Yes, if read capability expands broadly while write capability remains certified by risk class and exact reconciliation semantics.**

### Should AI be always running?

**No.** The fastest/reliable architecture uses deterministic recipes first and starts AI only when needed, then unloads it before BIM mutation.

### Is more broad documentation research still the bottleneck?

**No.** The research is now saturated enough to move to implementation plus a small set of controlled live probes and timing benchmarks.

## Final direction

**Build Safe BIM into a deterministic Archicad project compiler around Tapir 1.5.9, with templates/profiles/Favorites/Hotlinks/GDL/Recipes as reusable project knowledge, strict exact-receipt execution as the safety kernel, incremental QA/documentation as the throughput strategy, and AI as a short-lived optional planner rather than a resident controller.**
