# Architectural AI checkpoint 04 — performance-first reactive kernel

Date: 2026-10-07
Status: research checkpoint / architecture proposal. Not yet the final AI-architect specification.

## Why this checkpoint exists

Before expanding the architectural dependency, normative, intent, detail, equipment and context graphs, the system needs a performance skeleton that can absorb those layers without turning each edit into a full-project recomputation.

The core should behave more like an incremental compiler / reactive engineering kernel than a "mega graph queried from scratch".

## Audit of the current watcher

Current branch `feature/working-archicad-mvp`, file `scripts/archicad_change_watch.py`:

- polls Archicad periodically;
- calls `GetAllElements`;
- requests `GetDetailsOfElements` and `Get3DBoundingBoxes` for the full GUID set;
- hashes every element to detect changes.

This is acceptable as a proof of live synchronization, but it must not become the production change-propagation mechanism.

Graphisoft's native API supports element observers and BeginEvents/EndEvents notifications. Use those to capture deltas.

## Performance-first architecture

### 1. Thin Archicad Adapter (APX)

Responsibilities only:
- initial targeted/full bootstrap read;
- attach observers to relevant existing elements;
- catch new elements and attach observers immediately;
- collect modify/edit/delete/property/classification/undo/redo events;
- group events by `APINotifyElement_BeginEvents/EndEvents`;
- expose a small monotonic event queue;
- targeted reads for changed GUIDs only;
- execute approved BIM diffs;
- read back committed changes.

Do NOT run heavy graph traversal, constraint solving, normative checking or GPT calls in notification callbacks.

Recommended MVP command surface:
- `GetChangeEventsV1(afterSequence)`
- `GetModelDeltaV1(guids, fieldsMask)`
- `ApplyDesignDiffV1(baseRevision, operations)`
- `GetProjectRevisionV1()`

The external process may poll this tiny event queue frequently; that is very different from polling the whole BIM model.

### 2. External Design Engine (C++20)

Keep the heavy reasoning-support kernel outside Archicad:
- entity registry;
- typed dependency graph;
- spatial indexes;
- constraint registry;
- dirty/invalidation engine;
- candidate overlays;
- solvers;
- project rule pack;
- architectural intent metrics;
- scheduler;
- cache;
- persistence;
- profiler instrumentation.

Reason: Archicad database writes must occur in appropriate command/main-thread contexts, but read-only add-on commands may execute on a parallel thread. Heavy computation must not block Archicad's UI/event loop.

### 3. Reasoning Gateway

GPT receives only:
- the user's design goal;
- current project revision;
- relevant impact subgraph;
- relevant rules and provenance;
- candidate deltas;
- affected architectural-intent invariants;
- exact checker results.

GPT must never receive the complete model dump as routine context.

## Revision and concurrency model

Every completed Archicad event group increments `project_revision`.

Every AI candidate stores:
- `base_revision`;
- touched entity IDs;
- touched property masks;
- expected input fingerprints.

Before commit:
- if current revision != base revision, candidate is `STALE`;
- rebase/recompute the affected transaction;
- never apply a stale candidate.

Own commits must be tagged/reconciled so observer events caused by the commit become read-back evidence, not a second independent redesign request.

## Entity IDs and hot-path representation

External/API identity:
- Archicad GUID / stable document/rule IDs.

Hot internal identity:
- dense 32-bit integer `EntityId`.

Do not store long strings or full provenance records on each hot graph edge.

Hot edge:
- src EntityId;
- dst EntityId;
- compact RelationKind;
- small flags / policy ID.

Warm/cold metadata (reason, source clause, notes, provenance) stays in persistent storage and is retrieved when explaining/auditing.

Rich ontology can therefore contain many relation types without forcing every operation to scan every type.

## Do not build one universal fully-connected mega graph

Use specialized stores:

1. **Causal/semantic graph**
   Stable meaningful dependencies only.

2. **Containment/hierarchy indexes**
   Site/building/story/zone/system ownership.

3. **Spatial indexes**
   R-tree/AABB. Proximity and intersection relations are queried on demand, not stored as all-pairs graph edges.

4. **Constraint components**
   Cyclic strongly-connected components (SCCs) solved as units; condensation graph is a DAG.

5. **Rule inverted indexes**
   Map touched entity types/properties to only the potentially applicable rules.

6. **Intent index**
   Map project elements/parameters to protected exterior/interior intent invariants and key views.

## Dirty propagation

Each entity/property has a generation/version.

A change creates a compact `ChangeSet`.

Propagation:
`ChangeSet -> direct dependency index -> dirty bitmap/set -> spatial-neighbor query -> affected SCCs -> relevant rule IDs -> derived recomputation`.

Do not eagerly recompute every derived value.

