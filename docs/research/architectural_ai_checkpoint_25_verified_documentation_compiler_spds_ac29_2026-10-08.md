# Architectural AI checkpoint 25 — verified documentation compiler for Archicad 29 / current SPDS

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Branch: feature/working-archicad-mvp
Current implementation target: Archicad 29 only

## Context carried forward

This checkpoint continues from:
- Fast Project Compiler / HOT-WARM-COLD runtime;
- open compliance + semantic graph stack;
- floor-plan/spatial logic;
- AC29 control plane;
- Construction System Envelope / detail-first design.

The question in this pass is:

**Can plans, sections, elevations, details, schedules, dimensions, labels, sheet sets and publication be generated from the same verified project state instead of becoming a separate manually maintained drawing universe?**

## Executive conclusion

Yes, to a much greater extent than we were assuming.

For Archicad 29, most of the generic documentation infrastructure already exists across:

- native Archicad documentation features;
- current Tapir 1.7.0;
- our AC29 template;
- Archicad-MCP XML schedule tooling;
- native Revision Management;
- optional external drawing engines such as Qonic / ARES;
- enterprise automation such as SWAPP.

The custom SBIM layer should **not be a new drafting/CAD engine**.

It should be a **Documentation Compiler** that decides:
- which verified views/documents are required;
- which model state/version they must represent;
- which dimensions/annotations must be present;
- which current SPDS rules apply;
- whether every required drawing is complete and current;
- which existing Archicad/Tapir operation should materialize the document.

The primary rule is:

> Documentation is a derived, associative projection of verified project truth, never an independently edited representation of the building.

---

# 1. Normative baseline changed in 2026 and must be fixed in our template

## Current base standard

Official Rosstandart currently marks:

**ГОСТ Р 21.101-2026**
"Система проектной документации для строительства. Основные требования к проектной и рабочей документации"

as **Действует**.

- Order: 129-ст, 12.02.2026
- Effective: 01.04.2026
- Replaces: ГОСТ Р 21.101-2020
- Official source: protect.gost.ru

Rosstandart also lists:
**Поправка к ГОСТ Р 21.101-2026 — ИУС 11-2026**.

Therefore any template/plugin/rule pack still claiming 21.101-2020 as the current master standard is stale until explicitly updated.

## Consequence for our Archicad template

`TDK_AC29.tpl` must be audited against:
- ГОСТ Р 21.101-2026;
- its current correction(s), including ИУС 11-2026;
- ГОСТ 21.501-2018 for AR/KR working documentation;
- referenced SPDS/ESKD standards as applicable.

### Important external-product warning

The current public SPDS GraphiCS site still describes its main standard as **ГОСТ 21.101-2020** and targets AutoCAD/ZWCAD-class platforms.

Therefore:
- it is not a current normative authority for our 2026 template;
- it is not an Archicad 29-native solution;
- its objects/workflows can be studied as UX precedent only until 21.101-2026 support is explicitly verified.

---

# 2. Current ГОСТ Р 21.101-2026 maps naturally to an automated sheet compiler

Relevant current rules include:

- documentation may be produced by automated means;
- electronic/paper forms must mutually correspond;
- primary graphical convention is generally black;
- scales follow GOST 2.302 and are not printed except where required by standards;
- main title blocks use Forms 3–6 in Appendix E;
- Form 3 applies to main working-drawing sets / graphical PD sheets;
- drawings/views/sections/details on a sheet are ordered from upper left, left-to-right and top-to-bottom;
- multiple floor plans on one sheet are ordered floor-number bottom-to-top or left-to-right;
- vector-document dimensions are in millimeters unless another SPDS rule says otherwise;
- changes/revisions and document compilation are regulated;
- specifications have standard Forms 7/8.

These are **not aesthetic preferences**.
They belong in the Documentation Contract and template validation.

---

# 3. ГОСТ 21.501-2018 remains the current AR/KR working-document composition base

Rosstandart currently marks **ГОСТ 21.501-2018 — Действует**.

