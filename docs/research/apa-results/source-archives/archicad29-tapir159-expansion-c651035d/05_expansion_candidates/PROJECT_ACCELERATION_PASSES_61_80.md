# Project acceleration research — passes 61–80

Fifth acceleration round. Goal: expand functionality that directly reduces project-production time while keeping Safe BIM's exact-receipt/fail-closed model intact.

No live Archicad writes were performed.

## Pass 61 — MEP is already a real programmable subsystem, not a future placeholder

Tapir 1.5.9 exposes AC28+ MEP commands for listing/filtering MEP elements, reading routing elements, reading ports, distribution systems and preference tables, plus routing-element creation/modification/connectivity commands.

The MEP read model is rich enough to return route polyline, exact segment GUIDs, exact node GUIDs, cross-section sizes/shapes, MEP system, port position/direction and physical connections.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/MEPCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Examples/mep_elements.py

## Pass 62 — MEP belongs to `W5 MULTI_OBJECT_TOPOLOGY`

A routing element owns/creates routing segments and nodes, and connection operations can split/merge/create related MEP elements. This is not the same safety class as a single Wall create.

Future receipt design should persist at least:

- root routing-element GUID;
- requested route polyline/domain/system;
- reread exact segment GUID set and node GUID set;
- port topology/connectivity;
- any split/deleted/branch IDs returned by connection commands.

Conclusion: MEP can greatly expand functionality, but must not be enabled through the generic W1 primitive path.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/RFIX/Images/CommonSchemaDefinitions.json

## Pass 63 — MEP can eventually automate coordination, not just modeling

Because Tapir returns port positions/directions, physical-connection state and connected element/port IDs, Safe BIM can eventually verify continuity and connectivity rather than merely checking visual overlap.

Potential high-value use cases:

- duct/pipe/cable routing generation;
- connection QA;
- system/domain validation;
- clash-driven route repair proposals;
- MEP preference-table-based sizing.

This can eliminate substantial coordination routine, but requires a purpose-built topology verifier.

## Pass 64 — Keynotes can centralize project notes/spec references

Tapir 1.5.9 exposes Keynote tree reads and CRUD for Keynote folders/items, plus Keynote autotext tokens. Archicad 29 Keynotes are a hierarchical project documentation database with key/title/description/reference and support labels/autotext.

Automation opportunity:

`project specification data -> Keynote database -> labels/autotext -> legends`

This reduces repeated note editing across drawings.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/KeynoteCommands.cpp
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/072_Keynotes/072_Keynotes-1.htm

## Pass 65 — Archicad Issues can become the native QA backlog

Tapir Issue/Markup commands support creating/deleting/listing issues, comments, attaching exact elements to issues and reading elements attached to an issue.

This allows failed QA rules to produce navigable model issues instead of only log text:

`QA finding -> Issue GUID -> attach exact offending GUIDs -> comment/status`

That can shorten the feedback loop between automated checks and manual correction.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/IssueCommands.cpp
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Examples/issue_management.py

## Pass 66 — IFC IDs are useful interoperability handles, not ownership receipts

Tapir maps Archicad elements to/from IFC GlobalIds and exposes IFC type/properties/attributes.

Use cases:

- correlate external IFC QA/coordination findings back to Archicad exact elements;
- validate exported semantic classification;
- ingest external issue/coordination references.

Safe BIM ownership still uses its own exact returned Archicad GUID receipts. IFC IDs are an interoperability index, not proof that Safe BIM created an element.

Source:
https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/IFCCommands.cpp

## Pass 67 — Publisher should be the normal final-output engine

Tapir exposes Publisher Set discovery and `PublishPublisherSet`. Archicad Publisher stores reusable output sets and can republish with the same saved output properties.

Fast workflow:

`verified docs -> approved publisher set -> explicit publish node`

This avoids scripting every PDF/file output individually.

Sources:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp
- https://help.graphisoft.com/AC/29/INT/_AC29_Help/070_Documentation/070_Documentation-114.htm

