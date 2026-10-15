# Final targeted research passes 41–50

Purpose: close the pre-final source/design gaps that materially affect project speed, routine reduction and failure containment.

No live Archicad writes were performed.

## Pass 41 — start from a controlled template/seed instead of rebuilding project standards every time

Graphisoft AC29 documentation states that a `.tpl` template contains project preferences, placed elements and tool default settings.

Official source:
https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-28.htm

This makes a controlled template the fastest baseline for new projects: layers, attributes, Favorites, libraries, master layouts, views, classifications/properties and defaults can already exist before Safe BIM begins model generation.

Important Tapir limitation: `OpenProject` source currently accepts `.pln`/`.pla`, not `.tpl`. Therefore automated bootstrap should not pretend Tapir can create a new project from TPL.

Practical strategies:

- user starts a new project from the approved TPL, then Safe BIM verifies profile identity; or
- deterministic external bootstrap copies a canonical **seed PLN** to a new project path before Archicad opens it, then Tapir `OpenProject` loads that copy.

Never edit the canonical seed itself.

Sources:
- Graphisoft template help above;
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp

## Pass 42 — Favorite portability is dependency-sensitive, so template/profile preflight is mandatory

Graphisoft AC29 documents:

- Favorites are imported by name and can come from PLN/PLA/TPL or PRF/XML;
- for older versions, importing from a project is recommended over old PRF/XML;
- a Favorite containing a missing GDL object cannot be applied;
- Favorites reference project resources/attributes, so target-project resource differences matter.

Official sources:
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-64.htm
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-62.htm

Conclusion: the Project Profile must check libraries/attributes before checking/applying Favorites. A same-version controlled TPL/seed is the preferred way to reduce portability risk.

## Pass 43 — library-part identity model is strong enough for a Safe BIM catalog

Tapir 1.5.9 `GetAvailableLibraryParts` returns the library part's **Main GUID**, current index, document name, file name and type; it also reports skipped inventory entries.

Graphisoft states the library-part index is not stable over the project lifetime.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/LibraryCommands.cpp
- https://archicadapi.graphisoft.com/documentation/api_libpart

Catalog rule:

`main_guid` is persistent identity; `index` is runtime-only; human names are resolvers/display metadata.

Tapir's object-detail code resolves a placed object's library index back to library-part details (`AddLibPartBasedElementDetails`) before returning object-specific details. This is promising for a strict placed-object verifier, but the exact normalized `libPart` fingerprint should still be captured in one read-only/live fixture before generic production enablement.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCommands.cpp

## Pass 44 — make hotlink modules immutable/versioned rather than relying on hidden source refresh semantics

Tapir states that `CreateHotlinkNodes` finds an existing node by source file path and returns it with `existing:true`; requested name/story settings are then ignored. No dedicated “update this node from changed source contents” command was found in the 1.5.9 command set.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp

Safer reproducible policy:

- content/versioned module filename or directory, e.g. `<semantic-id>/<content-hash>.mod`;
- new module content -> new path -> new node;
- existing instances keep the old node unless an explicit migration/replacement job moves them;
- Project Recipe records expected module content hash and node GUID.

This avoids silent model changes because a file at an old path was replaced in place.

## Pass 45 — compile common project archetypes to parameterized recipes

Architecture proposal.

Common project operations should stop invoking AI once learned. Examples:

- apartment/unit layout shell;
- repeated hotel/office rooms;
- standard commercial grid/bay;
- standard stair/core arrangement;
- standard facade bay;
- standard drawing package.

A recipe exposes only project-specific variables (dimensions, counts, story map, module choice, materials/Favorites). The deterministic compiler expands the recipe to the Safe BIM DAG.

This turns AI from a per-element author into a recipe author/parameter assistant and is expected to have a larger speed effect than optimizing token generation.

## Pass 46 — documentation requires a dirty dependency graph, not full regeneration

Architecture proposal based on the available exact relations/navigator/document APIs.

Track dependencies such as:

`model elements -> zones/relations -> section/elevation sources -> dimensions/labels -> drawings -> layouts -> publisher output`.

A model change marks only affected downstream nodes dirty. At the documentation milestone, update/rebuild only dirty nodes. Associative Archicad elements may update internally, but Safe BIM should still verify the output state required by its own recipe rather than assume every document has refreshed.

