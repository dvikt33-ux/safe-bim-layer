# Archicad 29 Template — Exchange / Master Layout Checkpoint

Date: 2026-10-06
Branch: `feature/working-archicad-mvp`
Pre-checkpoint HEAD: `e4c76fa04039218f58bfe98a18ccf5fb092082e4`

## Repository-side status

The template preparation is now beyond specification-only state. A fail-closed builder exists for safe live materialization, while the remaining unsupported Archicad preset types are isolated as explicit seed contracts.

## Executable builder stages

Read-only / preflight:
- validate
- font-preflight
- inspect
- plan
- plan-materials
- plan-data-schema
- plan-navigator
- plan-master-layouts
- plan-autotext

Fail-closed writes:
- apply-core
- apply-surfaces
- apply-ready-materials
- apply-data-schema
- apply-navigator-shell
- apply-master-layout-shell

## Master Layout / SPDS

Verified source model:
- GOST R 21.101-2026 Form 3
- titleblock 185 x 55 mm
- exact A4-A0 master sizes registered
- Layout/Master Layout size units confirmed as millimeters in Graphisoft API
- exact Master Layout shell creation is implemented, live execution pending
- titleblock line/text generation remains blocked until one sacrificial Master Layout coordinate test passes

## AutoText

- official Archicad AutoText keys mapped to Form 3 fields
- titleblock registry contains built-in keys for building/layout/sheet count/scale/etc.
- custom read-only overlay command `GetAutoTextsV1` implemented
- builder action `plan-autotext` implemented
- overlay rebuild + live verification still pending
- dynamic fields must never be faked as static text

## Exchange

DWG contracts:
- DWG_IN_REFERENCE
- DWG_OUT_SPDS
- DWG_OUT_COMPAT

IFC contracts:
- IFC_COORD
- IFC_ISSUE
- IFC_REFERENCE_IMPORT

Rules:
- no silent unknown DWG unit assumption
- IFC schema/MVD is delivery-dependent
- IFC4 / Reference View is only a coordination default candidate, not a universal requirement
- external DWG/IFC remains reference-isolated by default
- Publisher translator names are CI-cross-checked against exchange registries

## Remaining Archicad seed/API gaps

Manual seed under Tapir 1.5.8:
- MVO presets
- Graphic Override rules/combinations
- Dimension Style presets
- Publisher Set creation
- DWG translator creation/editing
- IFC translator creation/editing
- Work Environment profile

Final Save As new TPL path remains outside the current JSON command surface.

## Live sequence

On a clean Archicad 29 candidate project:

1. font-preflight
2. validate
3. inspect
4. plan
5. apply-core
6. apply-surfaces
7. plan-materials
8. apply-ready-materials
9. plan-data-schema
10. apply-data-schema
11. create/verify manual MVO/GO/Dimension seed presets
12. plan-navigator
13. apply-navigator-shell
14. plan-master-layouts
15. apply-master-layout-shell
16. rebuild/load overlay containing GetAutoTextsV1
17. plan-autotext
18. sacrificial Master Layout line/text/AutoText test
19. only then generate full Form 3 geometry
20. seed/test DWG and IFC translators
21. Model Dump + PDF/DWG/IFC regression
22. save first candidate TPL manually if Save As remains unavailable

This checkpoint does not claim live Archicad execution or a released .tpl.