For AR, the standard includes, in general:
- general data;
- floor plans, including basement/technical/attic as relevant;
- sections;
- elevations;
- floor plans if required;
- roof plan;
- partition-layout schemes where relevant;
- opening-fill layout schemes where relevant;
- other project-specific plans/schemes;
- details/fragments/local sections;
- specifications.

It also specifies what a floor plan and section should carry, including axes, relevant dimensions, wall/partition thickness, opening dimensions/locations, levels, marks and detail references.

### Consequence

A Documentation Compiler can derive a **required-document graph** from:
- project type;
- stage;
- discipline;
- project-specific systems;
- current normative/contract requirements.

It should not blindly generate every possible drawing.

---

# 4. Archicad 29 already has the core associative documentation primitives

## Keynotes

Archicad 29 Keynotes provide:
- hierarchical database;
- key/title/description/reference;
- Keynote labels/text via autotext;
- automatic refresh;
- layout legends;
- import/export;
- hotlink support;
- Teamwork support.

This is a ready structured-notes database.

Do not build a separate generic keynote/note database.

## Autotext

Archicad already exposes dynamic fields for:
- project/site/client;
- layouts;
- drawings;
- scale;
- revisions;
- changes;
- transmittals;
- project info;
- many document attributes.

This should drive title blocks and repeated sheet metadata.

Do not duplicate these values as manually typed text.

## Interactive Schedules

Native Interactive Schedules are associative:
- model -> schedule;
- editable schedule field -> model;
- schedule -> saved View;
- schedule -> Layout.

Use them as the primary source for:
- window/door schedules;
- room/zone schedules;
- finish schedules;
- component/material schedules;
- project indices where native functionality fits.

## Revision Management

Archicad's native Revision Management already has an important causal property:

When a Change is linked to model elements, every Layout containing affected elements can automatically acquire the corresponding revision/change state.

This is extremely close to our project-causal philosophy.

Do not write a parallel revision universe.

---

# 5. Tapir 1.7.0 now covers a surprisingly complete documentation pipeline

Latest GitHub release observed:
- Tapir **1.7.0**
- published 2026-10-04
- MIT
- active AC29 support.

The current repository exposes enough commands to build a real Documentation Compiler.

## View Map

Available current functionality includes:
- CreateViewMapFolder;
- CreateViewsInViewMap;
- CloneProjectMapItemToViewMap;
- Get/SetViewSettings;
- view transformations/rotation and navigator operations.

This allows the compiler to create standardized views rather than manually pre-authoring every future View.

## Sections / Interior Elevations / Details

Current Tapir includes:
- CreateSections;
- CreateInteriorElevations;
- CreateDetails;
- Worksheets and related document-database creation functions.

A room can therefore create its own interior-elevation chain programmatically.

## Layout Book

Current functionality includes:
- CreateLayoutSubset;
- CreateLayout;
- Get/SetLayoutSettings;
- Layout Info custom fields.

This means sheet hierarchy and metadata can be compiled from a document manifest.

## Drawings

`CreateDrawings` can create Drawing elements on a selected/active Layout from navigator items and supports placement/transform-related settings.

The source link is established at creation.

## Associative dimensions

This is especially important.

Tapir currently provides:
- `CreateAssociativeDimensions`;
- `GetDimensionData`;
- `CreateAssociativeDimensionsOnSection`;
- `CreateWallThicknessDimensions`.

Section/elevation dimension presets include:
- WallCompositeFaces;
- WallSkinBorders;
- SlabCompositeFaces;
- SlabSkinBorders;
- BeamOrColumnRefLineEndPoints;
- BeamOrColumnBoundingBoxCorners;
- DoorWindowWallHoleCorners;
- DoorWindowModelHotspots.

Therefore a substantial amount of dimension generation can remain **associative to actual model/section elements**.

This is much better than generating dumb 2D lines/text.

## Labels / Text / Autotext

Tapir can create/modify:
- Labels;
- Text;
- style/content;
- Autotext-backed content.

## Keynotes

