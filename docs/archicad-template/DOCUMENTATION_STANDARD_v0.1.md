# Archicad 29 Documentation / View / Publisher Standard v0.1

Status: draft
Depends on:
- GRAPHICS_STANDARD_v0.1
- PROJECT_BASELINE_v0.1
- DATA_SCHEMA_v0.1

## 1. Rule: publish only saved Views / Layouts

A deliverable must originate from a Saved View or Layout.

A Saved View is treated as an immutable display recipe containing:
- Layer Combination
- Scale
- Partial Structure Display
- Pen Set
- Model View Options Combination
- Graphic Override Combination
- Renovation Filter
- Design Option Combination
- Floor Plan Cut Plane
- Dimension standard
- zoom/rotation where relevant

No formal issue from an ad-hoc viewpoint.

## 2. Model View Options

Core combinations:

MVO_01_WORK_FULL
- maximum useful model symbols/details for editing
- doors/windows/stairs/railings at working detail
- suitable for AR model editing

MVO_10_AR_DOCUMENT
- architectural documentation output
- stable symbols and detail level
- avoid unnecessary 3D-library decoration

MVO_20_COORD
- coordination-oriented representation
- suppress decorative/detail clutter
- retain openings, stairs, structural/MEP coordination-critical geometry

MVO_30_SITE
- site/general-plan representation
- simplified building symbols where appropriate

MVO_40_PRESENTATION
- presentation-specific representation
- never used for normative/QA decisions

Rule:
MVO controls representation/detail, not semantic status.
Fire/QA coloring belongs to Graphic Overrides.

## 3. Graphic Override combinations

GO_00_NONE

GO_10_QA_DATA
Priority order:
1. QA_ERROR
2. QA_WARNING
3. DATA_PLACEHOLDER
4. DATA_UNVERIFIED
5. REFERENCE_SUBDUE

GO_11_QA_NORM
Priority order:
1. NORM_ERROR
2. NORM_WARNING
3. NORM_BLOCKED_SOURCE
4. NORM_NOT_CHECKED
5. NORM_PASS_SUBTLE

GO_20_PB_FIRE_COMPARTMENTS
- fire-compartment boundaries and IDs
- fire-resistance related checks

GO_21_PB_EVACUATION
- evacuation-route elements
- exits/openings/stairs on evacuation paths

GO_30_MEP_SYSTEMS
- system-based engineering visualization
- uses system/discipline properties, not layer colors as data source

GO_40_AUTOMATION_STATE
- MANAGED
- USER_MANAGED
- REFERENCE
- LOCKED
- QUARANTINE

GO_90_PRESENTATION
- optional visual output only

Rules:
- property values never encode RGB/color
- Graphic Override rule names are stable identifiers
- rule order is part of the standard
- same-name GO imports with different content can create suffixed duplicates; release process must detect this

## 4. Core View Map

00_QA
  QA_MODEL
  QA_DATA
  QA_NORM
  QA_AUTOMATION

01_AR
  AR_200_PLAN_GENERAL
  AR_100_PLAN_WORK
  AR_100_PLAN_PRINT
  AR_050_PLAN_WORKING
  AR_050_SECTION
  AR_020_SECTION_DETAIL
  AR_010_DETAIL
  AR_005_DETAIL

02_KR
  KR_100_COORD
  KR_050_COORD
  KR_020_DETAIL

03_PB
  PB_100_FIRE
  PB_100_EVAC

04_MEP
  VK_100_COORD
  OV_100_COORD
  EOM_100_COORD
  SS_100_COORD
  MEP_100_ALL_COORD

05_GP
  GP_500_PLAN
  GP_200_PLAN

06_PRESENTATION
  3D_WORK
  3D_COORD
  3D_PRESENTATION

Only views relevant to loaded disciplines should exist in a project/object pack.

## 5. Partial Structure Display usage

AR_PRINT:
- Entire Model

KR_COORD:
- Core Only / Load-Bearing Core as project requires

MEP_COORD:
- Without Finishes or Core Only where that improves routing clarity

QA_JUNCTION:
- test all relevant PSD modes

Do not use a different Composite just to obtain a different PSD display.

## 6. Core schedules

QA_01_ELEMENTS_NO_STABLE_TYPE
- managed candidates missing SBIM.Core.StableTypeID

QA_02_DATA_STATUS
- DataStatus != VERIFIED/PROJECT_DEFINED where verification is required

QA_03_NORM_ERRORS
- SBIM.Norm.Status in ERROR/WARNING/BLOCKED_SOURCE

