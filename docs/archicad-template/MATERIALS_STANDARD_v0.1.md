# Archicad 29 Materials / Composites / Surfaces Standard v0.1

Status: draft-for-junction-tests
Target: Archicad 29 RU template
Depends on: GRAPHICS_STANDARD_v0.1.md

## 1. Principle

Archicad Building Material is the atomic construction-material identity.
A Building Material owns:
- cut fill and cut-fill pens
- intersection priority
- fill orientation
- default Surface
- classifications/properties including physical properties

Composite is an assembly of Building Materials with skin thicknesses and separator lines.
Complex Profile is a geometric assembly whose components also use Building Materials.
Surface is appearance only; it is not the physical material identity.

Never create one Building Material per wall thickness or per project wall type.
Thickness/configuration belongs to Composite/Profile/Favorite.

## 2. Stable identity

Canonical Building Material name:
BM_<GROUP>_<MATERIAL>[_<QUALIFIER>]

Canonical stable ID:
SBIM.BM.<GROUP>.<MATERIAL>[.<QUALIFIER>]

Examples:
BM_STR_CONCRETE_RC
SBIM.BM.STR.CONCRETE.RC

BM_MASONRY_CERAMIC_BLOCK
SBIM.BM.MASONRY.CERAMIC_BLOCK

Rules:
- English ASCII machine token in canonical name.
- Human Russian description is stored in Description/Properties.
- Do not encode thickness in Building Material name.
- Do not encode project, floor, manufacturer or color in generic Building Material name.
- Manufacturer-specific material is a separate material only when its physical/technical identity materially matters.
- Cross-project import uses Match by Name, not index, for managed template packs.
- Archicad index is treated as runtime-local, not a cross-project API key.
- Attribute name and stable ID are immutable after release except through a migration table.

## 3. Attribute installation order

1. Classification systems
2. Property definitions
3. Pens / Lines / Fills
4. Surfaces
5. Building Materials
6. Composites
7. Complex Profiles
8. Favorites
9. Views / Graphic Overrides / Schedules

Reason: imported Building Material classification/property values can be lost if referenced Classification/Property definitions do not already exist in the host project.

## 4. Intersection priority model

Archicad valid range: 0..999.
Higher priority cuts lower priority when priority-based connection conditions are met.

Template policy:
- use broad semantic bands with gaps
- never tune a global Building Material priority for one local junction
- local exceptions require geometry/junction logic or an explicitly named duplicate material
- every priority change after v1.0 requires junction-regression tests

Draft bands:

900-949  primary structural concrete/steel
850-899  structural masonry / dense structural mineral bodies
800-849  secondary structural masonry/timber
700-799  non-load-bearing solid wall bodies / boards
600-699  cementitious beds, screeds, renders used as substantial layers
500-599  thermal/acoustic insulation
400-499  sheathing/substrates
300-399  membranes/air/drainage/cavities represented as skins
200-299  finishes
100-199  adhesives/coatings/auxiliary modeled layers
000-099  special non-cutting placeholders only

Draft priority assignments are provisional until junction test matrix passes.

## 5. Core / Other / Finish policy

For Composites and Profiles:
- Core = primary body of the construction used for structural/core-only representation
- Other = insulation, cavities, service/substrate layers which are not finish
- Finish = outer finish skins only

Rules:
- Core skins must remain contiguous.
- Finish skins must be outermost contiguous finish zones.
- Thermal insulation is normally Other, not Core.
- Air cavity is Other.
- Plaster, tile and decorative cladding finish skins are Finish.
- Main body of a non-load-bearing partition can still be Core; the element classification carries its structural function.

## 6. Physical properties

Never invent thermal conductivity, density, heat capacity, embodied energy or embodied carbon.

Allowed sources:
- verified manufacturer declaration / technical documentation
- verified normative/reference source
- Archicad Material Catalog when source and value are recorded

If source is not verified:
- keep physical property undefined in production
- set SBIM.Source.Status = UNVERIFIED where applicable

No generic guessed lambda/density values are permitted in released template packs.

## 7. Collision-detection policy

Default: Building Material participates in collision detection.

Exceptions:
- air cavity: false
- explicitly modeled non-solid void/service gap: false
- membranes represented only for documentation: normally false
- all structural solids, insulation solids and finish solids: true unless a tested discipline rule says otherwise

This policy is important for Archicad Collision Detection and IFC export workflows.

## 8. Surface policy

Canonical name:
SURF_<MATERIAL/APPEARANCE>[_<QUALIFIER>]

Surface is visual appearance, not construction identity.

Starter set:
SURF_GENERAL_LIGHT
SURF_CONCRETE_GREY
SURF_CONCRETE_DARK
SURF_BRICK_RED
SURF_CERAMIC_NEUTRAL
SURF_PLASTER_WHITE
SURF_PAINT_WHITE
SURF_PAINT_GREY
SURF_STEEL_GALV
SURF_STEEL_PAINTED
SURF_ALUMINIUM
SURF_WOOD_NATURAL
SURF_GLASS_CLEAR
SURF_INSULATION_GENERIC
SURF_WATERPROOF_BLACK
SURF_SOIL
SURF_GRAVEL
SURF_ASPHALT

Rules:
- keep template Surface set deliberately small
- Building Material carries its default Surface
- element-level surface override is only for a real finish/appearance override
- do not duplicate Building Materials solely to obtain a different render color
- textures must be stored in managed project/library locations and tested for missing-link behavior
- technical elevations should rely on vectorial cover fills where needed, not photoreal textures