Current commands include:
- GetKeynoteTree;
- create/modify/delete folders;
- create/modify/delete items;
- Keynote Autotext retrieval;
- CreateKeynoteLabels.

## Publisher

Current Tapir includes:
- GetPublisherSetNames;
- Publisher tree access;
- `PublishPublisherSet`;
- optional selected publisher-tree items.

This already supports a fully automated final publishing step.

A 2026 Graphisoft Community example also demonstrates scheduled recurring publishing through Tapir on Windows/macOS.

### Strategic conclusion

We should **not build a generic View/Layout/Publisher automation layer**.

Tapir already is that layer.

---

# 6. Schedule-scheme authoring is one of the remaining awkward AC29 gaps

Native Interactive Schedules are powerful, but schedule-scheme authoring/editing is not cleanly exposed through the standard JSON/Tapir route.

Our earlier Archicad-MCP audit found an existing workaround:
- export schedule scheme XML;
- modify bindings/columns conservatively;
- import back;
- preserve unknown XML fields.

Therefore preferred architecture:

```
Schedule Recipe
   ↓
Archicad-MCP XML scheme adapter
   ↓
native Interactive Schedule
   ↓
saved View
   ↓
Layout Drawing
```

No new schedule engine is required.

---

# 7. External drawing engines are useful as secondary/fallback accelerators, not source of truth

## Qonic

Current 2026 Qonic can:
- generate floor plans and sections from IFC;
- auto-add dimensions, annotations and room tags;
- edit generated drawings;
- export DWG.

October 2026 adds reusable Drawing Generation Presets controlling:
- discipline/product visibility;
- IFC class/material graphical rules;
- fills/hatches/boundaries/cut surfaces;
- annotations.

This is a very strong **IFC-derived drawing accelerator / external QA reference**.

But it currently does not prove:
- Russian SPDS presets;
- native Archicad associativity;
- direct ownership of our AC29 documentation truth.

Use as secondary comparison/output route.

## ARES Commander

Current ARES 2026 BIM drawing automation can:
- import IFC/RVT;
- create floor plans/sections/elevations;
- add dimensions;
- add labels from BIM properties;
- map materials;
- create sheets;
- retain BIM link and update drawings from newer model versions.

Again, this is a strong external BIM->DWG documentation engine.

It should not replace our native AC29 source-of-truth set unless a project explicitly requires a DWG-centric delivery workflow.

## SWAPP Frank

Current SWAPP documentation product publicly claims:
- native Archicad auto-dimensioning;
- dimensions/tags/callouts/interior elevations;
- view/sheet generation;
- annotation decluttering;
- repeated application after model changes;
- firm-guideline audit;
- complete construction-document sets.

This is the strongest "someone already built almost the whole documentation AI" evidence.

Unknowns remain:
- access/pricing;
- API;
- Russian SPDS;
- how much control/export we get over learned standards.

### Decision

**SWAPP remains P0 demo/product audit, not custom-code justification.**

---

# 8. Proposed core entity: Documentation Contract / Sheet Recipe

The compiler should not "make a pretty sheet."

It receives a contract.

Example:

```yaml
document_id: AR-05
document_type: floor_plan
discipline: AR
stage: R
standard:
  base: GOST_R_21_101_2026
  corrections:
    - IUS_11_2026
  discipline_standard: GOST_21_501_2018

source:
  story: 1
  model_revision: ...
  view_role: construction_plan

view:
  scale: 1:100
  layer_combination: AR_WORKING
  renovation_filter: ...
  model_view_options: ...
  graphic_override: ...
  structure_display: ...
  dimension_style: ...
  pen_set: ...

required_content:
  axes: true
  walls_partitions: true
  openings: true
  zones: true
  equipment: scoped
  section_markers: true
  detail_markers: conditional

dimensions:
  chains:
    - overall_axes
    - external_geometry
    - openings
    - internal_required
  associative_required: true

annotations:
  labels:
    - rooms
    - openings
  keynotes: visible_only
  autotext: true

layout:
  master: GOST_FORM_3_A1
  order_policy: gost_21_101_5_5_1
  placement_grid: office_rule_01
  min_clearance_mm: ...
  titleblock_mapping: ...

tables:
  - room_schedule
  - opening_schedule

publication:
  publisher_set: AR_R
  formats:
    - PDF
    - DWG
  naming_rule: ...

coverage:
  required: true
```

