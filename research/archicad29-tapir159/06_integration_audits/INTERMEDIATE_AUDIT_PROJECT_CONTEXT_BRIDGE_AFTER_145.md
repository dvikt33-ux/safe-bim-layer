# INTERMEDIATE AUDIT — Project Context Bridge after pass 145

Date: 2026-09-27

## Goal

Audit whether enough information is known to make external ChatGPT project-aware before generating Archicad code.

## Result

The feasibility is established, but a naive “dump the whole PLN to GitHub after every edit” design is rejected.

## What is already strong enough

1. **Project read context exists**
   - project metadata;
   - stories/current story;
   - selection;
   - all-element enumeration;
   - selective element details;
   - global 3D bounds;
   - supported element relations.

2. **Efficient incremental primitives exist in native AC29**
   - project `modiStamp`;
   - element `modiStamp`;
   - `EditNotificationInterface` changed GUID sets.

3. **External ChatGPT already has a practical transport**
   - authorized GitHub content can be retrieved on demand;
   - fixed paths eliminate dependence on GitHub search freshness.

4. **Safe BIM already has the right safety philosophy**
   - project identity check;
   - receipts/readback;
   - no blind retry;
   - exact GUIDs.

The missing part is to bind assistant output to an exact external context snapshot and revalidate that context before mutation.

## Major new blocker discovered: repository privacy

Both repositories inspected during this audit are currently reported by GitHub API as **public**:
- `dvikt33-ux/safe-bim-layer`;
- `dvikt33-ux/arena-archicad-project`.

Therefore **real architectural project state must not be mirrored into either repository**.

A separate private state repository is mandatory before any real project geometry/context export.

Suggested logical name:

`dvikt33-ux/safe-bim-project-state`

The exact name is not important; `visibility=private` is.

## Remaining design questions requiring follow-up passes

- repository layout and sharding;
- snapshot atomicity;
- canonical element hashing;
- stale-context preconditions;
- Save As/fork identity handling;
- multiple Archicad instance handling;
- publication scheduling/debounce;
- offline behavior and conflict policy;
- privacy/redaction policy;
- two-way assistant recipe delivery;
- performance targets and live probes.

## Intermediate verdict

**FEASIBLE: YES**

**SAFE TO EXPORT REAL PROJECT STATE TO EXISTING REPOS: NO**

**SAFE TO IMPLEMENT LOCAL READ-ONLY CACHE/INDEX: YES, after product design review**

**SAFE TO MAKE GITHUB MIRROR AUTHORITATIVE FOR BIM: NO**