## 9. Starter Building Material families

See attribute-registry-v0.1.yaml for machine-readable draft.

Required generic families:
- structural reinforced concrete
- structural plain concrete
- structural steel
- structural timber
- ceramic masonry block
- ceramic brick masonry
- aerated concrete masonry
- silicate/calcium-silicate masonry
- gypsum block
- cement-sand mortar/render
- cement screed
- gypsum plaster
- gypsum board
- cement board
- mineral wool
- EPS
- XPS
- PIR/PUR insulation
- waterproofing membrane
- vapor-control membrane
- air cavity
- ceramic tile
- stone finish
- metal cladding
- generic soil
- gravel/crushed stone
- asphalt

Manufacturer-specific variants are project/object packs, not Core template defaults.

## 10. Composite naming

Canonical:
CMP_<ELEMENT>_<FUNCTION>_<ASSEMBLY_TOKEN>_<TOTAL_MM>

Examples of naming only:
CMP_WALL_EXT_<assembly>_520
CMP_WALL_INT_<assembly>_120
CMP_SLAB_FLOOR_<assembly>_300
CMP_ROOF_FLAT_<assembly>_450

The number must equal the exact sum of encoded skin thicknesses.
If one skin changes, total thickness in the name and Favorite must change together.
A composite may not be released if name total != actual total.

Core TPL should contain only a small tested starter set.
Object packs (IZHS/MKD/TRC) may add project-appropriate assemblies.

## 11. Composite release metadata

Every released Composite must have registry data:
- canonical_name
- object_scope
- applicable_element_types
- ordered skins
- exact skin thicknesses
- skin role: core/other/finish
- total thickness
- reference plane policy
- separator line policy
- external/internal orientation
- source/provenance
- normative_status
- Favorite references
- junction test status

## 12. Reference plane rules

Walls:
- use a deliberate stable reference line tied to the primary/Core construction logic
- do not change reference line convention between Favorites of the same family without reason

Composite Slabs:
- favor Top of Core or Bottom of Core when coordination depends on structural level
- finish buildup must not silently shift structural elevations

Roofs:
- define whether roof reference plane tracks core/structural deck or finished surface in the family specification

Reference-plane convention must be stored in the registry and Favorite.

## 13. Complex Profile policy

Use Complex Profiles only when cross-section geometry genuinely varies beyond a simple Composite.

Good uses:
- parapets
- cornices
- plinth/foundation wall transitions
- edge beams
- multi-material façade bands
- special wall bases
- standard steel profiles

Avoid:
- making a profile merely because a simple wall composite exists
- hiding project-specific arbitrary geometry in generic Core profiles

Profile components use the same Building Material registry.
Profile modifiers must have stable names if automation will address them.

## 14. Priority-junction regression matrix

Before v1.0 test at minimum:
- RC vs ceramic masonry
- RC vs brick
- RC vs insulation
- masonry vs insulation
- masonry vs plaster
- slab vs wall core
- beam vs wall
- column vs composite wall
- two equal-priority walls with Junction Order
- roof/shell/morph intersections after Merge/Trim
- wall corners with reference-line intersection
- façade cladding / insulation / structural wall at opening
- floor screed vs wall finish
- foundation / wall / insulation / waterproofing base detail

Each test requires plan + section + 3D evidence.

## 15. Attribute import/export

Managed packs:
- export XML from Archicad Attributes
- preserve folder structure
- import Match by Name
- include associated attributes deliberately
- never bulk-import unknown associated attributes without review

Do not depend on matching numerical indices between unrelated projects.

## 16. Template attribute folders

Building Materials:
01_STRUCTURAL
02_MASONRY
03_BOARDS
04_INSULATION
05_MORTAR_SCREED
06_MEMBRANES_CAVITIES
07_FINISH
08_SITE
90_PROJECT_PACK
99_TEST_QUARANTINE

Surfaces:
01_GENERIC
02_MINERAL
03_MASONRY
04_METAL
05_WOOD
06_GLASS
07_FINISH
08_SITE
90_PROJECT_PACK

Composites:
01_WALL
02_PARTITION
03_SLAB
04_ROOF
05_FOUNDATION
90_PROJECT_PACK
99_TEST_QUARANTINE

Profiles:
01_WALL_SPECIAL
02_COLUMN
03_BEAM
04_FACADE
05_ROOF_EDGE
06_FOUNDATION
90_PROJECT_PACK
99_TEST_QUARANTINE

## 17. Release gates

A Building Material can enter Core v1.0 only if:
- canonical name and ID are unique
- cut fill exists
- default Surface exists
- priority is assigned
- collision flag reviewed
- physical values are either sourced or intentionally undefined
- classification/property dependencies exist
- junction behavior passes required tests

A Composite can enter Core v1.0 only if:
- all skins are registered Building Materials
- exact thickness sum matches its name/registry
- Core/Other/Finish roles are valid
- reference plane is defined
- element-type availability is defined
- key junction tests pass
- DWG/PDF section output is checked

## 18. Deferred to next cycle

- final numeric priority values after junction tests
- exact starter Composite thicknesses for IZHS/MKD/TRC packs
- thermal-property population from verified sources
- detailed manufacturer libraries
- Profile modifier registry
