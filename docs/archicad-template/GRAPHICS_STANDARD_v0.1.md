# Archicad 29 RU/SPDS Graphics Standard v0.1

Status: draft-for-template-build
Target: Archicad 29 / Windows / RU-SPDS workflow
Branch policy: working branch only; do not treat as released template until round-trip tests pass.

## 1. Fonts

Primary font family:
- PT Astra Sans Regular
- PT Astra Sans Italic
- PT Astra Sans Bold
- PT Astra Sans Bold Italic

Fallback Unicode:
- Noto Sans Regular
- Noto Sans Italic
- Noto Sans Bold
- Noto Sans Bold Italic

Optional drawing-style font:
- OpenGost Type B Regular

Rules:
- PT Astra Sans is the default for dimensions, labels, zone stamps, titles and schedules.
- OpenGost Type B is optional and must never be required for project readability.
- Arial is the DWG compatibility fallback.
- No random downloaded GOST fonts may enter the template.
- Fonts must be tracked by family/version/license in a separate manifest.

## 2. Text heights

Paper text heights:
- 2.5 mm: dimensions, ordinary notes, schedule body
- 3.5 mm: room/zone primary text, secondary headings
- 5.0 mm: grids, marks, image titles, section/detail identifiers
- 7.0 mm: major headings
- 10.0 mm: exceptional sheet-level headings only

Do not create arbitrary heights unless an explicit output standard requires them.

## 3. Pen philosophy

Pen number is a semantic contract, not a color.

Canonical print widths:
- 0.20 mm
- 0.25 mm
- 0.35 mm
- 0.50 mm
- 0.70 mm
- 1.00 mm
- 1.40 mm

Recommended default main contour s:
- 1:200 / 1:100 general drawings: 0.50 mm
- 1:50 developed plans/sections: 0.70 mm where stronger hierarchy is needed
- 1:20 / 1:10 details: 0.70-1.00 mm selectively

## 4. Core pen-number registry

01  LINE_MAIN_050
02  LINE_MAIN_070
03  LINE_HEAVY_100
04  LINE_XHEAVY_140
05  LINE_THIN_020
06  LINE_THIN_025
07  LINE_MEDIUM_035
08  LINE_HIDDEN_025
09  LINE_AXIS_025
10  LINE_SECTION_MARK_070

11  TEXT_MAIN_020
12  TEXT_SECONDARY_020
13  DIMENSION_020
14  GRID_TEXT_020
15  MARKER_TEXT_020
16  LEADER_020
17  HATCH_020
18  DETAIL_OUTLINE_035
19  OVERHEAD_020
20  BELOW_020

21  OPENING_SYMBOL_020
22  STAIR_SYMBOL_020
23  RAILING_SYMBOL_020
24  ZONE_BOUNDARY_020
25  ROOM_STAMP_020
26  FURNITURE_020
27  EQUIPMENT_020
28  SITE_THIN_020
29  SITE_MAIN_035
30  PROPERTY_BOUNDARY_050

31-39 reserved architecture/core
40-49 structure
50-59 fire safety / evacuation
60-69 water and sewer
70-79 heating / ventilation / air conditioning
80-89 electrical
90-99 low current / communications
100-109 technology
110-119 general plan / landscaping
120-139 references / hotlinks / XREF
140-159 demolition / existing / renovation auxiliaries
160-179 temporary/documentation
180-199 fills/background/support
200-219 QA / validation statuses
220-239 analysis / temporary visualisation
240-255 reserved; do not assign without registry update

## 5. Pen sets

01_WORK_COLOR
- same pen indices
- discipline-based screen colors
- true line weights retained
- QA pens visually strong

10_SPDS_PRINT_SMALL
- A4-A2
- mostly black
- minimum printed technical line: 0.20 mm
- main contour normally 0.50 mm

11_SPDS_PRINT_LARGE
- A1-A0
- mostly black
- main contour may be 0.70 mm
- secondary hierarchy adjusted without changing semantic pen indices

20_QA_COLOR
- geometry subdued
- QA error/warning/status pens emphasized

Rule: a Favorite stores semantic pen indices. Output appearance changes only by Pen Set.

## 6. Line types

LT_01_CONTINUOUS
- native solid

LT_02_HIDDEN
- simple dashed
- paper-scale
- target pattern approximately 4 mm dash / 1.5 mm gap

