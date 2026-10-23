# PROJECT CONTEXT BRIDGE — passes 131–145

Date: 2026-09-27
Scope: how external ChatGPT can know the current Archicad project state before generating code, without putting AI in the BIM write path.

## Objective

The external assistant must be able to answer from the current project state, while Safe BIM remains fail-closed if that state becomes stale before execution.

The bridge is a **context mirror**, not a write authority.

---

## Pass 131 — threat model

Failure classes:
- assistant sees an old project;
- assistant sees the wrong PLN;
- element changed after snapshot;
- target GUID deleted/replaced;
- attributes/stories changed while element GUID stayed stable;
- two Archicad instances publish concurrently;
- network/GitHub unavailable;
- publication blocks Archicad UI;
- sensitive project geometry accidentally becomes public;
- assistant output is executed automatically without local validation.

Primary safety conclusion: stale external context must never be able to cause a write. Every generated recipe must carry project/snapshot/precondition identifiers that Safe BIM rechecks immediately before dispatch.

## Pass 132 — GitHub as current transport

OpenAI's documented GitHub connection reads authorized repository content on demand and does not maintain a synchronized GitHub index. Therefore the bridge should use fixed known paths rather than depend on code-search indexing for the latest model state.

Source: https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt

GitHub is suitable as a durable **external assistant mirror**, not as the local runtime source of truth.

## Pass 133 — existing handoff architecture

Existing repository `dvikt33-ux/arena-archicad-project`, branch `agent-handoff`, already proves the pattern:

`local dispatcher -> durable GitHub state -> tiny wake message -> ordinary ChatGPT`

The project-state bridge can reuse the architectural pattern but should NOT reuse the same signal files: project context and agent control must stay isolated.

## Pass 134 — project identity/read-only metadata

Tapir 1.5.9 provides `GetProjectInfo` and returns project name/path/teamwork state. Archicad C++ API exposes `API_ProjectInfo.modiStamp` and Archicad 29 adds `ACAPI::GetCEIPProjectID(projectLocation)` described as a unique project identifier useful for usage logging.

Sources:
- https://archicadapi.graphisoft.com/documentation/api_projectinfo
- https://graphisoft.github.io/archicad-api-devkit/group___a_p_i_infrastructure.html

Do not use path alone as project identity.

## Pass 135 — stories and active floor

Tapir 1.5.9 `GetStories` exposes first/last/active story and story records. Current context should always include a story map with actual elevations and current active story.

This prevents generated code from inferring vertical position from display names.

## Pass 136 — selection as high-value context

Tapir `GetSelectedElements` is based on Archicad selection. Selection should be first-class external context because most user requests are naturally scoped by what is currently selected.

Snapshot should include selected GUIDs plus compact summaries; detailed records are fetched from the state store by GUID.

## Pass 137 — complete element index

A safe external context layer needs a compact index of the entire model, not full deep JSON on every edit.

Recommended index record:

`guid, type, floor, layer, bbox, modification_stamp, detail_hash, hotlink, renovation/design-option flags where available`

Archicad `API_Elem_Head.guid` is stable for the life of the element and `modiStamp` exists specifically to detect modification.

Source: https://archicadapi.graphisoft.com/documentation/api_elem_head

Tapir 1.5.9 does not currently expose `modiStamp`; no `modiStamp` use was found in upstream Tapir source. A small Safe BIM native read-only command is therefore justified.

## Pass 138 — selective deep details

Tapir 1.5.9 `GetDetailsOfElements` accepts field selection. Expensive fields (notably polygon geometry) should not be serialized globally when a compact context is enough.

Rule:
- headers/index often;
- deep details only for selected, dirty, neighboring, or assistant-relevant elements.

## Pass 139 — spatial context

Tapir 1.5.9 `Get3DBoundingBoxes` calculates 3D bounds for exact GUIDs. BBox belongs in the compact element index because it lets the assistant understand approximate placement and build local neighborhoods without loading every geometry field.

## Pass 140 — semantic relations

Tapir 1.5.9 `GetRelationsOfElements` can expose element relationships. The mirror should maintain relation shards for context-sensitive tasks (wall/zone, host/opening, curtain-wall and other supported relation families) rather than asking the LLM to infer relations from coordinates.

## Pass 141 — notification path audit

Tapir `SetElementNotificationClient` is convenient but its modification-notification setup attaches observers to existing elements. Historical Graphisoft developer reports show that attaching an observer to very large element sets can be expensive and can block Archicad for significant time.

Conclusion: do not make project-wide Tapir element observers the mandatory V1 synchronization mechanism.

Prefer an Archicad-29-native event/index hybrid.

## Pass 142 — project and element stamps

Two cheap stamps exist at C++ level:
- `API_ProjectInfo.modiStamp`: coarse project dirty/version signal;
- `API_Elem_Head.modiStamp`: per-element changed signal.

These are ideal for incremental reconciliation.

Recommended native command:

`GetSafeBIMStateIndex`

returns at least:
- project modification stamp;
- project identity signals;
- all element GUID/type/modiStamp/floor/layer headers;
- optionally hotlink/group/renovation state.

No geometry should be returned by this command.

## Pass 143 — Archicad 29 EditNotificationInterface

Archicad 29 introduces `ACAPI::EditNotificationInterface`. `ElementsEdited` receives a `GS::HashSet<API_Guid>` of changed item GUIDs after element editing plus transformation parameters.

Source: https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_edit_notification_interface.html

This is much more attractive than attaching observers to every element, but documented wording is “after element editings”; it must not be assumed to cover every create/delete/property/attribute/project-setting path.

Architecture consequence: event queue accelerates updates, while periodic/index reconciliation provides completeness.

## Pass 144 — project identity persistence

Archicad Add-On Objects can store arbitrary add-on-owned bytes inside the project database and are Teamwork-safe; Graphisoft explicitly recommends Add-On Objects over legacy ModulData for custom project data.

Source: https://graphisoft.github.io/archicad-api-devkit/group___add_on_object.html

Candidate identity stack:
1. `CEIPProjectID` as native project/file signal;
2. Safe BIM logical project UUID stored as one unique Add-On Object;
3. local registry records canonical file location/fork history.

Important: Save As/copy semantics must be live-tested. A stored logical UUID may be duplicated with a copied PLN, so duplicate-ID detection is mandatory.

## Pass 145 — first architecture audit

### Confirmed
- GitHub is viable for external ChatGPT read context.
- local Archicad/SQLite must remain authoritative.
- GUID + `modiStamp` provides an efficient incremental model index.
- Archicad 29 has direct edited-GUID notifications.
- selection, story map, bounding boxes, deep details and relations are all available from Tapir/native API paths.
- fixed-path manifest is preferable to search/index dependence.

### Not yet proven
- EditNotificationInterface coverage for all mutation classes;
- `API_ProjectInfo.modiStamp` coverage granularity;
- CEIPProjectID behavior across Save As/copy;
- performance of full header/modiStamp scans at 10k–100k elements;
- acceptable Git publication cadence;
- external assistant two-way writes in every ChatGPT product surface.

### Mandatory safety invariant

`assistant context snapshot != current local state` must result in `STALE_CONTEXT` and **zero BIM writes**.
