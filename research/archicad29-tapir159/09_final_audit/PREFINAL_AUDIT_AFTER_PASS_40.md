# Pre-final audit after project-acceleration pass 40

Scope: consolidate the missing-data, Tapir 1.5.9, AI-resource, development-speed, capability-expansion and project-acceleration research before the final targeted pass set.

No live Archicad writes were performed as part of this research branch.

## 1. Primary objective status

Target objective:

> Make Archicad projects as fast as practical, minimize routine, minimize failures, maximize useful functionality.

Current evidence supports a coherent architecture rather than a collection of ad-hoc commands.

## 2. Highest-confidence architecture

```text
Human / selected elements / schedule / optional parametric frontend
                         |
                         v
            deterministic intent router
                         |
       known recipe? ----+---- no ---> on-demand AI planner
             |                            |
             +----------------------------+
                         |
                         v
            typed/versioned ProjectRecipe
                         |
             Project Profile resolver
                         |
                         v
             deterministic DAG compiler
                         |
             capability/evidence registry
                         |
                         v
                Safe BIM runtime
                         |
         one mutation item per dispatch
                         |
                         v
                   Tapir 1.5.9
                         |
                         v
                  Archicad 29
```

Heavy AI is unloaded before the physical BIM dispatch/reconciliation phase.

## 3. Major speed multipliers confirmed

### A. Reuse settings through Favorites

- create with `favoriteName`;
- capture a manually-correct exemplar with `CreateFavoritesFromElements`;
- explicit geometry overrides settings;
- project profile preflights dependencies.

### B. Reuse assemblies through Hotlink Modules

- `SaveAsModuleFile`;
- `CreateHotlinkNodes`;
- `CreateHotlinkInstances`;
- exact instance readback.

This is likely the strongest multiplier for repeated multi-element building content.

### C. Generate custom single objects through GDL/HSF

- Graphisoft ships `LP_XMLConverter` with Archicad;
- source-controlled HSF/GDL -> GSM;
- Tapir loads/inventories/places library parts;
- Main GUID provides a stable content identity.

### D. Generate documents downstream from verified model state

Tapir 1.5.9 supports sections/interior elevations/dimensions/text/labels/views/layouts/drawings/publisher workflows.

### E. Batch read-only work, never ambiguous writes

- one physical mutation item per dispatch;
- immediately persist returned GUID;
- batch `GetDetailsOfElements` over exact GUIDs;
- request only verifier-required fields;
- defer expensive polygons unless needed.

### F. Cache and invalidate rather than repeatedly scan

- cache stories/resources/catalogs inside project identity;
- element notifications mark element caches dirty;
- project/global state is explicitly revalidated at appropriate gates;
- no background polling.

## 4. Major failure reducers confirmed

- exact target GUID selection instead of geometric search;
- selected-element workflows for human-directed edits;
- `HighlightElements` preview before bulk edits;
- ScriptUI approval/parameter form;
- `GetPointFromUser` only in isolated WAITING_USER state;
- patch-in-place Modify operations rather than unnecessary delete/recreate;
- strict operation-specific readback;
- relation readback for SEO/trims;
- project identity check immediately before writes;
- source/version/schema pinning;
- capability tiers preventing raw new Tapir writes from automatically becoming production features.

## 5. Major functionality expansion found

High-value reachable areas in Tapir 1.5.9 include:

- native walls/columns/beams/slabs/stairs/windows/doors/openings;
- roofs/morphs/meshes/zones;
- objects/lamps/GDL parameters;
- lines/polylines/arcs/circles/hatches/splines/hotspots;
- texts/labels/dimensions;
- Favorites;
- libraries;
- attributes/profiles;
- properties/classifications/keynotes;
- Design Options;
- element groups;
- hotlink modules;
- SEO/trims;
- sections/interior elevations/details/worksheets;
- layouts/views/drawings/publisher;
- relations/connections/bboxes/collisions;
- Teamwork reservation/send/receive;
- Issues/BCF/IFC;
- MEP routing/elements/connections;
- ScriptUI and point input;
- element notifications.

Not all are production-safe yet; this is the reachable surface, not the certified surface.

## 6. Technologies audited outside core Tapir

- official Automation API: useful baseline/fallback;
- official Grasshopper Live Connection: useful geometry/parametric frontend, but direct writes bypass Safe BIM receipts;
- GDL/LP_XMLConverter: high-priority safe expansion path when paired with Tapir placement;
- BIBIM: useful source/UI/local-provider patterns, not safety authority;
- MCP progressive discovery: excellent AI tool-discovery pattern, but should expose certified Safe BIM capabilities only;
- custom Safe BIM C++ add-on: not justified now because Tapir already provides a signed/open ACAPI bridge and custom Developer ID constraints remain.

## 7. Material source-level gaps still open

### Geometry/probe gaps

- arc wall sign/orientation convention for the desired side;
- single-plane roof pivot/positive-side convention;
- Safe BIM Mesh builder must be corrected to the 1.5.9/source-informed Z model;
- Morph verifier must be updated to real origin/axes/body readback;
- 1.5.9 schema must replace the current pinned 1.5.8 schema before new capability certification.

### Reuse/resource gaps

- Favorite dependency portability must be encoded in Project Profile preflight;
- hotlink source-module update/relink lifecycle needs an immutable-version policy or dedicated probe;
- GDL source skeleton/Main-ID generation needs a deterministic workflow;
- placed Object readback should explicitly bind expected library-part identity + parameters.

### Performance gaps

- optimal filtered readback batch size is empirical;
- save checkpoint cost is empirical;
- documentation generation/update cost is empirical;
- local AI cold-start/wake/unload cost is empirical.

## 8. Pre-final risk assessment

### Risk: trying to expose all Tapir commands at once

High. It would expand the safety surface faster than verification capacity.

Mitigation: capability registry + certification tiers + Project Recipe compiler.

### Risk: direct LLM tool execution

High. It mixes planning uncertainty with irreversible model state.

Mitigation: AI only emits typed intent/recipe; deterministic compiler/runtime owns writes.

### Risk: maximizing speed by batching creates

High under transport loss because returned per-item GUID receipts can be lost for an unknown subset.

Mitigation: one mutation item per dispatch; batch readback only.

### Risk: project standards drift

High for Favorites/library parts/attributes across different templates or library sets.

Mitigation: Project Profile hash + preflight + preferably a controlled project template/seed.

## 9. Items selected for final research passes

1. controlled template/seed-project strategy;
2. Favorite portability/dependency rules;
3. stable library-part identity and object verifier implications;
4. immutable hotlink module version strategy;
5. fast-path archetype recipes;
6. documentation dirty-graph strategy;
7. resource/version compatibility contract;
8. measurable performance budget/benchmark plan;
9. implementation ordering by value/risk;
10. final end-to-end audit.

No implementation or live probe should be started from this pre-final document alone; the final pass set will turn these into an implementation priority map.
