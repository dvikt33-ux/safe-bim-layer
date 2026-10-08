# Checkpoint 29: Russian junction norms and BIM validation
Date: 2026-10-08. Target: Archicad 29. Research only; no PLN mutation.

## Norm edition gates
- СП 50.13330.2024 supersedes СП 50.13330.2012 as of 2024-06-16. Official: https://protect.gost.ru/sp/details/5081dae9-9ee9-455f-80e8-d093d495361c
- СП 230.1325800.2015 (amendments 1,2): thermal nonuniformity and tabulated junction parameters; match applicability before using tables. https://protect.gost.ru/sp/details/e8f68a1e-2928-41be-bf89-21330a32f8b5
- СП 17.13330.2017, amendments 1–5: current roofing provisions. https://protect.gost.ru/sp/details/844352c5-dda6-4006-acd8-b6875d1ed6a8
- СП 2.13130.2020, amendments 1,2: fire resistance; amendment 2 effective 2026-01-01. https://protect.gost.ru/sp/details/90783c81-7eaa-4b90-b774-55ad27e6dfa1

## Window-to-wall
ГОСТ 30971-2012, current. Three/four functional layers: exterior weather protection with outward vapour diffusion, central thermal/acoustic, interior vapour control, and optional fourth layer. Annex A specifies material evidence. Check geometry of gap, location of frame, layer descriptions and test/product values. Missing layer modelling is NOT_VERIFIED rather than FAIL.
https://protect.gost.ru/gost/details/09b731bf-531e-428b-8ef9-556ed2d1c110

## Roof-to-parapet, only where SP17 section 5.1 applies
- 5.1.17 bitumen rolled/mastic system: inclined fillet sides 50–100 mm; 2025 amendment 5 modified text.
- 5.1.18 additional membrane and insulation at upstands.
- 5.1.20 waterproofing membrane vertical rise >=300 mm.
- 5.1.22 parapet/fire wall/deformation wall <=600 mm high: bring waterproofing over upper face; 2025 addition requires protecting it with metal coping or coping slabs.
- 5.1.23 coping protection extends at least 60 mm beyond side faces, slopes at least 3% roofward.
- 5.1.25 drain axis at least 600 mm from parapet / protrusions; conditional roof system and drainage arrangement.
Verify semantic roof family *before* running any numeric checks. Do not generalize to all roof technologies.
https://meganorm.ru/mega_doc/norm_update_29032025/normy/0/sp_17_13330_2017_svod_pravil_krovli_aktualizirovannaya.html

## Wall-to-slab
Detect thermal envelope interfaces, continuity of insulation, overlapping geometry, slab edge thermal bridge, fire boundaries and penetrations. Use СП 50.13330.2024, СП 230.1325800.2015, СП 2.13130.2020 and relevant structural/SP facade family standards. Fire and load capacity require engineering and/or validated system tests; do not infer from materials alone.
Relevant СП 63.13330.2018, СП 293.1325800.2017.
https://protect.gost.ru/sp/details/8b67e228-0c9f-4a62-b562-964b3a58c667

## Deformation joints
Joint geometry alone cannot establish required width: structural movements, foundation settlement and potential seismic demand require specialist models (СП 22.13330.2016, СП 63.13330.2018). Check architectural continuity and absence of unintended rigid bridging; inspect waterproofing, firestop and equipment/pipe crossings. Do not invent a universal gap dimension.
https://protect.gost.ru/sp/details/71e96332-a446-4a15-87a0-2db895479f61

## Validation pipeline
AC29 Model Dump → CSE junction/assembly signature → edition-aware normative rule with applicability predicate → geometrical check or SP230 table lookup or dedicated engineering/test evidence → requirement-level verdict → documentation signature/invalidation.

Outcomes: NOT_APPLICABLE, PASS_GEOMETRY, PASS_DOCUMENTED, PASS_ENGINEERING, FAIL, NOT_VERIFIED, NEEDS_SPECIALIST. PASS_GEOMETRY is never whole-junction APPROVED.

## Later tests
WINDOW_JUNCTION_01, ROOF_PARAPET_01, WALL_SLAB_01, MOVEMENT_JOINT_01.
Negative cases: missing represented layer (NOT_VERIFIED); swapped roof family (different applicability); changed CSE wall (invalidate table match); geometry changes invalidating accepted detail signature.

Status: current norms and source clauses researched; NO local Archicad execution, numerical analysis or project compliance certification.