This is a **recipe/contract**, not a duplicate drawing model.

---

# 9. Document Coverage Signature

The same Coverage Signature concept from Fast Project Compiler should be applied to documentation.

Suggested fields:

```yaml
document_id:
source_project_revision:
source_entity_fingerprint:
view_settings_hash:
annotation_recipe_hash:
schedule_recipe_hash:
normative_standard_version:
spds_correction_set:
layout_recipe_hash:
publisher_recipe_hash:
last_generated_at:
last_validated_at:
published_file_hash:
status:
  VALID
  DIRTY_MODEL
  DIRTY_VIEW
  DIRTY_ANNOTATION
  DIRTY_STANDARD
  DIRTY_LAYOUT
  NOT_VERIFIED
```

### Why

If a wall changes:
- only sheets/views that expose that wall become DIRTY.

If ГОСТ/office documentation rule changes:
- only documents depending on that rule become DIRTY_STANDARD.

If a titleblock field changes:
- layouts update without rebuilding BIM.

This prevents "regenerate everything after every edit."

---

# 10. Documentation compilation pipeline

Preferred AC29-native path:

```
VERIFIED PROJECT STATE
        |
        v
required-document graph
        |
        v
Sheet Recipes / Documentation Contracts
        |
        +--> View Map
        |     create/configure views
        |
        +--> Viewpoints
        |     sections/interior elevations/details
        |
        +--> Annotations
        |     associative dimensions
        |     labels/autotext/keynotes
        |
        +--> Schedules / Project Indexes
        |
        +--> Layout Book
        |     master + layout + drawings
        |
        +--> Revision Management
        |
        +--> Publisher
        |
        v
VALIDATE DOCUMENT COVERAGE
        |
        v
PDF / DWG / BIMx / required outputs
```

Most boxes are existing Archicad/Tapir primitives.

---

# 11. Primary / secondary / enterprise documentation providers

## Primary — AC29 native + Tapir

Use for:
- authoritative editable project documentation;
- associative dimensions;
- native views/layouts;
- keynotes;
- schedules;
- revisions;
- Publisher.

Reason:
stays connected to the source PLN.

## Secondary — Qonic / ARES

Use for:
- batch external drawings;
- alternative DWG route;
- independent comparison/QA;
- IFC-based drawing regeneration;
- projects whose output contract is DWG-heavy.

## Enterprise accelerator — SWAPP

If accessible and configurable:
- full automated documentation;
- office-standard learning;
- annotation arrangement/decluttering;
- documentation QA.

Do not reproduce SWAPP-class generic automation until its actual fit has been tested.

---

# 12. Current SPDS software warning

Because ГОСТ Р 21.101-2026 replaced 2020 on 01.04.2026 and already has an IUS 11-2026 correction, any automation claiming "SPDS-compliant" must carry:

```
standard_id
edition
correction_set
verification_date
```

No generic flag:
`SPDS = true`.

Our Documentation Contract must version its normative base exactly.

---

# 13. Practical experiment DOC-AC29-01

After the AC29 template/workstation baseline is stable:

Use one verified floor of a test model.

1. Create a View Map folder.
2. Create/synchronize:
   - floor-plan View;
   - Section;
   - Interior Elevation.
3. Apply deterministic View Settings.
4. Create a Layout subset.
5. Create a Layout from the current Form-3 master.
6. Place Drawings from navigator items.
7. Create associative dimensions:
   - plan witness elements;
   - wall thickness;
   - section slab/wall faces;
   - opening-hole corners.
8. Create room/opening Labels.
9. Create one Keynote + label + legend.
10. Create/update one Interactive Schedule through the XML schedule adapter.
11. Place schedule on Layout.
12. Publish the selected Publisher Set/subset.
13. Change:
   - one wall;
   - one window.