This is essential for fast iterative design on large projects.

## Pass 47 — runtime compatibility contract must be explicit before every job

Every compiled job should carry:

- expected Archicad major/build range;
- expected Tapir version (`1.5.9` for this research baseline);
- pinned Tapir schema/source snapshot hash;
- Safe BIM capability-manifest version;
- Project Profile version/hash;
- recipe schema version.

Runtime preflight uses `GetAddOnVersion` plus project/Archicad identity. A mismatch disables write capabilities whose semantics were certified against another version; read-only inspection can remain available where safe.

The user's installed add-on is reported as Tapir 1.5.9. The research baseline is the upstream 1.5.9 tag. Binary-file SHA equivalence has not been independently measured and is not assumed.

## Pass 48 — define an end-to-end performance benchmark, not command microbenchmarks only

Benchmark representative project workflows:

1. cold Safe BIM startup;
2. project/profile preflight;
3. create 10/50/200 independent native elements with one-item dispatch + batched readback;
4. repeated hotlink-module placement;
5. zone generation/update;
6. section/dimension generation;
7. view/layout/drawing generation/update;
8. save checkpoint;
9. publish/export;
10. AI cold start -> plan freeze -> unload.

Metrics:

- wall clock;
- JSON calls;
- Archicad main-thread blocked time where measurable;
- peak/idle RAM;
- peak/idle VRAM for local AI;
- number of user interactions;
- physical writes;
- reconciliation events/unknown outcomes;
- generated documents/verified elements per minute.

Optimization decisions should follow this benchmark.

## Pass 49 — implementation order by value / risk

### Phase A — foundation (highest priority)

1. pin/extract Tapir 1.5.9 schema/source artifact;
2. update offline Arc/Mesh/Morph/Roof contracts;
3. capability/evidence registry;
4. typed ProjectRecipe + deterministic DAG compiler;
5. Project Profile manifest/preflight;
6. filtered multi-GUID readback batching.

### Phase B — fastest practical project gains

7. Favorite capture/use;
8. selected-element + highlight + ScriptUI workflow;
9. hotlink module catalog;
10. standard archetype recipes;
11. incremental QA/cache invalidation.

### Phase C — model-to-document automation

12. sections/interior elevations;
13. dimensions/text/labels/autotext;
14. views/layouts/drawings;
15. publisher pipeline.

### Phase D — advanced geometry/functionality

16. SEO/trims;
17. GDL/HSF parametric object factory;
18. Design Option variant pipeline;
19. stairs/advanced objects;
20. MEP only after dedicated multi-object receipt design.

### Phase E — AI convenience

21. optional AI broker/planner;
22. progressive certified capability discovery;
23. recipe generation/parameter filling;
24. model unloaded before physical execution.

AI is deliberately not Phase A because deterministic automation gives project-speed gains without adding inference latency/resource risk.

## Pass 50 — final end-to-end architecture finding

The fastest robust strategy found is a **compiler/runtime system**, not an autonomous chatbot inside Archicad.

```text
CONTROLLED TEMPLATE / SEED
        +
PROJECT PROFILE
        +
FAVORITES / NATIVE ATTRIBUTES
        +
HOTLINK MODULE CATALOG
        +
OPTIONAL GDL PARAMETRIC LIBRARY
        |
        v
PARAMETERIZED PROJECT RECIPE
        |
        +-- optional AI only for ambiguous design/planning
        v
DETERMINISTIC RECIPE COMPILER
        v
SAFE BIM DAG + EXACT RECEIPTS
        v
TAPIR 1.5.9 / ARCHICAD 29
        v
INCREMENTAL QA + DOCUMENTATION + PUBLISH
```

The system becomes faster over time because every manually-approved configuration can be captured as a Favorite, module, library object or reusable recipe instead of being solved again.

# Result of final targeted passes

The final source/design passes did not uncover a better production write backend than Tapir 1.5.9 mediated by Safe BIM. They did uncover a stronger productivity stack around it: controlled project templates, capture-and-reuse, immutable modules, parametric GDL library generation, filtered readback batching, incremental docs/QA and deterministic recipe compilation.

Remaining uncertainties are now mostly empirical/live certification items, not broad architectural unknowns.
