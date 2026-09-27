# Parametric GDL library factory — 10 research passes

Goal: expand what Safe BIM can create without developing/signing a custom Archicad `.apx`, while keeping generated content reusable and version-controlled.

This is a source/documentation audit only. No local converter execution and no Archicad writes were performed.

## Pass 1 — Archicad already ships the compiler tool

Graphisoft documents that `LP_XMLConverter.exe` is shipped with Archicad on Windows, in the main Archicad installation folder. It converts between binary library parts and text source formats.

Official source:
https://gdl.graphisoft.com/tips-and-tricks/how-to-use-the-lp_xmlconverter-tool/

This is important for the user's setup: a separate custom Add-On Developer ID is not required just to compile GDL library sources into `.gsm` library parts.

## Pass 2 — use HSF/XML as source, not binary GSM as the development format

Graphisoft documents two text/source formats:

- XML: one XML file + optional images;
- HSF: folder-based source with XML + `.gdl` scripts + images.

HSF is available from Archicad 23 and is better suited to normal source control/diffs.

Official converter commands include:

- `libpart2hsf`;
- `hsf2libpart`;
- `l2hsf`;
- `hsf2l` / `makelibrary -format hsf` depending workflow.

Source:
https://gdl.graphisoft.com/tips-and-tricks/how-to-use-the-lp_xmlconverter-tool/

## Pass 3 — GDL is a native parametric-object technology, not a mesh hack

Graphisoft describes GDL library parts as parametric objects capable of 3D geometry, 2D symbols, parameters, UI and properties. Library parts cover objects, furniture, doors/windows and other placeable content.

Sources:
- https://gdl.graphisoft.com/gdl-basics/about-gdl/
- https://gdl.graphisoft.com/reference-guide/gdl-definition/

Use case: repeated parametric fixtures, custom furniture, signage, facade accessories, equipment, standardized room components and other objects whose native identity should remain one parametric Archicad object.

Do not replace native Wall/Slab/Zone semantics with GDL when a native BIM element already fits the task.

## Pass 4 — Main ID can be a stable content identity

Graphisoft's GDL documentation distinguishes Main ID and Revision ID. LP_XMLConverter compilation changes the Revision ID while leaving the Main ID unchanged. Renaming an object does not make it incompatible when the Main ID remains the same.

Source:
https://help.graphisoft.com/AC/29/INT/GDL.pdf

This enables a version-controlled Safe BIM library catalog:

`semantic role -> Main GUID -> expected revision/source hash -> display name`.

The source hash belongs to Safe BIM; Main GUID belongs to the Archicad library-part identity.

## Pass 5 — Tapir 1.5.9 can inventory library parts by Main GUID

`GetAvailableLibraryParts` returns:

- `guid` = Main GUID from `ownUnID`;
- current database `index`;
- documentName;
- fileName;
- typeId;
- `skippedCount` for partial inventory detection.

Tapir source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/LibraryCommands.cpp

Graphisoft explicitly warns that a library-part index is not constant for the life of a project. Therefore **never use `index` as persistent identity**.

Official API source:
https://archicadapi.graphisoft.com/documentation/api_libpart

Persistent catalog key should be Main GUID.

## Pass 6 — Tapir can load the compiled content

Tapir 1.5.9 provides:

- `AddFilesToEmbeddedLibrary`;
- `GetLibraries`;
- `SetLibraries`;
- `AddLibraries`;
- `ReloadLibraries`;
- `GetAvailableLibraryParts`.

`AddLibraries` checks existing locations and skips already-present folders. `GetLibraries` reports availability/read-only state.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/LibraryCommands.cpp

Recommended first implementation: keep a Safe BIM-generated local library folder and use `AddLibraries`, rather than copying every generated part into the embedded project library. Embedded import can remain an explicit packaging action.

## Pass 7 — CreateObjects currently resolves by library-part name, so add a GUID preflight

Tapir's `CreateObjects` path resolves `libraryPartName` into Archicad's library index. The source comment explicitly says the Create side resolves `libraryPartName`; Modify does not swap the library part of an existing object.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ElementCreationCommands.cpp

This creates a safety requirement:

1. inventory library parts;
2. locate the intended Main GUID;
3. confirm its current document name is unique/resolvable;
4. only then call `CreateObjects` with that resolved name;
5. verify the created exact GUID and its object/GDL details.

Do not trust an arbitrary display name as durable identity.

## Pass 8 — AI can author source, but the compiler is the first gate

Proposed architecture:

`approved object specification -> optional AI generates/edits HSF/GDL -> static checks -> LP_XMLConverter -> compiler result -> library catalog fingerprint -> Tapir library load -> controlled CreateObjects probe -> exact-GUID readback`.

The AI never runs arbitrary shell strings. A deterministic compiler wrapper invokes one fixed `LP_XMLConverter.exe` path with validated argument paths.

Compilation failure stops before Archicad. This converts many geometry mistakes into an offline development failure rather than a live-model failure.

## Pass 9 — this can become a reusable parametric component factory

High-value candidates:

- furniture families with dimensional parameters;
- retail fixtures;
- kitchen/bathroom equipment;
- signage/wayfinding;
- facade accessories;
- equipment/fittings not covered by native MEP automation;
- reusable presentation objects;
- project-specific custom objects;
- parametric 2D/3D annotation objects when native Text/Label is insufficient.

For larger multi-element BIM assemblies (apartment/core/facade bay), Hotlink Modules are usually better because walls/slabs/openings keep native element semantics.

Decision rule:

- one logical parametric object -> GDL;
- repeated multi-element BIM assembly -> Hotlink `.mod`;
- native architectural system -> native Wall/Slab/Roof/Mesh/Zone/etc.

## Pass 10 — integration audit

### Can it be integrated?

**YES, as an offline content-generation subsystem plus certified Tapir placement.**

### Why it fits Safe BIM

- source can live in Git;
- compilation happens outside Archicad;
- stable Main GUID exists;
- Tapir can inspect/load/place library parts;
- exact placed element GUID can enter the normal receipt/readback system;
- no custom unsigned Safe BIM APX is required for this path.

### Required controls before production

1. Find/verify the actual Archicad 29 `LP_XMLConverter.exe` path on the user's machine.
2. Pin/record converter/Archicad version in generated-library metadata.
3. Keep HSF source under version control.
4. Enforce stable Main GUID policy; creating a new functional object requires a new Main ID.
5. Validate UTF-8/BOM/source requirements documented by Graphisoft.
6. Compile in a dedicated generated-output directory.
7. Never execute AI-provided command lines.
8. Preflight `GetAvailableLibraryParts`; fail on duplicate/ambiguous names or unexpected Main GUID.
9. Use exact placed element receipt and strict object/GDL readback.
10. Add one small generated-object live probe before enabling generic placement.

### Main unresolved items

- exact deterministic procedure for creating a brand-new HSF skeleton/Main ID without copying a known-good exemplar;
- which GDL static checks can run before `LP_XMLConverter`;
- strict readback subset for library Main GUID/revision + object parameters in Tapir;
- behavior of reload/replacement when an already-placed object keeps the same Main ID but receives a new Revision ID;
- performance cost of reload on large projects.

These should be researched before implementing an AI-driven general GDL generator.
