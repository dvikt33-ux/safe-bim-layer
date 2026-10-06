# Archicad 29 Template — PRE-LIVE Checkpoint

Date: 2026-10-06
Branch: `feature/working-archicad-mvp`
Validated HEAD before checkpoint: `1d6207397a11ec847d48c6796888cf28719194c9`

## Status

Repository-side preparation for the first live Archicad 29 candidate-project execution is complete enough to proceed.

Latest CI:
- workflow: Validate Archicad template specs
- run: 37519655846
- result: SUCCESS
- head: 1d6207397a11ec847d48c6796888cf28719194c9

## Validated registry counts

- Layers: 40
- Layer Combinations: 14
- Semantic Pens: 30
- Candidate Line Types: 4
- Surfaces: 18
- Fill roles: 14
- Building Materials: 27
- SBIM Semantic Classification Items: 12
- SBIM Properties: 54
- View blueprints: 18
- Master Layout blueprints: 8
- Layout subsets: 11
- Publisher blueprints: 6

CI reports:
- errors: 0
- warnings: 0

## Executable commands prepared

Offline / preflight:
- validate
- font-preflight
- inspect
- plan
- plan-materials
- plan-data-schema
- plan-navigator

Fail-closed write stages:
- apply-core
- apply-surfaces
- apply-ready-materials
- apply-data-schema

## Explicitly blocked / deferred

- specialized GOST material-fill geometry until visual-source verification and Archicad calibration;
- final Composite assemblies until exact product/system/project dimensions are resolved;
- released Favorites until verified type elements exist;
- MVO preset creation/editing;
- Graphic Override rule/combination creation/editing;
- Dimension Style preset creation/editing;
- Publisher Set creation;
- DWG/IFC translator preset creation/editing;
- final Master Layout frame/titleblock graphics;
- Save As new TPL path;
- Work Environment profile creation.

## Live sequence

On a clean Archicad 29 candidate project:

1. font-preflight
2. validate
3. inspect
4. plan
5. apply-core
6. inspect
7. apply-surfaces
8. plan-materials
9. apply-ready-materials
10. plan-data-schema
11. apply-data-schema
12. plan-navigator
13. inspect/read-back
14. Model Dump validation

No production geometry should be created by these template setup stages.

This checkpoint does NOT claim that live Archicad execution or a .tpl file already exists.
