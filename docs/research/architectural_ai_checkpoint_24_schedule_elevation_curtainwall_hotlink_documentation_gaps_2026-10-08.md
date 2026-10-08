# Architectural AI checkpoint 24 — schedules narrowed, elevation/Curtain Wall/hotlink/documentation reuse

Date: 2026-10-08
Status: ACTIVE RESEARCH CHECKPOINT
Target: Archicad 29 first
Branch: feature/working-archicad-mvp
Builds on: checkpoints 20–23

## Executive conclusion

The remaining Archicad 29 documentation/modeling gap is smaller again.

Confirmed ready-made/reusable paths now exist for:
- exterior Elevations;
- deep Curtain Wall create/modify including panel/frame parts;
- Hotlink node/instance management;
- Publisher/export workflows;
- most Interactive Schedule XML editing.

The schedule gap is now narrowly defined as:
1. criteria code tables / criteria editing;
2. deterministic import/export lifecycle automation;
3. reading produced schedule rows if needed.

Everything else should be reused or ported, not rebuilt.

## 1. Exterior Elevation is not an Archicad 29 capability gap

The MIT repository davidharutyunyan/archicad-mcp-connector implements Elevation as a first-class viewpoint marker.

`ViewsMarkers.cpp` contains:
`CreateElevation(spec) -> CreateCutPlaneLike(spec, API_ElevationID)`

and registers:
`API_ElevationID -> CreateElevation / SerializeCutPlaneLike / ModifyCutPlaneLike`.

The typed MCP surface exposes `create_elevations`.

Supported semantics include:
- begin/end line;
- view side;
- depth;
- horizontal range;
- vertical range;
- name;
- reference ID;
- common element fields.

Conclusion:
the absence of CreateElevationsCommand in the project's older Tapir revision was a Tapir surface gap, not an Archicad limitation.

Decision: HARVEST_OR_USE_PROVIDER, no custom Elevation subsystem.

## 2. Curtain Wall deep writes are already implemented openly

`davidharutyunyan/archicad-mcp-connector` contains `ComplexElementsCurtainWall.cpp` and typed tools:
- create_curtain_walls;
- modify_curtain_walls;
- modify_curtain_wall_parts.

Observed functionality includes:
- straight/polyline/curved base path;
- height and flip;
- primary and secondary grid patterns;
- fixed module sizes;
- number-of-divisions logic;
- flexible modules;
- grid origin and end-with settings;
- panel outer/inner/cut surfaces;
- panel thickness;
- panel building material;
- frame surface;
- frame building material;
- individual panel modification;
- individual frame modification;
- serializers for CurtainWall, Segment, Frame, Panel, Junction and Accessory.

Current Tapir main can deeply read Curtain Wall subelements/details but no CreateCurtainWall or ModifyCurtainWall command was found in this pass.

Conclusion:
deep Curtain Wall write is an AC29 port/provider choice, not a from-scratch native gap.

New test: CW-PORT-01.

## 3. Hotlink CRUD is also largely solved

The same MIT connector exposes:
- GetHotlinks;
- PlaceHotlinks;
- UpdateHotlinks including relink;
- DeleteHotlinks with optional keepElements/break semantics;
- MergeFile.

It models:
- module/XRef node hierarchy;
- source status;
- source path;
- update time;
- story range/source story;
- placement transform;
- mirror/rotation;
- layer/story;
- nested behavior;
- source relinking;
- instance element count through proxy mapping.

Its live documentation test exercises placing, reading and updating Hotlinks.

Current Tapir main also advanced beyond the project's older baseline.
Observed commands at current main include:
- CreateHotlinkNodesCommand, registered since 1.5.9;
- CreateHotlinkInstancesCommand, since 1.5.9;
- ChangeHotlinkInstancesCommand, since 1.5.9.

No Tapir DeleteHotlink command was found during this pass.

Conclusion:
generic Hotlink CRUD should not be custom. Prefer current Tapir where sufficient; use/port open MIT implementation for relink/update/delete semantics if necessary.

## 4. Publisher/export is not custom scope

Existing open surfaces cover:
- Publisher Set discovery;
- PublishPublisherSet;
- layouts and drawings;
- PDF export;
- IFC export;
- DXF/DWG workflows;
- 3D model export;
- module export;
- drawing placement/update;
- schedule/list/toc Navigator items as drawing sources.

Tapir already had PublishPublisherSet; the MIT connector provides a larger tested documentation/export surface.

Conclusion:
custom work is policy/orchestration only: which outputs are dirty, required and releasable.

## 5. Interactive Schedule: actual public API boundary

Official Archicad 29 API exposes Schedule as:
- Navigator item;
- view node;
- Interactive Schedule window type;
- a placeable drawing source.

Teamwork permission enums even distinguish permissions to create and delete/modify schedules/indexes.

However no public structured C++/JSON CRUD surface for Scheme Settings was found:
- no ScheduleScheme object;
- no criteria API;
- no field/column API;
- no Scheme_Settings import/export command API.

This matches the independent deep audit in `alesdev88/Archicad-MCP`.

## 6. Major reuse candidate: alesdev88/Archicad-MCP schedule engine

Repository: alesdev88/Archicad-MCP
Observed release/commit in this pass: v0.7.1 / bc147fe107a24fc59f5b2ba9537bf6a5e711614f
License: MIT.

