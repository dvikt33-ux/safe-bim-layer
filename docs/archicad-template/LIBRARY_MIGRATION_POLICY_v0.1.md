# Archicad 29 Library and Migration Policy v0.1

Status: draft
Target: new Archicad 29 projects using SBIM template.

## 1. New projects use Global Library

Archicad 29 new projects use the Global Library / libpack technology.

Core policy:
- new SBIM TPL uses Global Library only as Graphisoft base content;
- do not preload old Archicad 26/27 monolith libraries into the new Core template;
- do not copy migration libraries into the new template;
- additional Graphisoft libpacks are loaded only when needed.

## 2. SBIM custom library

Reusable custom content is not stored ad hoc in each project.

Preferred structure:
SBIM_LIBRARY/
  00_MACROS/
  01_ANNOTATION/
  02_DOORS_WINDOWS/
  03_FURNITURE_EQUIPMENT/
  04_MEP_OBJECTS/
  05_SITE/
  06_DETAILS/
  90_PROJECT_PACKS/
  99_TEST/

Solo project:
- linked SBIM library/package

Teamwork:
- BIMcloud library equivalent

## 3. Embedded Library

Embedded Library is for project-specific content only.

Allowed:
- custom object created specifically for the project
- project-specific Patch
- one-off custom door/window component
- project-specific texture required to preserve the project
- project-specific macro/text file where justified

Forbidden by default:
- whole manufacturer catalog
- duplicate copy of Global Library objects
- reusable company/SBIM standard objects
- random downloaded objects with unknown provenance
- large texture collections

Reason:
embedded content exists only in that project and becomes difficult to update centrally.

## 4. Manufacturer content intake

Every manufacturer object/system entering SBIM must record:
- manufacturer
- product/system
- source URL/document
- download date
- license/usage terms if available
- Archicad version / GDL compatibility
- geometry complexity
- polygon count / performance note where measurable
- required libraries/macros/textures
- classification/properties
- dimensions verified against technical source
- release status

Statuses:
QUARANTINE
REVIEWED
PROJECT_APPROVED
CORE_APPROVED

Manufacturer content is PROJECT_APPROVED by default, not CORE_APPROVED.

## 5. No silent substitution

If a Favorite references a missing library part:
automation must return BLOCKED_LIBRARY.

Do not silently substitute:
- another door
- another window
- generic object
- nearest library item

unless the action explicitly authorizes a replacement/migration.

## 6. Migration cut

Global Library (AC28+) is a technology boundary relative to older monolith libraries.

For old project:
- use Graphisoft Migrate Libraries workflow
- do not convert the old project into the SBIM Core template in-place without migration tests

For new project:
- start directly from Global Library-based SBIM TPL

Do not mix old Monolith favorites/MVO defaults into the new TPL without explicit conversion/verification.

## 7. Template versioning

Template:
AC29_RU_SBIM_<major>.<minor>.tpl

Data schema:
SBIM.SchemaVersion

Library pack:
SBIM.LibraryVersion

Every project records all three versions in Project Info.

Migration matrix tracks:
- source TPL
- target TPL
- source Archicad
- target Archicad
- Library version
- Data schema
- changed Favorites
- changed MVO
- changed properties/classifications
- changed GDL/library parts

## 8. Update policy

Never update a production template by replacing files in place with no version bump.

Workflow:
1. clone clean test project from released TPL
2. apply candidate library/template change
3. open/reload libraries
4. check missing/duplicate library parts
5. regenerate plans/sections/3D
6. validate Favorites
7. validate schedules/properties
8. run Model Dump
9. run PDF/DWG/IFC issue tests
10. issue new template/library version

## 9. Performance policy

Core library must stay lean.

Before admitting custom GDL object to Core:
- verify it has clear recurring value
- inspect 2D and 3D behavior
- test at low/medium/high detail where applicable
- avoid unnecessarily dense geometry
- avoid uncontrolled high-resolution textures
- verify missing-texture behavior
- verify plan symbol performance in repeated placement

A manufacturer object that is visually heavy but semantically weak remains a project/reference asset, not Core.

## 10. Clean-project test

Released TPL must open on a clean Windows/Archicad 29 environment with:
- Global Library available
- required SBIM library available
- no developer machine absolute paths
- no missing object
- no missing texture
- no duplicate library warning
- no migration library required

## 11. Archiving

For project archive:
- save PLA or agreed archive format when required
- preserve project-specific embedded content
- record template/library/schema versions
- retain issued translators/settings separately where contractual reproducibility matters