QA_04_AUTOMATION_STATE
- elements grouped by AutomationState

QA_05_MATERIALS
- Building Materials with stable IDs / source status / collision flag

AR_01_ZONE_REGISTER
- zone number/name/function/area/occupancy/fire/accessibility fields

AR_02_DOOR_REGISTER
- door ID/type/dimensions/fire/accessibility fields

AR_03_WINDOW_REGISTER
- window ID/type/dimensions

AR_04_WALL_TYPES
- StableTypeID/composite/profile/core material

MAT_01_BUILDING_MATERIALS
- Building Material name/ID/description/manufacturer where applicable

MAT_02_COMPOSITES
- composite names and usage

MEP schedules are discipline packs, not necessarily Core.

## 7. Layout Book

Masters:
A4_P
A3_L
A3_P
A2_L
A2_P
A1_L
A1_P
A0_L

Do not create every exotic sheet size in Core.
Add nonstandard/extended sheets only in project packs.

Master contents:
- sheet border
- title block
- Project Info Autotext
- Layout ID/name
- revision/transmittal fields where required
- company information
- optional project logo field

No manually duplicated project metadata on each Layout.

## 8. Layout hierarchy

00_GENERAL
01_AR
02_KR
03_PB
04_VK
05_OV
06_EOM
07_SS
08_GP
09_TX
90_QA_INTERNAL

Only active disciplines are instantiated in final project pack.

Layout ID structure:
<SECTION>-<NN>

Examples:
AR-01
AR-02
PB-01
VK-01

Revision is not baked into permanent Layout ID unless the issue procedure explicitly requires it.

## 9. Drawing placement

Rules:
- Drawings reference Saved Views
- Drawing scale is normally 100% of source View
- do not use layout magnification as a substitute for correct View scale
- title reads Drawing/View metadata through Autotext where possible
- drawing pen set inherits from source view unless an explicit Drawing-level override is part of the standard

## 10. Publisher Sets

PUB_01_PDF_ISSUE
Source: Layout Book subsets
Method: Save PDF
Purpose: official issue set

PUB_02_PDF_INTERNAL
Source: QA/internal layouts/views
Purpose: review only

PUB_10_DWG_ISSUE
Source: required Views/Layouts
Translator: DWG_OUT_SPDS

PUB_11_DWG_COMPAT
Translator: DWG_OUT_COMPAT

PUB_20_IFC_COORD
Translator: IFC_COORD

PUB_21_IFC_ISSUE
Translator: IFC_ISSUE

PUB_30_BIMX
Optional project pack

Use publisher shortcuts/clones rather than disconnected copies where automatic synchronization is desired.

## 11. Publisher naming

Preferred source identity:
- Layout ID / View ID
- source item name

Do not depend on manual renaming of every output on every issue.

If external contractual file naming is more complex than Archicad Publisher can guarantee:
- publish deterministic base names
- apply packaging/renaming in a controlled external release script
- keep mapping log

## 12. PDF policy

Official PDF issue:
- vector output
- fonts verified/embedded by output test
- correct sheet size
- no unexpected PDF layer leakage if prohibited by issue rules
- image resolution controlled
- Project Info metadata reviewed for confidentiality

Run A3 and A1 physical print checks before v1.0.

## 13. DWG policy

DWG issue must use named translators:
DWG_OUT_SPDS
DWG_OUT_COMPAT

Tests:
- fonts
- line types
- fills
- pen/color conversion
- units
- model/paper space strategy
- XREF behavior if used

No default/unnamed translator in released workflow.

## 14. IFC policy

IFC_COORD:
- coordination geometry
- appropriate collision-material participation
- project georeferencing through approved Survey Point policy
- classification/type mapping checked
- property mapping includes Core + active IDS/project properties

IFC_ISSUE:
- contract/deliverable-specific settings
- locked preset/version
- exported schema recorded

## 15. Issue gate

Before Publisher issue:
- no QA ERROR unless waiver exists
- unresolved BLOCKED_SOURCE reported
- all Layout drawings updated
- correct View recipes
- fonts available
- no missing textures/library parts affecting deliverable
- Survey Point/coordinates verified for IFC/DWG
- Publisher log retained
- output count matches expected layout count

Failure:
SBIM.Project.CoordinationStatus stays REVIEW
official_issue = blocked

## 16. Next implementation artifacts

- actual MVO XML exports
- Graphic Override XML exports
- schedule scheme exports/test project
- Master Layout implementation
- Publisher sets in TPL
- DWG translator XML
- IFC translator presets