The repo contains an implemented schedule subsystem, not merely a design:
- `src/archicad_mcp/schemes/model.py`;
- `columns.py`;
- `spec.py`;
- `validate.py`;
- `xml_io.py`;
- `src/archicad_mcp/core/schemes.py`;
- dedicated tests and XML fixtures.

The MCP server currently registers:
- read_schedule_scheme;
- edit_schedule_scheme;
- validate_schedule_scheme.

## 7. Schedule XML engine capabilities

The subsystem uses Archicad's official Scheme Settings XML Export/Import seam.

It provides:
- byte-exact no-op round trip validation;
- safe parsing;
- preservation of unknown/unmodelled XML sections;
- ordered columns;
- add/remove/reorder/rename columns;
- retarget column bindings;
- width edits where the exact field exists;
- scheme rename;
- dry-run by default;
- never overwrite source XML;
- atomic write to the destination;
- property GUID bindings;
- property-name-to-GUID resolution against a live project;
- GDL-parameter bindings;
- built-in field bindings;
- validation of property bindings;
- warnings for caption/binding disagreement.

Important format findings already encoded:
- Header_Items are a linked-list/tree structure, not a plain XML list;
- property binding uses ACPropertyGuid;
- GDL parameter binding uses ACPropertyName/Parameter_Desc_Name plus type/index;
- built-in fields use Parameter_Type + Parameter_Index.

Decision:
REUSE/HARVEST this MIT subsystem instead of writing a schedule XML engine.

## 8. Schedule criteria are the remaining true gap

The current implementation deliberately preserves criteria unchanged.

`apply_spec()` explicitly reports criteria editing as not implemented because Archicad's numeric Param_Type / Relation_Index codes are undocumented.

Current measured code table in the upstream repo includes at least:
- Param_Type 88 + Relation_Index 1: element classification criterion;
- Param_Type 232 + Relation_Index 12: property/string-style criterion, with exact relation semantics still incomplete.

The upstream research method is sound:
1. scratch project;
2. export scheme before;
3. change exactly one criterion field;
4. export after;
5. diff;
6. build empirical code table.

Residual research:
- element type/classification variants;
- layer equals/not-equals;
- property empty/not-empty;
- property equals/contains/relational comparisons;
- OR/AND/bracket semantics;
- numeric and enum comparisons;
- classification hierarchy semantics.

New test/research track: SCHEDULE-CRITERIA-01.

## 9. Schedule Import/Export automation remains unconfirmed

Search of:
- official Archicad DevKit;
- current Tapir;
- davidharutyunyan open connector

found no confirmed command/API for automating Scheme Settings Export/Import.

Current safe architecture:
`deterministic XML core` is authoritative;
`manual Export + Import` is the baseline transport;
optional GUI automation may later reduce clicks but must stay isolated from the schedule logic and never become the only source of truth.

Do not use fragile locale-dependent GUI scripting as the canonical schedule editor.

## 10. Schedule output rows

The schedule XML subsystem edits scheme definitions, not the generated row data.

No direct API returning Interactive Schedule output rows has been confirmed.

Potential reuse path:
- place/publish Schedule via Navigator/Publisher;
- export to a tabular format if Archicad Publisher supports it in the actual project setup;
- otherwise compute equivalent data from element/property queries where the schedule is only a report, not the authoritative calculation engine.

Research track: SCHEDULE-OUTPUT-01.

## 11. Husky status for schedules

Current public Husky Archicad material does not prove Interactive Schedule scheme CRUD.

Do not infer Archicad schedule support from Husky Revit schedule features.

Keep HUSKY-SCHEDULE-01 as a live enumeration test:
- list tools containing schedule/index/scheme;
- inspect exact schemas;
- verify AC29 host;
- compare against XML engine capabilities.

## 12. Roadmap deletion

STOP / DO NOT BUILD FROM SCRATCH:
- exterior Elevation creation;
- generic Curtain Wall create/modify framework;
- generic panel/frame manipulation framework;
- generic Hotlink node/instance CRUD;
- generic Publisher execution;
- Interactive Schedule XML parser/serializer;
- schedule column editor;
- schedule binding validator.

KEEP / RESEARCH:
- Schedule criteria code table/editor;
- safe Scheme XML import/export transport;
- schedule output extraction if required;
- AC29 port/live proof of open Curtain Wall surface;
- capability arbitration across Tapir/MIT/Husky.

## 13. New tests

CW-PORT-01:
Port or wrap the MIT Curtain Wall surface on AC29 and verify create, grid pattern, panel/frame classes, individual part writes and read-back.

HOTLINK-01:
Compare current Tapir vs MIT/native for create node, place, move, relink, update, delete/break, source status and proxy mapping.

SCHEDULE-XML-01:
Adopt upstream MIT schedule engine fixtures/tests and run byte-exact round trips on anonymised AC29 exports from our environment.

SCHEDULE-CRITERIA-01:
Build empirical Param_Type/Relation_Index truth table on a scratch AC29 file by single-variable export diffs.

SCHEDULE-IMPORT-01:
Empirically determine whether importing an edited XML with the same Scheme ID updates in place or creates a duplicate; record naming/ID behavior.

SCHEDULE-OUTPUT-01:
Determine the cheapest reliable route to generated schedule rows without GUI scraping.

## Strategic conclusion

The documentation/modeling boundary is now:

`native/open Elevation + Curtain Wall + Hotlink + Publisher`
+
`MIT Schedule XML engine`
+
`small custom criteria/import/output tail`.

This is substantially smaller than a custom documentation subsystem.