14. Verify:
   - dimensions follow;
   - labels remain correct;
   - schedule updates;
   - relevant views/drawings update;
   - only affected Document Coverage Signatures become dirty.
15. Link a native Change to the modified elements and verify affected Layout Revision propagation.
16. Republish.
17. Compare PDF/DWG hash and expected changed sheets only.

### Success criterion

At least one small AR package must be rebuilt after a model change with:
- zero manual re-drafting;
- no stale model values;
- no non-associative dimension drift;
- explicit current-SPDS validation.

---

# 14. Practical experiment SPDS-2026-01

Audit current template assets against:

## Main title blocks
- Form 3;
- Form 4 if needed;
- Form 5;
- Form 6;
- IUS 11-2026 correction.

## Project Info / Autotext mappings
Ensure no duplicated manually typed project fields.

## View/Sheet order
Encode 5.5.1 sequencing.

## Drawing units/scales
Encode current 21.101 rules.

## AR document set
Cross-check against current 21.501.

## Revision/change fields
Use native Archicad data.

## Publisher
Map:
- AR/P/R set;
- PDF/DWG packages;
- file/folder naming;
- issue/transmittal output.

### Gate

Do not release TDK_AC29.tpl as "SPDS current" until this audit is PASS.

---

# 15. Annotation placement is the remaining genuinely nontrivial documentation problem

Creating an associative dimension is mostly solved.

Choosing **which** witness objects to dimension and **where** to place dimension strings/labels without clutter is still architectural/documentation intelligence.

But even here:
- SWAPP already productizes the problem;
- ARES/Qonic provide automatic examples;
- current research uses optimization/RL for annotation placement.

Therefore custom work, if needed, should focus narrowly on:
- Russian/office dimensioning intent;
- coverage checking;
- no-overlap/legibility objective;
- deterministic witness selection.

Do not write a general drawing-layout AI from scratch.

---

# 16. Documentation Quality Gate

Before publication, each document should pass:

## Source validity
- model revision current;
- required elements present;
- no unresolved critical model issues.

## View validity
- correct layer combo;
- MVO;
- GO;
- scale;
- structure display;
- filters;
- story/viewpoint.

## Content coverage
- required axes;
- dimensions;
- levels;
- labels;
- markers;
- schedules;
- notes;
- detail references.

## SPDS compliance
- current standard version;
- title block;
- ordering;
- units/scales;
- graphical conventions;
- required AR composition.

## Associativity
- no critical dumb/manual annotations where associative sources exist.

## Publication
- right Publisher set;
- naming;
- file format;
- revision/transmittal state.

Only then:
`READY_TO_PUBLISH`.

---

# 17. Roadmap removals after checkpoint 25

Custom implementation is now BLOCKED pending demonstrated gap for:

- generic view-map creation engine;
- generic section/interior-elevation creator;
- generic layout-book engine;
- generic drawing-on-layout engine;
- generic associative dimension engine;
- generic label/autotext system;
- generic keynote database;
- generic schedule engine;
- generic publisher;
- generic revision database;
- generic IFC/RVT-to-DWG auto-drawing engine;
- generic sheet-generation AI.

Custom justified layer remains:

- current Russian SPDS compiler/mapping;
- office/project Sheet Recipes;
- required-document graph;
- view/detail selection logic;
- witness-selection/dimension coverage logic;
- sheet placement/legibility policy where existing tools are insufficient;
- Document Coverage Signature;
- document completeness gate;
- orchestration/readback/QA.

---

# Strategic conclusion

The documentation layer should become one of the smallest custom layers in SBIM.

Archicad 29 + Tapir already provide most of the associative authoring and publication primitives.

Our real contribution is to compile:

`verified project state + current Russian SPDS + office standards + project stage`

into a deterministic set of:

`views + dimensions + annotations + schedules + layouts + revisions + publisher outputs`.

That is far safer than generating a second set of drawings that can drift away from the BIM model.