Use lazy/memoized derived values:
- if dependency generations have not changed -> cache HIT;
- otherwise recompute and store new dependency fingerprint.

Use fast content fingerprints for caches; xxHash/XXH3 is a candidate. Cryptographic hashing is unnecessary for hot cache identity.

## Candidate states: copy-on-write overlays

Never clone the whole project for each alternative.

`CandidateState = BaseState + DeltaOverlay`.

Overlay stores only:
- modified properties;
- created/deleted candidate entities;
- derived values invalidated by this candidate;
- candidate-specific solver/check results.

A rejected candidate is discarded in O(delta), not by restoring an entire project copy.

## Solver cascade

Do not send every change directly to CP-SAT/Z3.

Use cheapest sufficient method first:

0. direct deterministic formula / lookup;
1. interval/domain propagation;
2. spatial/local geometry checks;
3. small enumerated candidate set;
4. local constraint component solve;
5. CP-SAT for discrete modular/combinatorial choices;
6. Z3 for symbolic/logical constraints, incremental scenarios and unsat explanations;
7. heavy/global optimization only as an explicit redesign operation.

Architectural millimetres map naturally to integer domains for CP-SAT.

Each expensive solver receives:
- only the affected SCC/local component;
- hard time/resource limit;
- cancellation token;
- existing state as initial/hint when supported.

Timeout is not PASS. Return `UNKNOWN/NEEDS_DEEP_SOLVE`.

## Multi-fidelity engineering checks

Every discipline should have at least two levels.

### Interactive guard
Fast conservative check:
- span envelope;
- clearance;
- rule bounds;
- topology;
- module membership;
- bounding-box collision;
- service reachability;
- basic daylight proxy.

### Deep verification
Only when the transaction survives cheap checks or at a release gate:
- detailed structural analysis;
- Radiance/daylight;
- thermal/energy;
- full clash/IFC audit;
- detailed MEP calculations;
- visual/MLLM intent audit.

Early rejection prevents expensive simulations from running on obviously invalid candidates.

## Architectural intent optimization

Do not run visual AI comparison after every small edit.

Always-on deterministic intent checks:
- protected axes/datums;
- window-family relationships;
- facade rhythm;
- massing/silhouette values;
- material system IDs;
- interior key axes/spatial hierarchy.

Run rendered/key-view MLLM comparison only if:
- the change cone touches envelope/interior protected-view dependencies;
- or at an explicit milestone/release audit.

## Normative graph optimization

Full normative corpus is a COLD knowledge graph.

At project classification/start:
1. resolve jurisdiction/date/building class/site/context;
2. traverse normative references;
3. compile an ACTIVE PROJECT RULE PACK;
4. index active rules by entity class/property/input;
5. store exact source/version/provenance.

Interactive project edits evaluate only the active indexed rules whose inputs changed.

A normative-source update uses the opposite propagation direction:
source diff -> affected rule nodes -> active pack delta -> bound project parameters -> project impact cone.

Do not re-read/re-interpret all PDFs during an ordinary wall move.

## Hot / warm / cold data tiers

### HOT — RAM
- dense entities;
- typed adjacency;
- spatial boxes/indexes;
- current property values;
- active rule bindings;
- dirty sets;
- SCC map;
- small candidate overlays.

### WARM — local SSD
- SQLite project database/event log;
- decision history;
- rule pack;
- equipment/detail metadata;
- cached audits;
- transaction records.

SQLite WAL is suitable for local single-machine persistence: readers can coexist with a writer and writes append to the WAL.

### COLD
- full standards/PDFs;
- historical rule versions;
- manufacturer albums;
- precedents;
- images;
- large evidence artifacts;
- Google Drive / file library.

Cold data is retrieved only when building/updating rule/library knowledge or explaining provenance.

## Task parallelism

The project change graph often contains independent dirty components.

Use one long-lived C++ task executor and execute independent checks concurrently:
- geometry;
- rule groups;
- MEP guard checks;
- intent metrics;
- candidate checks.

Taskflow is a strong MVP candidate:
- header-only C++20;
- Windows support;
- work-stealing executor;
- dynamic subflows;
- built-in task-graph profiling.

Do not create/destroy an executor per edit.

Archicad modifications remain serialized through its required command/main-thread path.

## Archicad-specific performance rules

1. Use native observer notifications instead of full-project polling for production synchronization.
2. Use `BeginEvents/EndEvents` to coalesce one user operation into one design transaction.
3. Query only changed GUIDs and only required data masks.
4. Avoid expensive memos/3D bodies unless an affected checker actually needs them.
5. For AI writes, batch related modifications into a single undoable Archicad command.
6. Prefer multi-element/batched API functions where applicable.
7. Do not issue individual database modifications as separate commands when they can be grouped: Archicad otherwise may perform derived-data calculation/screen refresh after each command.
8. After commit, targeted read-back only on touched/derived-check elements.
9. Periodic/full integrity scan is a safety audit/fallback, not the interactive change loop.

