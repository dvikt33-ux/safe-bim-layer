# Archicad 29 Template — Intermediate Checkpoint

Date: 2026-10-06
Branch: `feature/working-archicad-mvp`
Pre-checkpoint HEAD: `a42e1d7633bd3cb17fc1cc7b40d5791570f90a57`

This checkpoint records the current intermediate state of the Archicad 29 RU/SBIM template preparation.

## Completed specification blocks

- Graphics / fonts standard
- Font manifest
- Materials / Building Materials / Surfaces standard
- Machine-readable attribute registry
- Layer-intersection policy
- Junction regression matrix
- SBIM semantic/data schema
- Machine-readable property schema
- Project baseline: units, coordinates, stories, views
- Documentation / MVO / Graphic Override / Publisher standard
- Compact layer standard and machine-readable layer registry
- Source-driven Composite family strategy
- Machine-readable Composite family registry
- Favorite / StableTypeID contract
- Favorite transfer policy
- Favorite blueprints
- Global Library / custom library / migration policy
- Template build roadmap

## Current architecture decisions

- Core TPL stays lean and universal.
- Object packs remain separated: IZHS / MKD / TRC.
- Discipline packs remain separated by module.
- No arbitrary dimensions or material properties are promoted without verified source/project basis.
- Building Material is atomic material identity; assembly thickness belongs to Composite/Profile/Favorite.
- Stable names and StableTypeID are part of the automation API contract.
- GPT creates common production elements from verified Favorites where possible.
- Native model stays near Project Origin; external coordinates use Survey Point.
- External IFC/DWG/XREF/reference geometry is isolated from native priority cleanup by default.
- Global Library is the baseline for new Archicad 29 projects.
- Production release remains blocked until Archicad implementation and regression tests pass.

## Current files under docs/archicad-template

22 specification/registry files existed immediately before this checkpoint.

## Next build phase

1. Create clean Archicad 29 candidate project.
2. Install/verify fonts.
3. Materialize attributes in dependency order.
4. Create actual layers and combinations.
5. Create Project Info / classifications / properties.
6. Create MVO / Graphic Overrides / Views / Schedules.
7. Create Master Layouts and Publisher sets.
8. Configure DWG / IFC translators.
9. Materialize first verified IZHS test-pack Favorites and assemblies.
10. Run junction, Model Dump, PDF, DWG, IFC and clean-machine tests.

This is an intermediate recovery point, not a released template.
