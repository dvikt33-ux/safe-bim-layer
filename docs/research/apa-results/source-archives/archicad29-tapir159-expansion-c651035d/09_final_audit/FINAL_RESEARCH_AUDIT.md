# FINAL RESEARCH AUDIT — Archicad 29 / Tapir 1.5.9 / Safe BIM

Research objective:

> Make Archicad projects as fast as practical, minimize routine work, minimize failures, maximize useful functionality, and integrate AI without slowing CAD/BIM work or weakening fail-closed safety.

Research baseline:

- Archicad 29;
- user reports Tapir Additional JSON Commands 1.5.9 installed;
- upstream Tapir research pinned to tag `1.5.9` -> commit `d0dbb11b13942e014661e1402b07958b70cd9dba`;
- Safe BIM product snapshot under study includes the already-audited runtime safety work and the offline house-primitives hardening line;
- no live Archicad write was performed by this research branch.

## 1. Research saturation result

The repeated source/documentation audits now converge on the same architecture. Additional source-only passes are unlikely to materially change the core design.

The remaining high-value unknowns are mostly **empirical/live certification** or **implementation-specific**, not broad uncertainty about what Archicad/Tapir can do.

Across the research workspace there are more than one hundred targeted audit/research passes spanning:

- missing-data/API semantics;
- Tapir 1.5.9 delta;
- AI runtime/resource control;
- developer-loop acceleration;
- project-production acceleration;
- GDL parametric library generation;
- external technology integration;
- pre-final and final targeted passes.

## 2. Core final finding

The fastest robust system is **not an autonomous LLM driving Archicad commands directly**.

It is a reusable project compiler/runtime:

```text
CONTROLLED TEMPLATE / SEED PROJECT
              +
       PROJECT PROFILE
              +
 FAVORITES / ATTRIBUTES / LIBRARIES
              +
 HOTLINK MODULE CATALOG
              +
 OPTIONAL GDL PARAMETRIC LIBRARY
              |
              v
      PARAMETERIZED PROJECT RECIPE
              |
     known recipe? ---------- no ----------> ON-DEMAND AI PLANNER
              |                                  |
              +----------------------------------+
              |
              v
     DETERMINISTIC RECIPE COMPILER
              |
      CERTIFIED CAPABILITY MANIFEST
              |
              v
         SAFE BIM DAG RUNTIME
              |
     exact receipt / reconcile rules
              |
              v
          TAPIR 1.5.9
              |
              v
         ARCHICAD 29 MODEL
              |
              v
  INCREMENTAL QA -> DOCS -> PUBLISH
```

The system gets faster with use because successful human work is captured as reusable Favorites, modules, GDL parts and recipes.

## 3. Fastest end-user workflow found

1. Start from a controlled AC29 TPL or copied seed PLN.
2. Safe BIM verifies project/profile/version identity.
3. User gives a short request or selects exact target elements.
4. Deterministic router checks for an existing recipe.
5. If the task is already known, **no AI starts**.
6. If ambiguous/new, local/cloud AI is loaded only for planning and emits a strict ProjectRecipe draft.
7. One ScriptUI form collects all missing human choices; point-pick is used only when a click is genuinely faster than typing.
8. Compiler freezes the immutable DAG and fingerprints.
9. Local AI is explicitly unloaded before physical BIM execution.
10. Preflight resolves stories, resources, Favorites, libraries and exact IDs.
11. Primary geometry is built using native BIM elements, Favorites and Hotlink Modules.
12. Each physical mutation is one item/dispatch and its exact GUID is durably stored immediately.
13. Independent exact GUIDs are verified with **batched filtered readback**.
14. Only impacted QA/zone/relation nodes run.
15. Documentation is generated/updated at a milestone, not after every geometry edit.
16. Drawing/update/publisher/save are explicit downstream project-global nodes.
17. New approved configurations can be captured back into the reusable catalog.

## 4. Final speed multipliers

### Tier A — largest expected impact

1. **Controlled template/seed project**
   - starts with project standards already present;
   - avoids rebuilding layers, attributes, libraries, views, master layouts and defaults every job.

2. **Project Profile**
   - machine-readable declaration of expected resources/settings;
   - enables fast preflight and deterministic resource resolution.

3. **Favorites**
   - remove huge repeated settings payloads;
   - can be captured from manually-correct exemplar elements;
   - explicit geometry still overrides critical placement/dimensions.

4. **Hotlink Module catalog**
   - turns repeated multi-element assemblies into one instance placement;
   - ideal for apartments, rooms, cores, facade bays and repeated site components.

5. **Parameterized Project Recipes**
   - known project archetypes bypass AI and repetitive coding.

