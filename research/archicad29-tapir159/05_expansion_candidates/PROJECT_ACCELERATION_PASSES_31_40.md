# Project acceleration research — passes 31–40

Third acceleration round. Focus: eliminate user routine, reduce wrong-target failures, and turn user-approved work into reusable automation.

No live Archicad writes were performed.

## Pass 31 — selection-first exact-target workflows

Tapir provides `GetSelectedElements`. For many editing tasks the safest and fastest target resolver is simply: user selects elements in Archicad -> Safe BIM receives exact GUIDs -> preview -> modify.

This avoids:

- natural-language ambiguity;
- expensive model-wide search;
- geometry matching/adoption;
- accidental edits to look-alike elements.

Use this path for commands such as “change these walls”, “apply this classification to the selected rooms”, or “make these objects a reusable module”.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp

## Pass 32 — highlight before risky bulk operations

Tapir exposes `HighlightElements`, including clearing previous highlights with an empty element list.

A low-friction approval flow is:

1. deterministic runtime resolves exact GUID target set;
2. `HighlightElements` previews targets in Archicad;
3. ScriptUI shows operation summary;
4. user approves;
5. exact GUID mutation begins.

Highlight is presentation only and is not ownership evidence.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp

## Pass 33 — “teach by example” through Favorites

Tapir 1.5.9 exposes `CreateFavoritesFromElements`, in addition to listing/applying Favorites.

This enables a very efficient workflow:

- user configures one element manually exactly as desired;
- selects it;
- system records/creates a named Favorite from the exact element;
- project profile stores the semantic role -> Favorite name mapping;
- future elements use `favoriteName` at creation plus explicit geometry.

This is faster and less error-prone than manually encoding every Archicad setting into prompts or code.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/FavoritesCommands.cpp

## Pass 34 — “teach by example” through Modules

For multi-element assemblies the equivalent workflow is:

- user builds/selects a correct exemplar;
- `SaveAsModuleFile` writes a `.mod`;
- `CreateHotlinkNodes` registers the module;
- future projects use `CreateHotlinkInstances` with exact transform.

This is suitable for apartments, cores, bathrooms, hotel rooms, facade bays and other repeated BIM assemblies.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp

## Pass 35 — patch existing verified elements instead of recreate/delete where possible

Tapir has exact-GUID Modify commands for major element families. Source implementations patch only supplied fields for the supported types.

Safe BIM should prefer:

`read exact GUID -> before fingerprint -> ModifyX exact GUID -> reread exact GUID -> after fingerprint`

over delete+recreate when identity can be preserved.

Benefits:

- preserves downstream references/associations where Archicad supports it;
- reduces GUID churn;
- reduces document relinking;
- simplifies ownership/reconciliation.

Exceptions must remain explicit: operations that source code implements as replacement need old->new identity receipts.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp

## Pass 36 — parametric GDL factory for custom single objects

Graphisoft ships `LP_XMLConverter.exe` with Archicad and documents HSF/XML <-> GSM compilation. Tapir can load libraries, inventory Main GUIDs and place Objects.

This creates a no-custom-APX route for project-specific parametric object families. Full audit is in `PARAMETRIC_GDL_LIBRARY_FACTORY.md`.

Sources:
- https://gdl.graphisoft.com/tips-and-tricks/how-to-use-the-lp_xmlconverter-tool/
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/LibraryCommands.cpp

## Pass 37 — resource resolver must use stable identity, not transient indexes

Graphisoft documents that a library-part `index` is not constant throughout a project. Tapir 1.5.9 `GetAvailableLibraryParts` returns the Main GUID, index, names and type.

The same design principle should apply to other resources: resolve human names to canonical GUID/type at preflight, then keep exact IDs in the compiled recipe wherever the API permits.

Sources:
- https://archicadapi.graphisoft.com/documentation/api_libpart
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/LibraryCommands.cpp

## Pass 38 — two-stage project production avoids regenerating documents during design churn

Architecture proposal:

**Model stage**
- primary geometry;
- dependencies;
- zones/semantics;
- core QA.

**Documentation stage**
- sections/elevations;
- dimensions/labels;
- views/layouts/drawings;
- publisher/export.

During rapid design iteration, only dirty model DAG branches are rebuilt. Documentation is regenerated/updated at explicit milestones, not after every wall move. This reduces both Archicad compute and unnecessary API traffic.

Safety rule is unchanged: each actual mutation still has its normal receipt and verification.

## Pass 39 — QA gates should be incremental and dependency-aware

Do not run a full-project collision/zone/document audit after every small edit.

Use dirty sets derived from the recipe DAG and element notifications:

- changed element -> invalidate its exact details;
- invalidate relations/dependents;
- run bbox/collision only against impacted groups;
- update zones only when boundary-affecting geometry changed;
- regenerate affected views/drawings only at documentation phase.

Notification delivery is a hint, not a durable transaction log; exact reads remain authoritative.

## Pass 40 — ask the user once, not ten times

Interactive automation should batch missing decisions into one ScriptUI form whenever possible:

- target story;
- dimensional options;
- favorite/module variant;
- placement mode;
- documentation level;
- approval of highlighted target set.

Use `GetPointFromUser` only for data genuinely easiest to specify graphically. It blocks the Archicad JSON queue while waiting for a click, so repeated point prompts are expensive and disruptive.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ScriptUICommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ApplicationCommands.cpp

# Audit after passes 31–40

## Biggest new productivity insight

The system should support **capture-and-reuse**, not only code-driven automation:

- single-element settings -> Favorite;
- multi-element assembly -> Hotlink Module;
- single custom parametric object -> GDL/HSF library part;
- whole workflow -> versioned Project Recipe DAG.

This means the architect can teach Safe BIM by building a correct example once instead of describing every Archicad parameter forever.

## Failure reduction gains

- selection-first target resolution reduces wrong-target errors;
- highlight+approval catches target-set mistakes before writes;
- patch-in-place preserves exact identity;
- stable resource GUID resolution prevents name/index drift;
- delayed docs avoid cascading document churn;
- incremental QA avoids expensive unnecessary global recalculation;
- batched human decisions reduce blocking JSON interactions.

## Remaining source/research gaps

1. Exact readback contract for placed Objects to bind current library Main GUID/revision to an element.
2. Favorite portability rules across templates/languages/library versions.
3. Module update/relink behavior for existing instances after source `.mod` changes.
4. Dirty dependency rules for documentation regeneration need command-by-command mapping.
5. GDL factory needs a safe new-object source skeleton workflow and one compilation benchmark.
6. Selection/highlight UX needs an operational timeout/cancel policy but no new BIM semantics.

These gaps are narrower than the original capability uncertainty and can be handled in focused implementation/probe work.