## Pass 68 — manual Drawing update mode is useful during design churn

Archicad distinguishes automatic-update and manual-update placed Drawings. Automatic drawings update when the layout is activated/output and before publishing; manual drawings remain frozen until explicitly updated.

Project-speed implication:

- iterative MODEL phase can keep expensive drawing updates out of the critical loop;
- DOCS/PUBLISH phase explicitly updates only when needed.

This validates the earlier two-stage model/document architecture with native Archicad behavior.

Source:
https://help.graphisoft.com/AC/29/INT/_AC29_Help/070_Documentation/070_Documentation-92.htm

## Pass 69 — Hotlink update/relink is powerful but must not be a hidden automation

Graphisoft documentation confirms a changed source can update all placed module instances. However, Hotlink relink/update operations can have major global consequences; relink can clear the whole Undo queue, and differing story structures can cause dimensions/labels to be lost.

Policy:

- normal automation places versioned known module instances;
- source replacement/update/relink is a high-risk project-global operation with explicit approval;
- module catalog should prefer immutable/versioned source paths instead of silently replacing a source behind existing instances.

Source:
https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-60.htm

## Pass 70 — Hotlink modules are officially intended for repeated rooms/building structures

Graphisoft explicitly describes Hotlink Modules as suitable for repetitive building structures such as hotels/offices with identical rooms, with one source change updating all instances and reuse across projects.

This independently confirms that the Hotlink Module catalog is not a workaround; it is one of the highest-value native acceleration mechanisms for repeated architectural assemblies.

Source:
https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-56.htm

## Pass 71 — TPL/seed projects are the fastest standards bootstrap

Archicad TPL templates contain project preferences/settings, placed elements and tool defaults. They can also contain the project structure and IFC translator settings.

Therefore Safe BIM should not reconstruct an entire office/project standard from API calls for every new project when a controlled TPL/seed PLN already contains it.

Preferred flow:

`known TPL/seed -> verify profile fingerprint -> generate project-specific content`

Source:
https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-28.htm

## Pass 72 — Favorite portability needs dependency verification

Archicad can import Favorites from PLN/PLA/TPL as well as PRF/XML. Graphisoft specifically recommends using a project source rather than old-version PRF/XML when migrating versions.

Favorite names alone are not enough as a portable contract.

Project Profile should bind a Favorite role to:

- element type;
- name;
- critical dependencies/resources;
- expected library/profile/material context;
- optional source-template identity/version.

Source:
https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-64.htm

## Pass 73 — a Favorite with missing GDL content cannot be applied

Graphisoft documentation explicitly says a Favorite containing a missing GDL object remains visible but cannot be applied.

Preflight must therefore validate Favorite dependencies before the geometry phase. Detecting only `favoriteName exists` is insufficient.

Source:
https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-62.htm

## Pass 74 — library preflight becomes even more important with AC28+ Global Library

Archicad 29 uses the Global Library/package model introduced in AC28, with additional linked/embedded libraries possible.

A canonical project environment fingerprint should include loaded library/package availability before any Favorite/Object/Window/Door-dependent recipe starts.

Source:
https://help.graphisoft.com/AC/29/INT/_AC29_Help/020_Configuration/020_Configuration-41.htm

## Pass 75 — Keynotes + Autotext should replace copied annotation text

Keynote data is centrally stored, and Archicad exposes Keynote autotext tokens that can be embedded in labels/text.

Preferred documentation compiler behavior:

- create/update Keynote item once;
- place labels referencing Keynote/autotext;
- never replicate the same note text independently on many views.

This reduces annotation drift and correction time.

## Pass 76 — native Issues should be generated only from verified QA findings

The native Issue system is attractive, but creating one issue per transient warning would create noise.

Proposed rule:

`deterministic QA failure + exact offending GUID set + severity policy -> create/update native Issue`

Informational/temporary planner diagnostics remain outside Archicad. This keeps the native issue list actionable.

