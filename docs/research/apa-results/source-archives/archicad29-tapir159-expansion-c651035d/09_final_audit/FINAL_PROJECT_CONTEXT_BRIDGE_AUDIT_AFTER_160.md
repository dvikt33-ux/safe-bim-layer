# FINAL PROJECT CONTEXT BRIDGE AUDIT — after pass 160

Date: 2026-09-27
Scope: external ChatGPT awareness of the current Archicad project state, with Safe BIM remaining the only BIM execution authority.
Status: final research synthesis for this workstream. No product code changes. No Live BIM writes.

---

# 1. Final objective

The user should be able to work normally in Archicad, open ordinary ChatGPT, ask for project-specific code/recipes, and have the assistant inspect a recent machine-readable representation of the current model before answering.

The user should not have to:
- manually export geometry;
- describe every selected element;
- copy GUID lists;
- run PowerShell;
- keep a local LLM permanently resident.

The bridge must improve context and speed without moving BIM authority outside Safe BIM.

---

# 2. Final architecture

```text
ARCHICAD 29
   │
   ├─ Safe BIM native read/event adapter
   │    ├─ logical project identity
   │    ├─ project modiStamp
   │    ├─ element GUID + modiStamp shallow index
   │    └─ changed-GUID event hints
   │
   ├─ Tapir 1.5.9 read APIs
   │    ├─ stories / active story
   │    ├─ selection
   │    ├─ details(fields=...)
   │    ├─ 3D bounding boxes
   │    └─ relations
   │
   v
LOCAL CONTEXT SERVICE / SQLite
   │  authoritative automation mirror
   │
   ├─ canonical element records
   ├─ relation shards
   ├─ QA state
   ├─ recent changes
   └─ outbound publish queue
            │
            v
ASYNC GIT PUBLISHER
            │
            v
PRIVATE PROJECT-STATE REPOSITORY
            │ coherent immutable snapshot commit
            v
EXTERNAL CHATGPT
   │
   ├─ reads active project manifest
   ├─ reads selection / recent changes / QA
   ├─ fetches only relevant element/relation shards
   └─ generates code or typed Safe Recipe bound to snapshot/preconditions
            │
            v
SAFE BIM PALETTE / RUNTIME
   ├─ re-read current local authoritative state
   ├─ project-id check
   ├─ target/state-hash preconditions
   ├─ capability validation
   ├─ Preview / Checkpoint / optional Sandbox
   └─ physical write only if all checks still pass
```

GitHub is never in the physical BIM write path.

---

# 3. Source-of-truth hierarchy

1. Open Archicad project.
2. Local Safe BIM cache/index.
3. Private GitHub project-state snapshot.
4. External ChatGPT context/conversation.

A lower layer must never override a higher layer merely because it is newer in wall-clock time.

---

# 4. Why the architecture is technically feasible

Confirmed available primitives are sufficient:

## Tapir 1.5.9
- project info;
- stories and active story;
- current selection;
- all elements / elements by type;
- selective `GetDetailsOfElements` fields;
- global 3D bounding boxes;
- element relations;
- current window type;
- save project and other project operations.

## Archicad 29 C++ API
- stable element GUID for element lifetime;
- per-element `modiStamp`;
- project `modiStamp`;
- `EditNotificationInterface` changed-GUID notifications after supported element edits;
- `GetCEIPProjectID(projectLocation)` native project identifier signal;
- Add-On Objects for persistent Safe BIM project-owned metadata.

The missing capability is not “how to read the project”. It is a small Safe BIM-native indexing/identity layer plus synchronization policy.

---

# 5. Chosen synchronization model

Do NOT deep-export the whole PLN after every click.

Use a hybrid:

```text
edit event
  -> enqueue dirty GUID(s)
  -> debounce/coalesce
  -> shallow GUID/modiStamp reconciliation
  -> deep-read changed/relevant elements only
  -> refresh local relation/QA neighborhood
  -> create coherent snapshot
  -> background commit/push
```

Notifications accelerate synchronization. Shallow reconciliation provides completeness if notifications are missed.

The notification callback itself must not perform network, Git, deep JSON serialization or long Tapir calls.

---

# 6. Native read-only extensions recommended

## `GetSafeBIMProjectStamp`

Returns at minimum:
- Safe BIM logical project ID;
- native CEIP project ID where available;
- project modification stamp;
- project display name;
- Teamwork flag;
- current Archicad-instance ID.

## `GetSafeBIMElementStateIndex`

Returns intentionally shallow element records:
- GUID;
- type;
- native modification stamp;
- floor/story;
- layer;
- group/hotlink identity where useful;
- renovation status;
- design-option identity where cheap and reliable.

No full geometry should be returned by this command.

## Edit-event queue

Use Archicad 29 `EditNotificationInterface` as a dirty-GUID hint source.

Do not treat it as the sole completeness mechanism until its coverage is live-certified for create/delete/properties/undo/redo/settings-dialog edits and other relevant edit classes.

---

# 7. Project identity

Final identity should be composite rather than path-only.

Recommended:

1. Safe BIM logical project UUID persisted in the PLN using an Add-On Object.
2. `ACAPI::GetCEIPProjectID(projectLocation)` as a native project/file signal.
3. Local registry containing known file locations/fork lineage.
4. Per-process Archicad instance ID.

Save As / copied-PLN semantics remain a live-certification item. A copied PLN may duplicate add-on-owned metadata, therefore duplicate logical IDs must be detected rather than silently accepted.

---

# 8. External snapshot format

Research schemas created:
- `project_context_snapshot_v0_1.schema.json`
- `assistant_recipe_envelope_v0_1.schema.json`

Recommended private repository layout:

```text
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
```

GUID-prefix sharding limits rewrite volume and lets an external assistant fetch only needed data.

---

# 9. Snapshot atomicity

A Git commit is the external publication transaction.

The publisher must:
1. build the complete snapshot in local staging;
2. validate schemas/hashes;
3. confirm project identity did not change during capture;
4. write all files coherently;
5. publish one commit;
6. advance the current manifest only as part of that commit.

The assistant must never combine `manifest.json` from snapshot N with element shards from snapshot N-1.

---

# 10. Canonical state hashes

Each deep element/contract record should have deterministic `state_hash` computed from canonical JSON.

Canonicalization policy must include:
- sorted keys;
- fixed unit convention;
- stable floating-point normalization/tolerance policy;
- removal of volatile UI/time fields;
- inclusion of geometry and semantic fields relevant to Safe BIM operations.

Keep separately:

- native `modiStamp`: cheap change detector;
- Safe BIM `state_hash`: exact external-context execution precondition.

---

# 11. Stale-context protection — mandatory

Every executable assistant result must carry context binding, for example:

```json
{
  "basedOn": {
    "logicalProjectId": "...",
    "snapshotId": "...",
    "projectRootHash": "..."
  },
  "preconditions": [
    {
      "kind": "ELEMENT",
      "id": "<GUID>",
      "expectedHash": "..."
    }
  ]
}
```

Immediately before any mutation Safe BIM rereads local authoritative state.

Any relevant mismatch must produce:

`STALE_CONTEXT`

and physical writes = **0**.

This includes:
- wrong project;
- changed target;
- deleted target;
- changed story/attribute/relation contract;
- unsupported capability;
- stale/forked logical project identity.

This is the mechanism that makes a non-instantaneous GitHub mirror safe enough for code generation.

---

# 12. Publication cadence

Initial policy to benchmark, not hard-code as final truth:

- edit debounce around 2 seconds;
- coalesce continuous edit storms;
- background publication no more frequently than roughly every 10–15 seconds during continuous work;
- immediate/high-priority sync on:
  - explicit `Синхронизировать ChatGPT`;
  - project Save;
  - opening/requesting external AI context;
  - before Safe BIM stage;
  - after Safe BIM stage.

Archicad work must remain independent of GitHub availability.

---

# 13. Multiple Archicad instances

Use session records, not one unqualified “current project”.

Each session should include:
- random per-process instance ID;
- logical project ID;
- current snapshot ID;
- last-active timestamp;
- foreground/active indication when reliably available.

External ChatGPT may default to the latest active session, but Safe BIM execution still requires exact project match.

---

# 14. Privacy and repository audit

GitHub API inspection during this research reported both current repositories as public:

- `dvikt33-ux/safe-bim-layer`;
- `dvikt33-ux/arena-archicad-project`.

Therefore they are **not eligible for real architectural model context**.

Before exporting real project state, create and authorize a dedicated **private** project-state repository.

Suggested logical name:

`dvikt33-ux/safe-bim-project-state`

Requirements:
- private visibility;
- no API keys/tokens/passwords/BIMcloud secrets;
- omit absolute local filesystem paths by default;
- no PLN binary;
- structured context only;
- configurable scope: selection / active story / full project;
- optional excluded layers/types.

Repository privacy is a hard release gate.

---

# 15. External ChatGPT read workflow

For a project-specific Archicad request, the assistant should:

1. read `active.json`;
2. read active project manifest;
3. require `complete=true` and a coherent snapshot;
4. read story map, selection, recent changes and QA summary;
5. locate target GUIDs in compact index;
6. fetch only relevant element/relation/attribute shards;
7. generate code/recipe bound to project ID, snapshot ID, root hash and target preconditions.

It must not infer unseen current geometry solely from conversation memory.

---

# 16. User experience

Safe BIM palette remains compact.

Suggested status line:

- `Контекст ChatGPT: ✓ синхронизирован`
- `Контекст ChatGPT: ● обновляется`
- `Контекст ChatGPT: ⚠ устарел`
- `Контекст ChatGPT: офлайн`

Optional button:

`[Синхронизировать сейчас]`

Normal workflow:

1. user edits model;
2. bridge updates context automatically in background;
3. user asks ChatGPT normally;
4. ChatGPT inspects current private mirror;
5. user receives project-aware code/recipe;
6. code/recipe is pasted/opened in Safe BIM palette;
7. Safe BIM validates freshness and only then offers Preview/Execute.

No PowerShell and no manual model dump required.

---

# 17. One-way V1 vs bidirectional future