6. **One-write + batched filtered readback**
   - preserves exact receipt safety while reducing read/API overhead.

### Tier B — major project-time reduction

7. Incremental QA rather than full-project checks after every change.
8. Model-to-document DAG: sections/elevations/dimensions/text/labels/views/layouts/drawings/publisher.
9. Selection-first exact-target workflows.
10. Highlight + one-shot approval UI before risky bulk operations.
11. Patch existing exact GUIDs instead of unnecessary recreate/delete.
12. Event-driven cache invalidation instead of polling.

### Tier C — strong functional expansion

13. SEO/trims with relation receipts.
14. Design Option variant workflow.
15. GDL/HSF parametric component factory using LP_XMLConverter.
16. Zones/spatial program automation.
17. Stairs/advanced native elements after verifier certification.
18. MEP after a purpose-built multi-object topology receipt/reconciliation design.

## 5. Final failure-minimization rules

These are non-negotiable even when optimizing speed:

- one physical mutation item per dispatch;
- persist returned exact GUID before moving on;
- never blind retry after possible dispatch;
- geometry match is never ownership;
- dependent writes wait until parent verification;
- project identity check immediately before physical writes;
- source/version/schema compatibility preflight;
- operation-specific verifier rather than generic “command returned success”;
- global/project operations use a stricter risk class;
- interactive commands are isolated WAITING_USER states;
- notifications are cache hints only, never transaction evidence;
- AI cannot decide APPLIED / NOT_APPLIED / DONE / retry / ownership;
- raw MCP/Tapir writes are not exposed to the model.

## 6. Final capability classification

Recommended risk classes:

- `R0 READ_ONLY` — details, relationships, catalogs, QA.
- `W1 EXACT_LOCAL` — one exact element create/modify with strict readback.
- `W2 RELATION` — SEO/trim/relation mutations with tuple receipts.
- `W3 REPLACE` — old identity explicitly replaced by a new identity.
- `W4 GLOBAL` — stories, libraries, geolocation, save, broad recalculation/view/project state.
- `W5 MULTI_OBJECT_TOPOLOGY` — one call may create/split/merge several BIM objects.
- `I1 INTERACTIVE` — user click/form blocks or awaits user input.
- `X1 EXTERNAL_OUTPUT` — publish/export/filesystem output.

Each write capability is promoted only after:

1. exact source/schema contract;
2. pure offline validation;
3. ownership/result model;
4. strict verifier/reconciliation contract;
5. timeout/crash/wrong-project tests;
6. controlled live probe;
7. independent audit;
8. explicit production enablement.

## 7. Final AI architecture

AI is optional and **outside the trusted executor process**.

Preferred runtime behavior:

- deterministic recipe/rules first;
- one local model maximum;
- one inference request maximum;
- short context;
- no local inference while BIM physical dispatch/reconciliation is active;
- explicit unload after plan freeze;
- child process in a Windows Job Object / low-priority scheduling where implemented;
- cloud AI is a valid fallback for rare difficult planning because provider choice does not change write authority.

Initial provider candidates from the AI audit:

1. Ollama with `MAX_LOADED_MODELS=1`, `NUM_PARALLEL=1`, short keep-alive, explicit unload; or
2. llama.cpp server with sleep/explicit process termination for stronger idle-resource control.

The correct provider should be selected by a benchmark on the user's machine, not assumption.

## 8. Final reusable-content strategy

Use the right reuse primitive for the right object:

### Favorite

One element's settings/style/configuration.

### Hotlink `.mod`

Repeated multi-element BIM assembly.

### GDL/HSF library part

One logical parametric custom object.

### Project Recipe

Reusable workflow/building-system/archetype.

### TPL/seed PLN

Whole-project standards and baseline configuration.

This hierarchy minimizes both code volume and repeated Archicad setup.

## 9. Important source-derived corrections to current Safe BIM work

Before new geometry probes/production expansion:

1. Current offline house primitive work still pins `tapir-1.5.8.json`; installed/researched backend is 1.5.9.
2. Tapir 1.5.9 contains large semantic/capability changes and per-item default-reset fixes.
3. Arc wall readback is stronger than the original offline assumptions; remaining key uncertainty is orientation/sign.
4. Current Mesh flat-ground builder likely double-applies the `-0.5` level when it also puts `-0.5` in vertex `meshPolyZ`; the 1.5.9/source-informed contract must be implemented before a live probe.
5. Morph verification must use actual origin/axes/body geometry rather than fake `size/absolute_bottom/absolute_top` echo fields.
6. Single-plane Roof readback in 1.5.9 is strong enough for a strict future verifier; deterministic gable should use two single-plane roof elements rather than assuming a rectangular multi-plane roof is a gable.
7. `CreateElementsCommandBase` in 1.5.9 resets defaults per item specifically to prevent previous-item parameter leakage.

