# PREFINAL AUDIT — Project Context Bridge after pass 155

Date: 2026-09-27

## Executive conclusion

The preferred architecture is now stable:

```text
ARCHICAD 29
  -> native lightweight change/index bridge
  -> local authoritative SQLite/context cache
  -> asynchronous context publisher
  -> PRIVATE GitHub state mirror
  -> external ChatGPT reads fixed-path current snapshot
```

GitHub is not in the BIM write path.

## Why this is preferable to direct full-model upload

- normal Archicad work does not wait for network;
- only changed context is serialized;
- ChatGPT can retrieve current state without the user pasting geometry manually;
- snapshot is durable/versioned;
- stale assistant code is rejected locally;
- embedded/local AI can bypass GitHub and consume the same local cache directly.

## Strongest new technical simplification

Archicad 29 already provides exactly the native primitives needed for low-cost incremental state:

1. `API_ProjectInfo.modiStamp` — project-level modification stamp.
2. `API_Elem_Head.modiStamp` — per-element modification stamp.
3. `ACAPI::EditNotificationInterface::ElementsEdited(changedItemGuids, ...)` — changed GUID set after element editings.
4. stable element GUIDs.

This means Safe BIM does **not** need to deep-read the entire model after every edit.

## Required native read-only bridge extensions

Recommended minimum commands/services:

### GetSafeBIMProjectStamp
Returns:
- Safe BIM logical project ID;
- CEIP project ID where available;
- project `modiStamp`;
- project display name/teamwork flag;
- active Archicad instance/session token.

### GetSafeBIMElementStateIndex
Returns compact records only:
- GUID;
- element type;
- `modiStamp`;
- story/floor;
- layer;
- hotlink/group identifiers where useful;
- renovation status;
- optional design-option identity when available cheaply.

### Edit notification event queue
Use Archicad 29 EditNotificationInterface for immediate dirty GUID hints. It accelerates cache updates but is not accepted as the sole completeness mechanism.

## Completeness rule

Before publishing an externally usable snapshot:

1. consume dirty event queue;
2. compare compact state index against local cache;
3. detect new/deleted/modified GUIDs;
4. deep-read only changed records;
5. update affected relations/QA neighborhood;
6. compute root hash;
7. commit coherent snapshot.

Thus missed notifications are corrected by reconciliation.

## Project identity audit

Useful sources exist but Save As/fork semantics are not fully proven.

- `ACAPI::GetCEIPProjectID(location)` is a native unique project identifier for usage logging.
- Add-On Objects can persist a Safe BIM logical UUID in the PLN and are preferred to legacy ModulData.

Final design should store both and detect duplicates/forks. It must not silently assume that a copied PLN is the same logical working branch forever.

## External ChatGPT contract

When user asks for Archicad code/recipe, assistant should first read:

1. active session/project pointer;
2. current manifest;
3. selection;
4. recent changes + QA summary;
5. only the element/relationship shards relevant to the requested operation.

Assistant must mention or encode the snapshot it used.

## Remaining live/benchmark unknowns

These no longer block architecture design but must be measured before release:

- `EditNotificationInterface` coverage by edit class (geometry, settings-dialog edit, properties, create/delete, undo/redo);
- how `project.modiStamp` changes for element/attribute/story/property operations;
- full state-index scan latency at representative model sizes;
- CEIPProjectID and Add-On Object behavior across Save As/copy;
- Git commit/push latency/repo growth;
- practical context shard size for ChatGPT connector;
- behavior with two Archicad instances modifying the same logical project.

## Privacy gate

This is a hard blocker before real model context export:

**create/authorize a PRIVATE repository dedicated to project state.**

Neither current public repo may receive real project geometry.

## Prefinal verdict

ARCHITECTURE READY: **YES**

READY TO IMPLEMENT LOCAL INDEX/CACHE PROTOTYPE: **YES**

READY TO EXPORT REAL MODEL STATE TO CURRENT REPOS: **NO**

READY FOR EXTERNAL CHATGPT READ CONTEXT AFTER PRIVATE REPO SETUP: **YES, prototype**

READY FOR AUTOMATIC REMOTE CODE EXECUTION: **NO; intentionally prohibited**