LT_03_AXIS
- simple dash-dot
- paper-scale
- target pattern approximately 10-15 mm dash / 3 mm gap / point / 3 mm gap

LT_04_SECTION_OPEN
- use section/marker tool logic where possible; avoid hand-built symbol line types

LT_05_BREAK_SHORT
- drafting break line

LT_06_BREAK_LONG
- thin break representation

LT_07_FOLD
- thin dash-double-dot

LT_08_OVERHEAD
- simple dashed; use for overhead model representation only where Archicad element display cannot represent it semantically

Rules:
- Prefer simple vector dash patterns.
- Avoid custom symbol line types when a simple dashed line can do the job.
- Symbol line types must pass DWG round-trip before release.
- Annotation line types should normally be scale-independent (paper size).
- Model-dependent line types are allowed only when physical model spacing is semantically meaningful.

## 7. Fill architecture

Three categories must stay distinct:
- CUT
- COVER
- DRAFTING

Core cut/drafting fills:
FILL_00_EMPTY
FILL_01_SOLID
FILL_10_GOST_GENERIC_45
FILL_11_GOST_METAL
FILL_12_GOST_NONMETAL
FILL_13_GOST_WOOD
FILL_14_GOST_STONE
FILL_15_GOST_MASONRY_CERAMIC
FILL_16_GOST_CONCRETE
FILL_17_GOST_GLASS
FILL_18_GOST_LIQUID
FILL_19_GOST_SOIL
FILL_20_INSULATION_CONVENTIONAL
FILL_21_BACKFILL
FILL_22_MESH
FILL_30_EXISTING
FILL_31_DEMOLITION
FILL_32_NEW
FILL_90_QA_ERROR
FILL_91_QA_WARNING

Rules:
- Building Materials own their Cut Fill.
- Surface appearance owns Cover Fill/texture.
- Drafting fills are not substitutes for Building Material logic.
- Image fills are forbidden for cut representation.
- Conventional material hatches should use paper-stable patterns when graphic legibility is the goal.
- Physical module patterns (tile, panel, brick module when used as actual module) may use model-scaled fills.
- Additional material symbols not covered by GOST must have a legend/note in the drawing set.

## 8. Building Material contract

Building Material is an API-facing identity.

Naming:
BM_<SYSTEM>_<MATERIAL>_<QUALIFIER>

Examples:
BM_STR_CONCRETE_RC
BM_MASONRY_CERAMIC_BLOCK
BM_MASONRY_BRICK
BM_INSULATION_MINERAL_WOOL
BM_INSULATION_XPS
BM_FINISH_GYPSUM_PLASTER
BM_FINISH_GYPSUM_BOARD

Do not encode thickness in Building Material name.
Thickness belongs to Composite/Profile/Favorite unless material identity itself changes.

Each Building Material must define:
- stable name
- stable internal ID/GUID where possible
- Cut Fill
- foreground/background pens
- intersection priority
- Surface
- physical properties where useful
- classification/properties

## 9. DWG constraints

Maintain three translators:
DWG_IN_REFERENCE
DWG_OUT_SPDS
DWG_OUT_COMPAT

DWG_OUT_COMPAT:
- map PT Astra Sans to Arial when receiver does not install project fonts
- maintain explicit pen/color conversion table
- maintain line-type conversion dictionary
- no untested symbol line types
- units explicitly controlled
- do not rely on RGB nearest-match for authoritative round-trip tests

## 10. QA release gates

Before GRAPHICS_STANDARD v1.0:
1. A3 PDF print at 100%.
2. A1 PDF print at 100%.
3. 1:100 plan readability.
4. 1:50 plan/section readability.
5. 1:20 and 1:10 detail readability.
6. DWG export/import round trip.
7. Font substitution test on a Windows machine without PT Astra Sans.
8. Line-type dash pattern test after DWG export.
9. Fill scale test at 1:100 / 1:50 / 1:20.
10. Black-and-white laser print test.
11. Model Dump confirms stable attribute names.
12. Favorites reference only registered pens/lines/fills/materials.

## 11. Decisions intentionally deferred

- exact RGB values of 01_WORK_COLOR
- final pattern geometry of material hatches
- final pen adjustments for A0/A1 plotting after physical print tests
- future migration to GOST R 2.303-2026 / GOST R 2.304-2026 before their mandatory 2027 transition
