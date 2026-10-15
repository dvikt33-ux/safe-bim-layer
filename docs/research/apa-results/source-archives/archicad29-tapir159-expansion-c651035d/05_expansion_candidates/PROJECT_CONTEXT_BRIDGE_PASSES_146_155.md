# PROJECT CONTEXT BRIDGE — passes 146–155

Date: 2026-09-27

Follow-up after the pass-145 intermediate audit.

## Pass 146 — transport topology

Separate the BIM state mirror from product code and agent-control repositories.

Recommended V1 topology:

```text
PRIVATE REPO: safe-bim-project-state

branch: model-state          # only local Safe BIM bridge writes
branch: assistant-inbox      # assistant/proposal side if write-capable transport is available
```

If the ChatGPT integration is read-only, only `model-state` is required; code/recipe continues to be copied manually from chat.

Do not put project state into public `safe-bim-layer` or public `arena-archicad-project`.

## Pass 147 — atomic snapshots

Git commit is the publication transaction.

Local bridge builds a coherent snapshot in a staging directory, validates it, then commits/pushes the whole set. ChatGPT reads one branch HEAD, so it never needs to combine files from different publication generations.

Every snapshot receives a monotonic `snapshot_id` independent of the Git commit SHA.

## Pass 148 — sharding strategy

Do not make one huge model JSON.

Recommended structure:

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
projects/<project_id>/current/elements/shards/00.json ... ff.json
projects/<project_id>/current/relations/shards/00.json ... ff.json
```

GUID-prefix sharding bounds the amount of JSON rewritten when a small number of elements changes and lets the assistant fetch only relevant shards.

## Pass 149 — canonical fingerprints

Every deep element record gets a deterministic `state_hash` derived from canonical JSON:
- sorted object keys;
- fixed unit conventions;
- stable numeric normalization/tolerance policy;
- omit volatile timestamps/UI fields;
- include geometry/semantic fields required by Safe BIM operations.

Keep native `modiStamp` and Safe BIM `state_hash` separately:
- `modiStamp` = cheap native change detector;
- `state_hash` = exact external-context precondition.

## Pass 150 — stale-context gate

Every assistant-generated executable recipe must declare:

```json
{
  "based_on": {
    "project_id": "...",
    "snapshot_id": 184,
    "project_root_hash": "..."
  },
  "preconditions": [
    {"guid": "...", "state_hash": "..."}
  ]
}
```

Immediately before physical mutation Safe BIM rereads local authoritative state.

Reject with zero writes if:
- project ID differs;
- target disappeared;
- target state hash differs;
- required attribute/story contract changed;
- recipe capability is not production-enabled.

This makes a stale GitHub mirror inconvenient but not dangerous.

## Pass 151 — multiple Archicad sessions

A single `active_project.json` is insufficient if more than one Archicad process is open.

Use:

```json
{
  "sessions": [
    {
      "instance_id": "random-per-process-token",
      "project_id": "...",
      "snapshot_id": 184,
      "last_active_at": "...",
      "is_foreground": true
    }
  ]
}
```

The external assistant may default to the newest foreground session but recipe execution still requires exact `project_id` match.

## Pass 152 — publication schedule

Network/Git operations must never run in Archicad notification callbacks.

Recommended pipeline:

```text
Archicad callback
 -> enqueue GUID/stamp only
 -> debounce/coalesce
 -> read/update local cache
 -> background Git worker
 -> commit/push
```

Suggested initial policy (to benchmark, not yet production constants):
- event debounce: ~2 s;
- coalesce all events during active edit;
- no more than one background push per ~10–15 s during continuous manual work;
- immediate high-priority publication on explicit `Sync ChatGPT`, project Save, before/after Safe BIM stage, and when external-AI/code panel requests a fresh context.

Archicad remains usable if GitHub is slow/offline.

## Pass 153 — offline/conflict policy

Offline:
- local SQLite/cache continues normally;
- palette shows `Контекст ChatGPT: офлайн/устарел`;
- no project operation depends on GitHub availability;
- assistant-generated recipe must still satisfy local snapshot preconditions when later imported.

Conflict:
- `model-state` branch has exactly one authorized writer per active project session;
- unexpected remote advance => STOP publication and surface diagnostic, never force-push silently;
- assistant proposals are append-only IDs on a separate branch/path to avoid state conflicts.

## Pass 154 — privacy/minimum disclosure

Project geometry is architectural IP. Requirements:
- private repository only;
- never upload API keys, access tokens, local credentials, BIMcloud secrets;
- omit absolute local filesystem paths by default;
- prefer display project name + stable project ID;
- configurable context scopes (`selection`, `current story`, `full project`);
- allow excluded layers/types if needed;
- publish only structured model state, not the PLN binary.

Important current finding: existing Safe BIM and Arena repos are public despite `safe-bim-layer` description saying “Private safety layer”. Repository visibility, not description, is authoritative.

## Pass 155 — bidirectional assistant path

V1 external ChatGPT only requires **state -> assistant**. This alone solves the user's immediate need: ChatGPT can inspect current project before producing code.

Optional later two-way protocol:

```text
model-state branch (local writer)
  projects/.../current/*

assistant-inbox branch (assistant writer where supported)
  projects/.../inbox/<recipe_id>.json
```

Rules for inbox:
- append-only recipe IDs;
- never auto-execute;
- local palette shows proposal and requires Preview/Execute;
- bind recipe to project/snapshot/hash preconditions;
- replay protection (`recipe_id`, consumed status locally);
- raw Python is classified `UNTRUSTED_CODE`; preferred transport is typed Safe Recipe JSON.

OpenAI's documented standard GitHub connection is read-oriented. Therefore two-way GitHub write must be treated as an optional connector capability, not a universal assumption.

Source: https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt
