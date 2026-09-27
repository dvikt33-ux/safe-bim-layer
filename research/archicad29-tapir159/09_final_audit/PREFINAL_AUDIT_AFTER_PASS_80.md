# Pre-final audit after project-acceleration pass 80

This audit supersedes the older pre-final checkpoint at pass 40 for the expanded objective:

> make Archicad projects as fast as practical, minimize routine, minimize failures, maximize useful functionality, and keep AI/resource usage from slowing the CAD/BIM workload.

No live Archicad writes were performed by this research branch.

## 1. Convergence status

The research has now converged on a stable production architecture. New source discoveries are expanding *capability breadth* (MEP, Keynotes, Issues, IFC, publishing) but are no longer changing the core safety model.

The dominant architecture remains:

`template/profile + reusable assets -> typed ProjectRecipe -> deterministic compiler -> Safe BIM DAG runtime -> certified Tapir operations -> exact readback -> incremental QA/docs/publish`

AI remains an on-demand planner/compiler assistant outside the trusted executor.

## 2. Highest-value project-speed mechanisms

### A. Reuse before generation

1. TPL/seed project for whole-project standards.
2. Project Profile for machine verification/resolution.
3. Favorites for settings-heavy single elements.
4. Hotlink Modules for repeated multi-element assemblies.
5. GDL/HSF parts for repeated parametric custom objects.
6. Versioned Project Recipes for repeated project archetypes/workflows.

### B. Keep the critical Archicad loop small

1. one physical mutation item per dispatch;
2. exact returned identity persisted immediately;
3. filtered/batched readback only after durable identities exist;
4. dependency-aware incremental QA;
5. documentation and publishing deferred to phase boundaries;
6. no resident AI during physical write/reconciliation.

### C. Native relationships instead of geometric imitation

Prefer Archicad-native relationships when available:

- hosted openings;
- SEO links;
- roof/shell trims;
- Design Option membership;
- groups;
- Hotlink instance/source relationships;
- MEP route/node/segment/port topology;
- Issue -> exact element attachments.

This reduces both modeling work and reconciliation ambiguity.

## 3. Functionality expansion map

### Near-term / high confidence

- broad read-only model/query/QA integration;
- Favorites capture/list/use;
- Hotlink module placement after dedicated verifier;
- selection/highlight/ScriptUI workflows;
- Zones and room-program automation;
- sections/elevations/dimensions/text/labels/views/layouts;
- Keynotes/autotext;
- SEO/trims;
- Design Options;
- Publisher-set output;
- IFC identity/type/property reads;
- native QA Issues.

### Medium-term / requires operation-specific contracts

- advanced Roof/Mesh/Morph primitives;
- Hotlink update/relink governance;
- project-global library/story/geolocation changes;
- complex document replacement/update operations;
- object/library-part factory lifecycle.

### Later / separate safety design

- MEP create/connect/repair topology;
- Teamwork reservation/send/receive production flow;
- any operation that splits/merges/replaces multiple BIM objects in one call.

## 4. Most important failure-prevention findings

1. Tapir 1.5.9 must be separately pinned/certified; current house-primitives code still pins 1.5.8 schema.
2. Create arrays must not be used as a write-throughput shortcut because transport loss can hide a partial subset.
3. Notifications are cache-invalidation hints only because delivery is intentionally non-durable.
4. Favorite existence is not Favorite usability: missing GDL/library dependencies can make a Favorite unappliable.
5. Hotlink source update/relink is high risk; relinking can clear the Undo queue and story differences can damage dimensions/labels.
6. Story changes are project-global and deletion destroys contained elements.
7. Manual lock, Teamwork reservation and runtime execution lock are distinct mechanisms.
8. MEP is a multi-object topology problem, not a generic create/readback problem.
9. AI must never own APPLIED/NOT_APPLIED/DONE/retry/ownership decisions.
10. Broad upstream APIs should be exposed faster on the read side than on the write side.

## 5. AI and compute architecture audit

The user requirement is that AI must not sit in the background consuming RAM/VRAM or slow Archicad/Twinmotion/other work.

The research supports:

