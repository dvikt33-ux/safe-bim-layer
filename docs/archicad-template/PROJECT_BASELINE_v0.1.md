# Archicad 29 Project Baseline v0.1

Status: draft-for-template-build
Purpose: deterministic project environment for RU/SPDS + SBIM automation.

## 1. Unit contract

Archicad UI / modeling:
- model length working unit: millimeter
- layout unit: millimeter
- working display precision: 0.1 mm where available
- angles: decimal degrees
- working angle precision: 0.01 degree

Published documentation:
- ordinary linear dimensions: millimeter, 0 decimals unless a specific detail requires otherwise
- elevations/levels: project-specific display standard, normally meters with required decimals
- area: m2, normally 2 decimals
- volume: m3, normally 3 decimals

SBIM API / Model Dump:
- geometry transport unit: meter
- absolute project XYZ transport: meter
- conversions must be explicit at API boundary
- never infer whether a bare number is mm or m

Rule:
UI unit != API transport unit.
Every executor request schema must declare units.

## 2. Project Origin and Survey Point

Default:
- native building geometry stays close to Archicad Project Origin
- Project Zero is the local modeling elevation datum
- real-world/geodetic location is represented by Survey Point / Location Settings
- Survey Point is used for coordinated DWG/XREF/Hotlink/IFC workflows
- Survey Point is locked after project georeferencing is approved

Forbidden:
- placing the building millions of meters from Project Origin only to imitate national grid coordinates
- manually moving the whole native model after georeferencing without a controlled migration

Required Project Info:
SBIM.Project.CoordinatePolicy = PROJECT_ORIGIN_WITH_SURVEY_POINT

## 3. Stories

Core template:
- contain the minimum viable story structure only
- do not encode assumed project storey heights
- no object-type pack may silently impose storey heights

Project initialization:
1. read project brief
2. define exact story elevations/heights
3. create/rename stories
4. validate no inverted/top-linked elements
5. save story schedule/evidence

Story naming:
- use stable human names
- do not encode absolute elevation into the story name as the only source of truth
- elevation is authoritative data in Story Settings

Element policy:
- use Home Story intentionally
- use top-link where it represents design intent
- avoid arbitrary absolute-Z placement for ordinary story-based walls/columns/zones

## 4. Reference levels

Project Zero:
- local architectural datum

Sea Level:
- use Location Settings/approved geodetic basis only

Optional named reference levels:
- create only when project brief requires them
- do not create fake/placeholder absolute levels in Core template

## 5. Layer intersection baseline

Native architectural/structural construction intended to connect:
- intersection group 1

External reference / IFC / DWG / XREF / quarantine / SEO helper:
- intersection group 0 unless a controlled workflow says otherwise

See layer-intersection-policy-v0.1.yaml.

## 6. Layer naming baseline

Core prefixes:
AR_ architecture
KR_ structures
VK_ water/sewer
OV_ heating/ventilation/air-conditioning
EOM_ electrical
SS_ low current/communications
PB_ fire safety
TX_ technology
GP_ general plan
REF_ references
DOC_ 2D/documentation
QA_ validation/testing

Do not encode:
- floor number
- renovation state
- pen/color
- material
into layer names unless visibility/isolation truly depends on it.

Renovation uses Renovation Filter.
Variants use Design Options.
Appearance uses Graphic Overrides/Pen Sets.
Material identity uses Building Materials/Properties.

## 7. Initial layer combinations

00_ALL_NATIVE
- all production native model layers visible
- external references controlled separately

AR_WORK
- architecture working set
- relevant structural coordination visible
- MEP optional reference

AR_PRINT
- architecture issue/print set
- no temporary/QA/reference clutter

KR_COORD
- structural coordination

MEP_COORD
- coordination of active engineering disciplines

PB_CHECK
- fire/evacuation checking context

QA_MODEL
- QA layers and model-check context

REF_COORD
- external reference coordination context

DOC_LAYOUT_SUPPORT
- documentation helper layers where needed

Exact visibility matrix is built after final layer registry.

## 8. Views are immutable output recipes

Every saved View must intentionally store:
- Layer Combination
- Scale
- Partial Structure Display
- Pen Set
- Model View Options
- Graphic Override
- Renovation Filter
- Design Option Combination
- Floor Plan Cut Plane
- Dimensions
- Zoom/rotation where appropriate

Do not publish from an unsaved/ad-hoc viewpoint.

View naming:
<DISCIPLINE>_<SCALE>_<PURPOSE>[_<VARIANT>]

Examples:
AR_100_PLAN_WORK
AR_100_PLAN_PRINT
AR_050_PLAN_WORKING
AR_020_SECTION
AR_010_DETAIL
PB_100_EVAC
PB_100_FIRE
QA_MODEL
QA_NORM

## 9. Partial Structure Display

Required saved modes:
PSD_ENTIRE
PSD_WITHOUT_FINISHES
PSD_CORE_ONLY
PSD_LOAD_BEARING_CORE

Use:
- AR issue: normally Entire Model
- coordination/structural: Core Only or Load-Bearing Core where appropriate
- finish coordination: Entire Model / Without Finishes comparison
- junction QA: all relevant PSD modes tested

Composite/Core/Finish definitions must be compatible with these views.

## 10. Dimension standards

Separate Dimension Preferences by output purpose where needed.

Base architectural dimensions:
- mm
- 0 decimals
- associative measured value, not manual text
- manual override only with explicit reason/QA marker

Level dimensions:
- define reference level explicitly
- do not mix Project Zero and Sea Level unintentionally
- saved View controls the dimension standard

Dimension font/pen follows GRAPHICS_STANDARD_v0.1.

## 11. Scale baseline

Primary template scales:
1:500 site/context
1:200 general
1:100 plans/sections
1:50 developed plans/sections
1:20 assemblies/details
1:10 details
1:5 fine details

Do not create output-specific attributes whose semantics depend on only one scale unless necessary.
Paper-size annotation must remain paper-size.

## 12. Project creation gate

Before any GPT-generated production geometry:
- TemplateVersion present
- SchemaVersion present
- ObjectClass present
- ActiveModules present
- Working Units verified
- Story elevations verified
- CoordinatePolicy verified
- Survey Point state verified
- required attribute packs loaded
- required Favorites loaded
- no unresolved duplicate attribute names

If any gate fails:
automation status = BLOCKED_SETUP

## 13. Coordinate QA

Automated checks:
- model bounding box distance from Project Origin
- Survey Point present/configured
- Project North set
- unreasonable coordinate magnitudes
- Story elevation monotonicity
- elements with suspicious Home Story / absolute Z mismatch

Do not auto-move production geometry merely because coordinates look unusual.
Return a setup warning/block for review.
