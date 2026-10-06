# Archicad 29 SBIM Data Schema v0.1

Status: draft
Purpose: stable semantic contract between Archicad template, GPT planner/executor, normative router, IDS and IFC.

## 1. Separation of concerns

Project context belongs to Project Info:
- object class
- active disciplines/modules
- template/schema version
- normative pack/version
- project identifiers

Element semantics belong to Archicad Properties:
- element role
- function
- fire/accessibility/MEP state
- normative QA result
- exchange/source metadata

Physical material identity belongs to Building Materials.

Do not repeat project object class on every element.

## 2. Primary classification policy

Use Archicad's native/current Classification System as the primary generic element classification and IFC type-mapping source.

Do not duplicate every native Archicad element class in a second SBIM classification system.

Use project/object-specific IDS classifications only when a contractual or normative information requirement needs them.

Property availability must be constrained by Classification where practical.

## 3. Project Info custom fields

Required custom Project Info keys:
- SBIM.TemplateVersion
- SBIM.SchemaVersion
- SBIM.Project.ObjectClass
- SBIM.Project.ActiveModules
- SBIM.Project.ModuleDepths
- SBIM.Project.NormativePackVersion
- SBIM.Project.RouteVersion
- SBIM.Project.CoordinationStatus
- SBIM.Project.CoordinatePolicy

Expected object-class values align with normative repository:
- residential.izhs
- residential.mkd
- public.trade_entertainment_complex
- public.multifunctional
- public.education
- industrial.production
- etc.

ActiveModules align with module_taxonomy:
- architecture
- structures
- foundations
- reinforced_concrete
- steel_structures
- fire_safety
- evacuation
- accessibility
- water_supply
- sewerage
- heating
- ventilation
- air_conditioning
- smoke_control
- gas_supply
- electrical_power
- lighting
- low_current
- fire_automation
- automation_dispatching
- technology
- general_plan
- landscaping
- thermal_protection
- acoustics
- daylight_insolation

## 4. Core property groups

### SBIM.Core
StableTypeID
ElementRole
Discipline
SourcePack
AutomationState
AutomationLock
DataStatus

### SBIM.Space
FunctionCode
FunctionName
OccupancyType
OccupantCount
WetZone
AccessibleRequired
FireCompartmentID
SmokeZoneID

### SBIM.Fire
FireResistanceRequired
FireResistanceProvided
FireHazardClass
IsFireCompartmentBoundary
IsEvacuationRouteElement
EvacuationRouteID
IsSmokeBarrier

### SBIM.Accessibility
Required
RouteID
ClearWidthRequired
ClearWidthProvided
ThresholdHeight
Slope

### SBIM.MEP
SystemCode
SystemName
Discipline
ServiceZoneID
FireRelated
RequiresAccess
AccessZoneID

### SBIM.Norm
Status
RulePackVersion
RuleIDs
ViolationIDs
WarningIDs
LastCheckedAt
CheckScope

### SBIM.Exchange
ExternalID
SourceSystem
SourceModel
SourceDiscipline
ReadOnlyReference
IFCExportClassOverride

### SBIM.QA
Status
IssueCode
IssueMessage
Reviewed
Reviewer
LastReviewAt

## 5. Data-state vocabulary

SBIM.Core.DataStatus:
- VERIFIED
- PROJECT_DEFINED
- UNVERIFIED
- PLACEHOLDER
- IMPORTED
- QUARANTINE

SBIM.Core.AutomationState:
- MANAGED
- USER_MANAGED
- REFERENCE
- LOCKED
- QUARANTINE

SBIM.Norm.Status:
- NOT_CHECKED
- PASS
- WARNING
- ERROR
- NOT_APPLICABLE
- BLOCKED_SOURCE

SBIM.QA.Status:
- PASS
- WARNING
- ERROR
- REVIEW
- IGNORE_WITH_REASON

## 6. StableTypeID

Purpose:
- machine-stable type identity independent of element GUID
- points to a registered Favorite/type definition