- deterministic recipe lookup first;
- start local AI only when planning/reasoning is actually needed;
- one loaded model maximum;
- one inference at a time by default;
- short context and progressive command/schema discovery;
- freeze a typed recipe before BIM execution;
- unload/sleep/terminate local model before the write/reconcile phase;
- use cloud AI when it is more efficient than keeping a large local model resident;
- never couple runtime safety state to a model process being alive.

The remaining AI choice is empirical: benchmark Ollama vs llama.cpp (and any chosen alternative) for cold-start, task latency, unload latency, RAM/VRAM release and interference with Archicad/Twinmotion.

## 6. Development-speed architecture audit

To stop hand-writing integration boilerplate for 190+ commands:

- pin the upstream schema/source snapshot;
- generate DTOs/validators/read adapters mechanically;
- use progressive command discovery;
- maintain a machine-readable capability registry with risk class/evidence/version;
- hand-write only semantic safety contracts and strict verifiers for mutation operations;
- auto-diff future Tapir schemas to identify changed commands/contracts;
- run fast offline/golden/property tests by default and expensive/live tiers explicitly.

This reduces both coding time and schema-drift bugs.

## 7. Contracts still missing before implementation can be called complete

### Project Profile

Needs a concrete typed/versioned schema covering:

- Tapir/Archicad compatibility;
- stories;
- libraries/packages;
- Favorites/dependencies;
- attributes/profiles/materials;
- classifications/properties;
- zone categories;
- annotation/document presets;
- Hotlink/GDL asset catalogs;
- navigator/layout/publisher expectations.

### Reusable asset identity

Need policy for:

- immutable/versioned `.mod` paths and hashes;
- GDL Main GUID/version;
- Favorite source/version/fingerprint;
- library/package fingerprint.

### Native QA Issue lifecycle

Need deterministic dedup/update key so repeated QA runs update the same issue rather than create duplicates.

### Keynote lifecycle

Need identity/update contract by GUID/key/folder, including conflict policy if a user manually edits the Keynote tree.

### MEP topology receipt

Need a dedicated receipt model for route root + nodes + segments + ports + split/merge/branch outcomes.

### Documentation invalidation

Need an explicit dependency map from model changes to zones, dimensions, labels, views, drawings and publisher output.

## 8. Pre-final implementation priority

### Priority 0 — compatibility correction

1. pin Tapir 1.5.9 schema/source;
2. runtime version gate;
3. update Arc/Mesh/Morph/Roof contracts;
4. independent offline re-audit.

### Priority 1 — compiler/profile/reuse foundation

5. capability registry;
6. typed ProjectRecipe;
7. deterministic DAG compiler;
8. typed Project Profile;
9. reusable Favorite/Hotlink/GDL catalogs;
10. filtered batch-read layer and cache invalidation.

### Priority 2 — immediate architect productivity

11. selection-first exact targets;
12. highlight + one-shot approval UI;
13. Favorite teach-by-example workflow;
14. Hotlink module teach-by-example workflow;
15. standard room/program recipes;
16. zones + documentation generation.

### Priority 3 — expanded professional workflow

17. Keynotes/autotext;
18. native QA Issues;
19. SEO/trims;
20. Design Options;
21. publisher/output phase;
22. IFC coordination reads.

### Priority 4 — advanced topology

23. MEP safe adapter;
24. Teamwork adapter if intentionally adopted.

## 9. Pre-final verdict

### Architecture stable enough to implement?

YES, at the architecture level.

### Is the raw upstream capability surface the limiting factor?

NO. Tapir 1.5.9 exposes substantially more than the current Safe BIM dispatcher uses.

### Biggest productivity bottleneck now?

Lack of a reusable project compiler/profile/catalog layer, not lack of individual Archicad commands.

### Biggest safety bottleneck now?

Certifying each mutation family's ownership/readback/reconciliation semantics while keeping project-global and multi-object operations out of the generic W1 path.

### Does more research still have value?

YES, but only in focused contract/benchmark areas. Another pass set should now convert the remaining gaps into concrete machine-readable schemas/policies rather than continue broad capability discovery.
