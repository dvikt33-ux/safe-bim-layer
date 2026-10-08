# Canonical project goal and story convention (2026-10-08)

Status: ACTIVE, applies to every subsequent research and development chat for Safe BIM Layer.
Target runtime: Archicad 29. Archicad 30 adaptation only after the AC29 working solution is complete.

## Non-negotiable end goal

**Fully create and deliver an architectural project**, not just complete a model or send a preliminary model to structural engineering. There are two equally valid starting modes:

- New project: brief -> study -> generate geometry -> specialists/engineering -> coordinate -> documentation -> release.
- Existing project: inspect one already-open PLN -> identify remaining work -> extend/repair -> verify -> coordinate -> publish.

H0 architectural feasibility and H1 structural handoff are milestone gates, **not stopping points**. H2 structural feedback and H3 final project documentation and checks must remain on the roadmap.

**Primary business KPI:** human elapsed time from accepted brief to complete, verified, final project release, including engineer feedback cycles. Sub-metrics: time to first model, first structural handoff, time to corrections, model/document update latency, user editing minutes.

## Intensive prebuild before fast modeling

At project initialization, permit extensive research without arbitrary time budget:
- verify task/brief, project type, site/region/jurisdiction;
- compile current applicable normative rules;
- research structural, wall, roof, façade, floor, window, MEP, firestop, wet-room and other applicable assemblies;
- identify/verify existing project examples and manufacturer libraries;
- build a project-local small library pack from the large global source registry;
- choose tested native Archicad Favorites/Composites/Profiles/Objects, solver recipes and available expert engines;
- precompute known architectural constraints and acceptance tests;
- record decisions, source provenance and unresolved specialist tasks.
Stop initial prebuild only when critical coverage obligations are satisfied or explicitly blocked, with no made-up proof. Re-run only impacted research if project requirements change.

**Do not** inflate live PLN, runtime RAM or model context with the entire global source catalog. Reuse `details/v2.12` as ONE source, not enough alone. Project library only includes relevant legally usable, version-compatible, evidence-gated assets.

## Ground floor / first storey convention

- Architectural and published first above-ground storey = **«1 этаж»**.
- Its level in the normal project baseline = **±0,000 m**, which is an elevation, NOT an architectural story number.
- Do not label this storey «0 этаж».
- **Never hardcode Tapir floorIndex=0 or =1** for this purpose.
- Obtain real story map from the sole currently open AC29 project with GetStories / native StorySettings: `API_StoryInfo` (`firstStory`, `lastStory`, `skipNullFloor`) + `API_StoryType` (`index`, `floorId`, `level`, `uName`).
- `skipNullFloor` can cause displayed/indexed stories to start with 1 rather than 0. The same actual first architectural floor can be represented by a native 0 or 1 depending on settings. The human label and elevation must be authoritative for design, while native index is a resolved transport field.
- For new projects: explicitly create/rename first floor `1 этаж` at `0.0 m`, then subsequent floors by approved elevations, basements separately. Never insert fictitious "zero storey".
- For existing projects: NEVER renumber silently; map the existing story names/levels, ask about conflicts instead.
- Read-back validates exact native story identity and elevation; if no unique match return `NEEDS_STORY_RESOLUTION`.

Native contract:
https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___story_info.html
https://graphisoft.github.io/archicad-api-devkit/struct_a_p_i___story_type.html

## Engineering

Structural analysis is a part of the full project cycle, not a replacement for the architect. Native SAM/SAF feeds an approved receiver. LIRA-FEM (formerly LIRA-SAPR) 2026 has COM Python scripting/input/result capabilities, user extensions and batch/LAN calculations. **Installed version, license, specific API methods, Russian-code support, source identities, engineer signoff and return flow must be tested.**

## Reality and research status

Checkpoints and vendor feature claims are not production readiness. Research documents and registry changes do not imply installation, working geometry or integration. No live PLN writes unless explicitly approved for the designated test project.

Priority is maximum progress per design hour, not minimum research duration, tool count or independently completed components.
