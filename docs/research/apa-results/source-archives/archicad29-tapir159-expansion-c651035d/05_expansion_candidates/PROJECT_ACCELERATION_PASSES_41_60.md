# Project acceleration research — passes 41–60

Fourth acceleration round. Goal: make Archicad project production materially faster while minimizing manual routine, wrong-target failures, transport ambiguity and repeated AI reasoning.

Baseline: Archicad 29 + Tapir Additional JSON Commands 1.5.9. No live Archicad writes were performed during this research round.

## Pass 41 — 1.5.9 is not a minor schema bump

The upstream delta from 1.5.8 to 1.5.9 contains 258 commits. The changed surface includes element creation/modification, project commands, libraries, favorites, solid operations, navigator/document commands, common schemas and Grasshopper wrappers.

Practical consequence: Safe BIM should treat `tapir-1.5.9` as a separately certified backend contract, not as a drop-in patch over the pinned 1.5.8 schema.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/compare/1.5.8...1.5.9

## Pass 42 — use the exact Tapir tag as executable documentation

Tapir 1.5.9 tag resolves to commit `d0dbb11b13942e014661e1402b07958b70cd9dba`.

The upstream C++ contains live-confirmed failure notes that are more precise than the JSON schema alone (examples: stale per-item defaults, Window/Door current database constraints, Text/Label `withdel=true`, story-level anchoring behavior).

Research policy: every production capability should bind to `(Tapir version, upstream commit, schema snapshot, source contract)` rather than only a command name.

Sources:
https://github.com/ENZYME-APD/tapir-archicad-automation/tree/1.5.9
https://github.com/ENZYME-APD/tapir-archicad-automation/releases/tag/1.5.9

## Pass 43 — per-item Favorite application is the fastest settings path

`CreateElementsCommandBase` in 1.5.9 supports `favoriteName` per create item. It snapshots global tool defaults, applies the requested favorite, reloads defaults for every item, and restores the original defaults afterward.

This solves two productivity problems simultaneously:

- project standards can be stored in Archicad Favorites instead of duplicated as giant API payloads;
- automation does not leave the user's manual tool defaults altered after generated work.

Safe BIM should compile semantic roles such as `external_wall`, `door_900`, `room_label`, `stair_standard` to Favorite names in a Project Profile.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp

## Pass 44 — never optimize write throughput with multi-item Create arrays

Tapir processes create arrays item by item inside one undoable command and only returns the per-item results in the final response. A connection loss after dispatch can therefore leave an unknown subset applied.

Production policy remains:

`one mutating physical item -> persist returned GUID -> exact-GUID verification`

Throughput must be recovered with cached preflight, parallel offline planning and batched reads, not by batching risky writes.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp

## Pass 45 — notifications are excellent cache invalidation, not a transaction log

`SetElementNotificationClient` can notify on new, changed, deleted, reserved and released elements. The callback HTTP client uses a 100 ms timeout and swallows transport exceptions.

Therefore notifications are ideal for:

- invalidating cached details;
- marking dependent recipe nodes dirty;
- triggering cheap targeted rereads;
- updating UI state.

They are not durable enough to prove ownership, completion or absence of a write.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NotificationCommands.cpp

## Pass 46 — future Teamwork support can be non-modal and deterministic

Tapir `ReserveElements` calls the Archicad Teamwork API with dialogs disabled and returns explicit conflicts containing element GUID, user ID and username. `ReleaseElements`, `TeamworkSend` and `TeamworkReceive` are also exposed.

This is suitable for a future Safe BIM Teamwork adapter:

1. resolve exact target GUIDs;
2. reserve with dialogs disabled;
3. fail closed on any conflict;
4. execute verified mutations;
5. reread;
6. release;
7. send only at an explicit phase checkpoint.

This must remain separate from the current non-Teamwork P2P concept.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/TeamworkCommands.cpp

## Pass 47 — manual lock and Teamwork reservation must not be conflated

Tapir has `LockElements`/`UnlockElements` and separately Teamwork reserve/release commands. Upstream explicitly describes Lock as manual lock, not Teamwork.

Safe BIM capability metadata should therefore distinguish:

- `manual_element_lock`;
- `teamwork_reservation`;
- local runtime execution lock.

They solve different concurrency problems and cannot substitute for one another.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp

## Pass 48 — Design Options are a high-value variant engine in AC29

Tapir 1.5.9 exposes native AC29 Design Option operations including listing options/sets/combinations, creating options/combinations, reading element membership, changing active options and moving exact elements into an option or back to the main model.

Fast project workflow:

`base recipe -> variant parameter sets -> separate Design Options -> user comparison -> selected variant becomes downstream documentation target`

This avoids duplicate PLN files for many alternative studies. Design Options are organizational state, not a transaction rollback mechanism.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/DesignOptionCommands.cpp

## Pass 49 — Solid Element Operations have unusually strong reconciliation potential

1.5.9 exposes create/remove/read of Solid Element links. Readback returns exact target/operator relationships plus operation and flags.

This is a strong Safe BIM operation class because a receipt can be represented as:

`target GUID + operator GUID + operation + flags`

and reconciled without geometry search.

Use cases include terrain cuts, structural penetrations and repeated boolean construction relationships.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/SolidElementOperationCommands.cpp

## Pass 50 — Roof/Shell trimming is also relationship-readable

Tapir 1.5.9 adds `TrimElements`, `GetElementTrims` and `RemoveElementTrims`. This is preferable to destructive geometry replacement for roof-wall and shell trimming where Archicad's native relationship can express the design intent.

Integration requirement: persist exact participating GUIDs and trim type, then read the relationship back. Do not infer successful trimming from visual geometry alone.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/SolidElementOperationCommands.cpp

## Pass 51 — story mutation must be a rare project-global recipe node

`SetStories` can grow/shrink the story structure, rename stories and change levels. Upstream source explicitly notes that deleting a story deletes its elements, and live AC29 observations were needed to handle the active-story anchor when setting levels.

Therefore normal project generation should usually consume an already-defined Project Profile story structure rather than casually modifying stories during geometry creation.

If story changes are required, treat them as a high-risk pre-model migration phase with full before/after story snapshot and explicit user approval.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp

## Pass 52 — Hotlink Modules can collapse hundreds of writes into one assembly placement

1.5.9 supports module export/registration/placement/change operations: `SaveAsModuleFile`, `CreateHotlinkNodes`, `CreateHotlinkInstances`, `ChangeHotlinkInstances`, `GetHotlinks`.

For repeated rooms, apartment types, facade bays, stairs/cores, bathroom pods and furniture layouts, this can be the largest raw speed multiplier in the system.

Important split:

- node registration can detect an existing node pointing at the same source file;
- every placed instance is still a mutation and needs its own exact receipt/readback.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp

## Pass 53 — library state belongs in Project Profile preflight

Tapir can read libraries, add local libraries, replace the set of local libraries, reload libraries and add files to the embedded library.

A fast reliable project boot sequence should resolve required libraries once and refuse model generation if mandatory resources are missing. Do not discover missing library parts halfway through a large recipe.

`AddLibraries` is preferable to repeated forced reloads because upstream returns success without changing state when every requested path is already loaded.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/LibraryCommands.cpp

## Pass 54 — create project-specific parametric assets instead of modeling repeated special geometry

The previously researched GDL/HSF factory route should be considered part of the fast path:

`generate/compile library part once -> load library -> place Objects many times -> edit via parameters`

This is often cheaper and more stable than rebuilding a custom assembly from many Morphs for every occurrence.

Detailed research:
`PARAMETRIC_GDL_LIBRARY_FACTORY.md`

## Pass 55 — Autotext removes repeated annotation synchronization

1.5.9 adds `GetAutoTextKeys` and `GetAutoTextName`; Text/Label creation/modification can embed Archicad autotext keys.

Documentation automation should prefer dynamic autotext for project/element properties instead of copying static strings. This reduces manual annotation updates after model changes.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp

## Pass 56 — room program should compile directly into Zones

`CreateZones` supports automatic reference-point geometry or explicit polygons with arcs/holes. `UpdateZones`, `GetZoneBoundaries`, relations and room images provide downstream QA.

High-throughput workflow:

`room schedule -> validated zone recipe -> zone creation -> one targeted UpdateZones phase -> batched boundary/area QA -> labels/autotext`

This removes repeated room naming, numbering, stamp placement and manual area checking.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp

## Pass 57 — associative dimensions should be generated from verified semantic geometry

