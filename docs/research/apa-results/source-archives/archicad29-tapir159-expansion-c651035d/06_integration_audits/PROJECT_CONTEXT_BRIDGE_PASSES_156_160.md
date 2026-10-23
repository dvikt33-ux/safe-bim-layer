# PROJECT CONTEXT BRIDGE — passes 156–160

Date: 2026-09-27

Final targeted passes after prefinal audit.

## Pass 156 — external ChatGPT user workflow

Target user experience:

1. user works normally in Archicad;
2. Safe BIM context indicator remains compact (`ChatGPT context: synced / pending / offline`);
3. local bridge coalesces edits and publishes asynchronously;
4. user asks ChatGPT for project-specific code in the normal conversation;
5. assistant reads fixed-path current project state before generating code;
6. response is based on an explicit snapshot ID;
7. user inserts code/recipe in Safe BIM palette;
8. Safe BIM detects whether the context is still current before allowing Preview/Execute.

No PowerShell and no manual geometry dump are required.

Important limitation: ChatGPT itself cannot continuously “watch” local Archicad. It gets current state when the conversation/tool reads the published mirror. The bridge therefore solves freshness through automatic publication plus stale-context rejection, not through magical shared memory.

## Pass 157 — code delivery / no-copy future

Immediate V1 keeps the user's current workflow: ChatGPT returns code/recipe and user pastes it into the Safe BIM palette.

This is deliberately compatible with the documented standard GitHub ChatGPT connection, which is primarily read access.

Future paths:
1. connector/app with explicit repository write action;
2. custom MCP/remote bridge when available/appropriate;
3. existing local dispatcher pattern for bounded handoff;
4. embedded AI directly inside Safe BIM.

Even when two-way delivery exists, remote output is only an inbox proposal. Never auto-run it.

## Pass 158 — performance budget

The bridge must be invisible during modeling.

Design targets to validate experimentally:
- edit callback: enqueue identifiers only; no network/deep serialization;
- no project-wide element observer attachment during startup;
- shallow index reconciliation should be substantially cheaper than deep geometry scan;
- deep details refreshed only for changed/relevant elements;
- Git commit/push runs in external worker process/thread, not Archicad UI operation;
- event storms coalesce into one publication;
- publication failure does not block BIM work.

Benchmark matrix to collect:
- 1k / 10k / 50k elements;
- cold initial index;
- one-wall edit;
- 100-element edit;
- story/attribute change;
- Save;
- Git online/offline;
- multiple rapid edits.

## Pass 159 — live certification backlog

Before production enablement, run controlled read-only/manual-edit probes:

### Notification coverage
Observe which GUIDs appear for:
- drag/stretch;
- settings-dialog geometry/property edit;
- create;
- delete;
- undo/redo;
- property/classification change;
- story change;
- relevant attribute changes.

Compare event queue against state-index/modiStamp reconciliation.

### Project identity
Test:
- normal Save;
- Save As;
- filesystem copy opened separately;
- copied PLN on second path;
- optional Teamwork case later.

Record CEIPProjectID, Safe BIM logical ID, project modiStamp.

### Performance
Measure shallow index and changed-element deep refresh latency.

### Publication
Measure local materialization, git commit, push, and external ChatGPT fixed-path fetch latency.

No BIM mutation is required for the bridge implementation itself beyond user-driven/manual test edits.

## Pass 160 — final design stability test

The architecture was challenged against these cases:

- GitHub down -> local Safe BIM still works;
- assistant sees 30-second-old snapshot -> execution rejects changed targets;
- user switches PLN -> project ID mismatch blocks recipe;
- target deleted -> precondition failure;
- another layer/building-material definition changes -> relevant contract hash invalidates recipe;
- two Archicad instances -> session pointer + project ID disambiguates;
- missed edit notification -> index/modiStamp reconciliation catches it;
- giant project -> shallow index + sharded deep cache prevents full JSON regeneration;
- assistant requests global task -> full-project context level/shards available;
- sensitive model -> publication policy requires private repo and configurable scope;
- remote recipe arrives twice -> recipe ID replay protection;
- raw Python arrives -> classified untrusted and never auto-executed.

No architecture-breaking contradiction was found.

Final recommendation: implement the bridge in stages, beginning with local state index/cache and private one-way GitHub mirror. Bidirectional recipe transport comes later and must not block V1.