Pattern:
SBIM.TYPE.<DISCIPLINE>.<ELEMENT>.<TOKEN>

Examples:
SBIM.TYPE.AR.WALL.EXT_CERAMIC_MW_BRICK
SBIM.TYPE.AR.WALL.INT_PARTITION_GYPSUM
SBIM.TYPE.KR.COLUMN.RC_RECT
SBIM.TYPE.VK.PIPE.COLD_WATER
SBIM.TYPE.OV.DUCT.SUPPLY

Do not put placed-element GUID into StableTypeID.
Placed element keeps its native Archicad GUID.

## 7. IDS policy

IDS is used to add object/project-specific information requirements.

Rules:
- Core SBIM property schema is versioned separately.
- IDS import is additive; do not depend on IDS to mutate existing Core properties.
- Generate IDS from selected object route + active modules only.
- Do not load inactive-domain requirements.
- Import IDS into a dedicated IFC Property Mapping preset for the project/route.
- Record IDS source/version in Project Info.

Example:
TRC with architecture + fire_safety + water_supply:
Core TPL
+ PACK_TRC
+ Core Properties
+ generated IDS(TRC, AR, PB, VK)
+ Favorites relevant to those domains

## 8. Property availability

Do not expose all properties to every classification.

Examples:
- OccupantCount only to Zones/Spaces where applicable.
- FireResistanceRequired to construction elements/doors/openings where applicable.
- Slope to ramps/slabs/roofs and accessibility-relevant elements.
- MEP SystemCode to MEP/distribution elements.
- Norm/QA status may be broadly available because Graphic Overrides consume it.

## 9. Graphic Override contract

Minimum QA combinations:
QA_DATA_MISSING
QA_NORM_STATUS
QA_AUTOMATION_STATE
PB_FIRE_COMPARTMENTS
PB_EVACUATION
MEP_SYSTEMS

Recommended rule semantics:
- SBIM.Norm.Status == ERROR -> strong error override
- SBIM.Norm.Status == WARNING -> warning override
- SBIM.Core.DataStatus == PLACEHOLDER -> placeholder override
- SBIM.Core.AutomationState == REFERENCE -> subdued/reference override
- SBIM.QA.Status == REVIEW -> review override

Do not encode QA colors in property values. Colors live in Graphic Override/Pen standards.

## 10. Favorites contract

Every managed Favorite must record:
- Favorite canonical name
- StableTypeID
- expected Archicad tool
- Building Material/Composite/Profile
- Layer
- Classification
- Core properties/default values
- allowed object scopes
- allowed modules
- source pack/version
- release status

A Favorite is the preferred creation primitive for GPT.
The executor should select a verified Favorite/type and then alter only parameters required by the command/project.

Do not construct common production elements from dozens of raw settings every time if a released Favorite exists.

## 11. Project Info vs element Property

Project Info:
- project-wide facts
- sheet/autotext/IFC project metadata
- object routing context

Element Property:
- fact about a specific placed element/type/material
- searchable/listable/GO/IFC data

Building Material Property:
- fact about a physical material identity

Favorite registry:
- default configuration used to create elements

## 12. Import/migration

Core schema updates must be explicit migrations:
- source version
- target version
- renamed properties
- changed enum values
- changed availability
- changed defaults
- affected Favorites / GO / schedules / IFC mappings

No silent renames after release.

## 13. Initial execution order for template build

1. Create Project Info custom fields.
2. Install/review Archicad Classification.
3. Create SBIM property groups.
4. Assign classification availability.
5. Create Graphic Override QA rules.
6. Create material attributes.
7. Create first verified Favorites.
8. Generate a minimal IDS test.
9. Import IDS into a clean test project.
10. Export IFC and verify mapped data.
11. Read model via Model Dump/API and verify semantic fields.

## 14. Release gates

- no duplicate Core property names
- enumerations stable
- classification availability tested
- IDS additive behavior tested
- IFC type/property mapping verified
- Graphic Override rules verified
- Favorites preserve classification/properties
- agent can resolve Favorite by StableTypeID
- Project Info object route matches normative router