Tapir provides associative linear dimensions, section dimensions, wall-thickness dimensions and readback of dimension witness data.

Do not draw dimensions as independent graphics. Compile them from verified element GUIDs and semantic witness presets after model geometry stabilizes. This makes documentation regeneration much cheaper after design changes.

Sources:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Examples/get_dimension_data.py

## Pass 58 — existing Objects/Lamps can be patched instead of replaced

1.5.9 supports create and modify paths for library-part based Objects/Lamps, including coordinates, dimensions, angle and many display/material settings.

For generated furniture/equipment, preserve GUID identity where possible:

`exact GUID -> ModifyObject/ModifyLamp -> reread`

rather than delete/recreate, especially when labels, classifications or external references already depend on the element.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp

## Pass 59 — eliminate handwritten integration boilerplate with schema generation

The public Tapir Archicad MCP project dynamically generates typed tools/models from Tapir + official Archicad schemas, and supports progressive command discovery rather than maintaining a manually written wrapper for every command.

Safe BIM should reuse the architectural idea but keep its own stricter execution policy:

`schema snapshot -> generated DTO/validator/read command stubs -> hand-written safety contract only where semantics matter`

This can dramatically reduce implementation time for read-only capabilities and mechanical request validation.

Source:
https://github.com/SzamosiMate/tapir-archicad-MCP

## Pass 60 — AI should see capabilities progressively, not 190+ tools at once

The MCP project exposes a small deterministic discovery interface (`list commands -> get exact schema -> call`) instead of flooding the model context with all command schemas. It also removed vector-search dependencies such as PyTorch/FAISS/sentence-transformers.

For Safe BIM this suggests an efficient AI adapter:

1. AI receives only project intent + capability summaries;
2. it asks deterministic registry for candidate operations;
3. exact schema/contract is loaded only for selected operations;
4. AI emits a typed Project Recipe;
5. deterministic runtime executes it.

Benefits: smaller prompts, lower latency, less local RAM, fewer wrong tool calls and easier model swapping/unloading.

Source:
https://github.com/SzamosiMate/tapir-archicad-MCP

# Audit after passes 41–60

## Highest-value additions confirmed in this round

1. **Favorite-first Project Profiles** for settings-heavy elements.
2. **Hotlink Module catalog** for repeated multi-element assemblies.
3. **Native Design Options** for alternative design workflows.
4. **Relationship-native SEO/Trim operations** with exact GUID readback.
5. **Notification-driven dirty sets** for incremental QA/cache invalidation.
6. **Teamwork reservation adapter** with no-dialog conflict reporting if/when Teamwork is used.
7. **Autotext + associative documentation** to eliminate model/document synchronization routine.
8. **Schema-generated integration layer** to reduce development boilerplate.
9. **Progressive AI tool discovery** to reduce context/memory/tool-selection overhead.
10. **Project-global operations isolated into explicit recipe phases** instead of hidden side effects.

## Reliability rules reinforced by source review

- Do not batch physical writes merely to reduce HTTP calls.
- Treat notifications as hints only.
- Keep manual locks, Teamwork reservations and runtime process locks separate.
- Story deletion/change is high-risk project-global state.
- Favor native relationships (SEO/trim/design-option membership/group/hotlink) over geometry imitation when Archicad already models the relationship.
- Prefer exact-GUID patch-in-place over delete/recreate where the API supports it.
- Compile project standards from Favorites/libraries/attributes before geometry starts.
- Interactive commands must never run as background automation.

## Remaining gaps after pass 60

1. Exact hotlink-instance readback/reconciliation contract after placement and change.
2. Object readback fields needed to bind an element to stable library Main GUID/version.
3. Favorite portability across templates, languages and library revisions.
4. Exact duplicate/idempotency semantics for SEO and Trim relationship creation.
5. Documentation dependency graph: which model changes invalidate which views/drawings/dimensions.
6. Safe Project Profile manifest schema and version migration rules.
7. Generated schema layer needs a policy separating purely mechanical DTO generation from hand-certified mutation semantics.
8. AI progressive-discovery adapter requires latency/memory benchmark on the user's Legion.
9. Teamwork is source-supported but not relevant to the current non-Teamwork P2P workflow unless intentionally enabled.
10. Final production architecture still needs a unified prefinal audit combining runtime safety, capability expansion, AI resource use and project-production throughput.