## Suggested local tool stack

### Install/use for the optimized skeleton
- C++20 + existing Archicad DevKit/toolchain;
- CMake + Ninja;
- vcpkg or one controlled dependency mechanism;
- Boost.Graph;
- Boost.Geometry R-tree;
- Taskflow;
- SQLite;
- OR-Tools CP-SAT;
- Z3;
- Tracy Profiler;
- Google Benchmark;
- test framework already used by the repository or Catch2/GoogleTest;
- Graphviz for small affected-subgraph/audit visualizations.

### Add when justified by benchmarks
- CRoaring for large dirty/rule/entity sets;
- xxHash for high-volume dependency/cache fingerprints;
- GEOS for richer independent 2D topology if Boost.Geometry is insufficient;
- IfcOpenShell/IfcTester for independent release audits.

### Research/later, NOT MVP dependencies
- Soufflé Datalog: useful for stable recursive rule/dependency programs; compiled C++ and parallel evaluation are attractive, but compilation/startup complexity argues against placing it in the first interactive kernel.
- Feldera/DBSP: promising for very large incremental derived-state pipelines; use only if the custom invalidation engine becomes the bottleneck.
- SuiteSparse:GraphBLAS/LAGraph: high-scale graph analytics; unnecessary until real edge counts/algorithms justify it.
- Neo4j/Memgraph: useful for exploration/visualization/persistent knowledge queries, not recommended in the hot interaction loop.
- DuckDB: useful for analytics over logs/SQLite/Parquet, not the live state engine.

## Performance budgets to benchmark (targets, not guarantees)

The system must have explicit budgets before architecture logic grows.

- observer callback/event enqueue: effectively invisible to UI; no heavy work;
- event group -> dirty subgraph: target <100 ms typical;
- local deterministic geometry/rule guard pass: target <500 ms typical;
- normal local constraint solve: target <2 s;
- GPT architectural comparison/escalation: allowed several seconds, but only on architecturally meaningful transactions;
- global redesign/deep simulation: explicit operation with visible progress/cancellation; never hidden behind an ordinary edit.

No routine wall/door/equipment interaction should trigger a half-hour solve.

## Benchmark gates before adding "muscles"

Build synthetic and live benchmarks.

### Scales
- current-size live project;
- 10k entities / 100k edges;
- 100k entities / 1M edges;
- optional stress: 1M entities / 10M edges.

### Measure
- initial synchronization;
- event queue latency;
- targeted element refresh;
- dependency-cone traversal;
- SCC discovery;
- R-tree update/query;
- rule index selection;
- dirty-set union/intersection;
- candidate overlay creation/discard;
- local solver times;
- 1/10/100/1000-element Archicad batch commit;
- read-back verification;
- memory use;
- cache hit ratio.

Instrument the hot path with Tracy and microbenchmarks with Google Benchmark.

### Stop/go gate

Do not add large architectural graph families until:
- incremental event capture works;
- no full dump is required for routine edits;
- candidate overlays work;
- stale revision protection works;
- cache/dirty propagation works;
- performance metrics are recorded and regression-tested.

## Research findings supporting the architecture

- Graphisoft API supports observing specific elements and reports New/Change/Edit/Delete plus BeginEvents/EndEvents, Undo/Redo, property and classification events.
- Read-only Add-On commands may use parallel-thread execution; commands that modify the Archicad database require main-thread scheduling.
- Archicad documents that separate modification commands can trigger derived-data calculations/screen refresh after each call; related writes should be grouped.
- Boost.Graph SCC is O(V+E).
- Boost.Geometry R-tree supports dynamic insert/remove and spatial queries; packed bulk load can improve initial query structure.
- Taskflow uses a long-lived work-stealing executor and supports dynamic task graphs.
- Z3 supports incremental push/pop scopes and tracked/assumption constraints for infeasibility explanation.
- CP-SAT is well suited to integer/discrete constraints and supports explicit time limits/statuses.
- SQLite WAL allows concurrent readers with a writer on one machine.
- Soufflé supports parallel evaluation and compiled C++; Feldera DBSP is built around incremental view maintenance.

## Immediate implementation order

1. Native event observer + sequence queue.
2. Targeted delta read command.
3. External C++ engine process.
4. Project revision / stale-candidate guard.
5. Dense EntityRegistry + typed graph.
6. R-tree spatial index.
7. Dirty generation/cache engine.
8. Candidate copy-on-write overlay.
9. Taskflow scheduler + Tracy instrumentation.
10. Simple deterministic constraint registry.
11. Only then integrate CP-SAT/Z3.
12. Only after benchmark PASS start adding the large architectural/normative/detail graph families.
