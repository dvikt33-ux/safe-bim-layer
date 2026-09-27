# PROJECT CONTEXT BRIDGE ARCHITECTURE

Date: 2026-09-27
Status: research architecture, no product code changes

## Purpose

Give external ChatGPT enough current Archicad context to generate safe project-specific code/recipes without making GitHub, ChatGPT, or any LLM authoritative for BIM state.

## Final data flow

```text
ARCHICAD 29
   │
   ├─ native Safe BIM read/event adapter
   │    ├─ project modiStamp
   │    ├─ element GUID + modiStamp index
   │    ├─ edited GUID notifications
   │    └─ project/session identity
   │
   └─ Tapir 1.5.9 read APIs
        ├─ stories
        ├─ selection
        ├─ details(fields=...)
        ├─ 3D bounding boxes
        └─ relations
             │
             v
LOCAL CONTEXT SERVICE (authoritative mirror/cache)
   ├─ SQLite
   ├─ canonical element records
   ├─ relation records
   ├─ QA state
   └─ outbound snapshot queue
             │
             v
ASYNC GIT PUBLISHER
   │
   v
PRIVATE GitHub state repository
   │ fixed paths / coherent snapshot commit
   v
EXTERNAL CHATGPT
   ├─ read manifest
   ├─ read selection/recent changes
   └─ fetch only relevant shards
             │
             v
CODE OR SAFE RECIPE
             │
             v
LOCAL SAFE BIM VALIDATION
   ├─ project match
   ├─ snapshot/precondition checks
   ├─ capability checks
   ├─ preview/checkpoint/sandbox
   └─ only then physical BIM write
```

## Source of truth hierarchy

1. **Open Archicad project** — ultimate truth.
2. **Local Safe BIM cache** — authoritative machine mirror for automation.
3. **GitHub snapshot** — external assistant mirror.
4. **ChatGPT conversation/model memory** — never authoritative.

## Native bridge minimum

### `GetSafeBIMProjectStamp`
Desired read-only result:

```json
{
  "logicalProjectId": "...",
  "ceipProjectId": "...",
  "projectModiStamp": 12345,
  "projectName": "...",
  "teamwork": false,
  "archicadInstanceId": "..."
}
```

### `GetSafeBIMElementStateIndex`
Desired read-only result per element:

```json
{
  "guid": "...",
  "type": "Wall",
  "modiStamp": 123,
  "floorIndex": 1,
  "layerIndex": 12,
  "groupGuid": null,
  "hotlinkGuid": null,
  "renovationStatus": "Existing"
}
```

This should be intentionally shallow and fast.

### Edit event adapter
Use AC29 `EditNotificationInterface` as a dirty-GUID accelerator. It is not the completeness authority; index reconciliation is.

## Local SQLite candidate tables

- `project_state`
- `element_index`
- `element_details`
- `element_relations`
- `attribute_index`
- `snapshots`
- `recent_changes`
- `qa_findings`
- `outbound_publish_queue`

`element_index` key = GUID.

Store both `native_modi_stamp` and canonical `state_hash`.

## Snapshot publication

### Fast path
Edited GUID event -> mark dirty only.

### Reconciliation path
Before publish:
1. acquire current project stamp;
2. acquire shallow element index;
3. diff GUID sets/modiStamps;
4. deep-read changed GUIDs with minimal fields;
5. refresh dependent relations/QA neighborhoods;
6. compute hashes/root hash;
7. materialize Git tree;
8. commit/push asynchronously.

### Publication triggers
- explicit `Синхронизировать ChatGPT`;
- after Archicad Save;
- before Safe BIM stage (if external context is enabled);
- after Safe BIM stage;
- opening/requesting external AI context;
- debounced idle publication during manual editing.

## Git repository requirement

Real project state must be in a **private** repository. Current research/product repositories were observed as public via GitHub API and are not eligible for project geometry.

Recommended one-time private repo:

`safe-bim-project-state`

One repo can hold multiple projects under logical project IDs.

## Git layout

```text
branch model-state
  active.json
  projects/<project_id>/current/manifest.json
  projects/<project_id>/current/stories.json
  projects/<project_id>/current/selection.json
  projects/<project_id>/current/model_summary.json
  projects/<project_id>/current/recent_changes.json
  projects/<project_id>/current/qa_summary.json
  projects/<project_id>/current/attributes/index.json
  projects/<project_id>/current/elements/index.csv
  projects/<project_id>/current/elements/shards/<00-ff>.json
  projects/<project_id>/current/relations/shards/<00-ff>.json

optional branch assistant-inbox
  projects/<project_id>/inbox/<recipe_id>.json
```

Separate writers avoid push conflicts.

## External ChatGPT read protocol

For any request that would generate project-specific Archicad code:

1. read `active.json`;
2. read active project `manifest.json`;
3. verify snapshot `complete=true` and not marked dirty-at-publish;
4. read selection + story map + recent changes + QA summary;
5. locate target GUIDs in compact index;
6. load only relevant element/relation shards;
7. generate answer/recipe tagged with `project_id`, `snapshot_id`, root hash, and target preconditions.

Do not infer unseen current geometry from conversation memory.

## Local execution protocol

When code/recipe reaches palette:

1. parse as `SAFE_RECIPE` or `UNTRUSTED_CODE`;
2. reread current local project identity;
3. check target GUIDs and state hashes;
4. check story/attribute/relationship preconditions;
5. if any mismatch => `STALE_CONTEXT`, writes=0;
6. otherwise continue through normal Preview/Checkpoint/Sandbox/Safe Runtime.

## Context levels

### Selection
Smallest/fastest. Selection + local neighbors + required attributes.

### Active story
All shallow index on active story, deep selection/dirty neighborhood.

### Full project
Full shallow index plus all maintained shards. Best for broad planning, highest privacy/storage cost.

User may configure default; Safe BIM can escalate temporarily when a query needs more context.

## External AI vs embedded AI

Both should consume the same canonical context schema.

- embedded/local AI reads local cache directly: zero GitHub latency;
- external ChatGPT reads private GitHub mirror;
- deterministic recipes are transport-independent.

This keeps future MCP/API integration from forcing a rewrite of BIM state semantics.

## Safety invariants

- no network work on Archicad edit callback;
- no GitHub dependency for local modeling;
- no remote auto-execution;
- no model search/adoption to satisfy a remote receipt;
- wrong project => 0 writes;
- stale snapshot => 0 writes;
- changed target hash => 0 writes;
- public repository => publication blocked;
- Git push conflict => publication STOP, never silent force;
- secrets/local credentials never exported.