## Pass 77 — broad READ capability + narrow certified WRITE capability is the right scaling model

Tapir/official schemas expose a very broad surface, and public MCP tooling demonstrates progressive discovery across 191+ commands.

Safe BIM should scale asymmetrically:

- read-only catalog/query/QA commands can be integrated quickly behind schema validation;
- mutation commands require operation-specific certification by risk class;
- the AI/planner can discover reads broadly but sees only certified mutation recipes.

This maximizes functionality without turning every upstream command into a trusted write primitive.

Source:
https://github.com/SzamosiMate/tapir-archicad-MCP

## Pass 78 — generated wrappers should be rebuilt from a pinned schema snapshot

A code-generation step can mechanically produce request/response DTOs, schema validators, command metadata and read-only adapters from the pinned Tapir/official schemas.

Hand-written code should focus on the parts automation cannot infer mechanically:

- absolute/relative coordinate semantics;
- ownership and result identity;
- reconciliation;
- project/global side-effect classification;
- operation-specific strict verification.

This reduces development time and schema drift.

## Pass 79 — phase snapshots improve deterministic resume without over-saving PLN

At major DAG boundaries, persist a compact runtime snapshot independent of the PLN save frequency:

- project identity;
- profile hash;
- Tapir/schema version;
- story fingerprint;
- resource/catalog fingerprint;
- verified receipt set;
- dirty dependency set;
- documentation/publish phase state.

This makes resume deterministic while avoiding a costly Archicad Save after every element.

## Pass 80 — schedule for throughput: parallelize planning, serialize uncertain mutation

The highest-confidence scheduling pattern is:

- parallelize offline geometry math, recipe compilation, source/schema validation, file preparation and read-only postprocessing;
- serialize physical BIM mutations through one runtime lease;
- batch filtered readback where dependencies allow;
- keep local AI unloaded during physical write/reconcile windows;
- run expensive documentation/publish work only at phase boundaries.

This uses CPU/resources aggressively where failure is cheap and stays conservative where a lost transport response can create unknown BIM state.

# Audit after passes 61–80

## New capabilities with direct productivity value

1. **MEP topology read/write surface** — large future functional expansion, but W5 safety class.
2. **Keynote database automation** — central notes/spec references and autotext.
3. **Native Archicad Issues as actionable QA backlog**.
4. **IFC identity/type/property bridge** for external coordination.
5. **Publisher-set driven output** instead of custom per-file export logic.
6. **Manual drawing-update strategy** to keep design iterations fast.
7. **Versioned Hotlink module sources** rather than hidden source replacement.
8. **TPL/seed-first project startup** with profile verification.
9. **Favorite dependency preflight** rather than name-only checks.
10. **Generated read integration + narrow certified writes** as the scalable architecture.

## Important failure-reduction findings

- Hotlink update/relink is not a normal low-risk element edit.
- Favorite existence does not imply Favorite usability if library content is missing.
- Team/project standards should be verified before model generation, not discovered during it.
- MEP must use topology receipts, not generic element receipts.
- Publisher and Drawing update behavior belongs to an explicit downstream phase.
- Broad functionality should be obtained by expanding reads and recipes faster than raw write permissions.

## Remaining gaps that justify another focused pass set

1. Define a concrete Project Profile JSON schema with resource fingerprints and compatibility rules.
2. Define module-source versioning/hash policy and hotlink update/relink governance.
3. Define native Issue dedup/update policy so repeated QA runs do not duplicate issues.
4. Define Keynote identity/update policy by GUID/key and import/export interaction.
5. Define MEP root/subelement/topology receipt format before any write probe.
6. Define documentation invalidation rules command-by-command.
7. Benchmark phase scheduling/read batches/AI unload on the user's machine.
8. Turn broad upstream command inventory into a machine-readable capability registry.
9. Decide which global operations must require explicit human approval every time.
10. Run a new prefinal architecture audit after these contracts are drafted.