## V1 — implement first

`Archicad -> local context -> private GitHub -> external ChatGPT`

This solves the immediate problem and is compatible with ordinary external ChatGPT project-aware code generation.

## Later — optional no-copy delivery

Possible:

`ChatGPT -> assistant-inbox -> Safe BIM palette`

But this must depend on an explicitly write-capable connector/app/MCP. Standard GitHub read integration must not be assumed to provide repository writes in every ChatGPT surface.

Inbox rules:
- append-only recipe IDs;
- never auto-execute;
- local Preview/Execute required;
- replay protection;
- same stale-context preconditions;
- raw Python classified as untrusted code;
- typed Safe Recipe is preferred.

No-copy delivery is an optimization, not a prerequisite for the context bridge.

---

# 18. Relationship to embedded/local AI

The same canonical context cache should serve both paths:

- external ChatGPT reads private GitHub mirror;
- embedded/local AI reads local SQLite directly.

Therefore the BIM-context model is independent of model provider and transport.

This prevents later BIBIM/MCP/local-model integration from forcing another rewrite of project-state semantics.

---

# 19. Relationship to existing dispatcher/handoff

The existing Arena/ChatGPT handoff repository already demonstrates a useful architecture:

`durable GitHub state -> tiny wake/control message -> target agent`

Reuse the pattern/code where practical, but keep channels isolated:

- agent-control repo/branch: control messages only;
- private project-state repo: architectural context only.

Never place private model state into the current public handoff repository.

---

# 20. Live/benchmark certification still required

These are now targeted measurements, not broad research unknowns.

## Edit notification coverage
Test:
- drag/stretch;
- settings-dialog edits;
- property/classification edits;
- create/delete;
- undo/redo;
- story changes;
- relevant attribute changes.

Compare events against index/modiStamp reconciliation.

## Project identity
Test:
- Save;
- Save As;
- copied PLN at another path;
- second simultaneously opened copy;
- Teamwork later if needed.

Record logical ID, CEIP ID and project modification stamp.

## Performance
Measure:
- 1k / 10k / 50k elements;
- cold state-index scan;
- one-element edit refresh;
- 100-element edit refresh;
- changed relations/QA neighborhood refresh;
- local snapshot materialization;
- Git commit/push;
- ChatGPT fixed-path retrieval latency.

## Failure cases
Test:
- GitHub offline;
- push conflict;
- project switch during snapshot;
- two Archicad sessions;
- edit during publication;
- stale recipe after target modification.

---

# 21. Implementation order

## Phase A — local state foundation
1. logical project identity prototype;
2. native project/element stamp commands;
3. shallow state index;
4. SQLite context cache;
5. canonical hashes;
6. change reconciliation.

## Phase B — private external mirror
1. create private state repo;
2. snapshot schema validation;
3. sharded materializer;
4. asynchronous Git worker;
5. sync-state palette indicator.

## Phase C — external ChatGPT workflow
1. fixed-path context read protocol;
2. selection/current-story/full-project scopes;
3. project-aware code generation based on snapshot;
4. include snapshot/precondition envelope with generated recipe.

## Phase D — execution freshness gate
1. parse recipe envelope;
2. local project match;
3. local state-hash checks;
4. `STALE_CONTEXT` fail-closed behavior;
5. integrate with existing Preview/Checkpoint/Sandbox/Safe Runtime.

## Phase E — optional no-copy transport
Only after A–D are stable.

---

# 22. Final verdicts

**PROJECT CONTEXT BRIDGE TECHNICALLY FEASIBLE:** YES

**READY TO IMPLEMENT LOCAL STATE INDEX/CACHE:** YES

**READY TO IMPLEMENT STALE-CONTEXT EXECUTION GATE:** YES

**SAFE TO USE GITHUB AS BIM SOURCE OF TRUTH:** NO

**SAFE TO USE A DEDICATED PRIVATE GITHUB REPOSITORY AS EXTERNAL CONTEXT MIRROR:** YES, prototype after privacy setup

**SAFE TO EXPORT REAL PROJECT STATE TO CURRENT PUBLIC SAFE-BIM/ARENA REPOSITORIES:** NO

**SAFE TO AUTO-EXECUTE EXTERNAL AI CODE:** NO

**REQUIRES AN ALWAYS-LOADED LOCAL LLM:** NO

**CAN SERVE BOTH EXTERNAL CHATGPT AND FUTURE EMBEDDED AI FROM ONE CONTEXT MODEL:** YES

**MORE BROAD RESEARCH REQUIRED BEFORE IMPLEMENTATION:** NO

Only targeted live/benchmark certification is required now.

---

# 23. Final recommendation

Build the bridge now, beginning with the **local read-only state index + SQLite cache + stale-context precondition model**.

Do not begin with GitHub syncing code and do not begin with two-way AI transport. The local state model is the foundation that makes every later transport safe.

Before Phase B touches real architectural data, create a dedicated private project-state repository.

The desired end state is:

> External ChatGPT can inspect the current Archicad project before writing code, while Safe BIM locally proves that the project still matches the context the code was based on before allowing a single physical BIM write.