## 10. Final project-standard portability finding

Graphisoft documentation confirms Favorites and project resources are dependency-sensitive. A missing GDL object makes a Favorite unusable; older Favorite imports are safer from a project than old PRF/XML; template files carry project preferences/defaults/settings.

Therefore the fastest reliable path is **template/seed first**, with Project Profile preflight as verification, instead of attempting to reconstruct all standards from raw API calls on every new project.

## 11. Final technology integration verdict

### Core / integrate

- Tapir 1.5.9;
- Safe BIM safety runtime;
- Project Recipe compiler;
- Project Profile;
- Favorites;
- Hotlink modules;
- ScriptUI / selection / highlight / deliberate point-pick;
- GDL/LP_XMLConverter subsystem;
- progressive certified-capability discovery;
- event/cache/QA acceleration.

### Optional frontends / references

- official Grasshopper Live Connection as geometry/parametric design frontend;
- Tapir Grasshopper components as mappings/UI references;
- BIBIM as AI/UI/context/provider source reference;
- IFC/BCF external QA/interoperability;
- official Automation API as baseline/fallback/reference.

### Do not add as a new production write path now

- unrestricted raw MCP -> Tapir writes;
- direct LLM -> Archicad writes;
- direct Grasshopper production writes claimed as Safe BIM-owned;
- a new custom Safe BIM C++ `.apx` duplicating already-available Tapir functionality.

## 12. Immediate implementation roadmap

### Phase 1 — prerequisite compatibility

1. Add/pin Tapir 1.5.9 schema/source artifact.
2. Add runtime version compatibility gate.
3. Fix Arc/Mesh/Morph/Roof offline contracts against 1.5.9.
4. Re-run independent offline audit.

### Phase 2 — Safe BIM compiler foundation

5. Machine-readable capability/evidence registry.
6. Typed/versioned ProjectRecipe.
7. deterministic DAG compiler.
8. Project Profile manifest + hash/preflight.
9. filtered batched readback layer.
10. trace/golden-fixture/evidence tooling.

### Phase 3 — maximum immediate user productivity

11. selection-first target adapter.
12. Highlight + ScriptUI confirmation.
13. Favorite capture/list/use.
14. Hotlink module catalog and exact instance verifier.
15. reusable archetype recipes.

### Phase 4 — docs and advanced capabilities

16. incremental QA dirty graph.
17. section/elevation/dimension/text/label automation.
18. views/layouts/drawings/publisher.
19. SEO/trims.
20. GDL/HSF parametric object factory.
21. Design Options.
22. MEP only after multi-object safety design.

### Phase 5 — optional AI acceleration

23. AIResourceBroker.
24. progressive certified capability discovery.
25. recipe generation/parameter filling.
26. benchmark cold-start/unload/resource admission.

## 13. What still requires empirical evidence

Research should now hand off these narrow points to implementation/probes rather than more broad source archaeology:

- arc wall sign/orientation;
- single-plane roof positive-side/pivot convention;
- Mesh corrected Z write/readback confirmation;
- Morph actual body readback confirmation;
- optimal filtered-read batch size;
- hotlink placement/update timing and exact verifier fixture;
- Favorite/template/profile timing on a representative project;
- documentation pipeline timing;
- LP_XMLConverter generated-object compile/reload timing;
- local AI cold-start/unload RAM/VRAM timing.

## 14. Final verdict

### Can Safe BIM be made much faster for real Archicad project work?

**YES.** The largest gains come from reuse, compilation and incremental execution rather than less verification.

### Can routine work be reduced substantially?

**YES.** Favorites, modules, recipes, generated documents, selection/ScriptUI workflows and parametric library parts cover a large share of repeated setup/model/document work.

### Can functionality be expanded far beyond the current wall/slab/opening dispatcher?

**YES.** Tapir 1.5.9 exposes a large AC29 surface, but capabilities must be certified incrementally by risk class.

### Should speed be obtained by weakening Safe BIM's receipt/reconciliation rules?

**NO.** The research found safer optimizations: template/profile reuse, module reuse, AI bypass, readback batching, filtering, caching, dirty graphs and capture-and-reuse workflows.

### Is more broad source research the current bottleneck?

**NO.** The next bottleneck is implementation of the 1.5.9 compatibility/capability foundation plus a small set of controlled empirical probes and timing benchmarks.

**Final research direction: build a deterministic project compiler around Safe BIM, with Tapir 1.5.9 as the backend, reusable project knowledge as data, and AI as an on-demand planner rather than a resident executor.**
