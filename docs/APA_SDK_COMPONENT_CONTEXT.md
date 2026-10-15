# Native component, envelope and Drawing integration

Exact PR94 base: `d758957f97cf1e347262da6f7e7b325ae6609ea4`. A11.S03 remains PARTIAL.

Existing hierarchical membership, element GDL parameters, material attributes, Navigator and ViewMap contracts are reused. Three new grouped read contracts add component parent/root and missing Stair/Railing/CurtainWall scalar parameters; modern AC29 Opening cut/host relationships and extrusion frames; and quantity pre-engine identity diagnostics without an engine call. Existing envelope query adds indexed trims, side surface overrides, bounded pivot-level overrides and Shell base plane. Existing Drawing query accepts an explicit database ID, runs the native status/content-box calls in that database through the existing context helper, restores it and reports restoration failure.

The same dynamic catalog provides lazy schemas. Native calls retain the existing read dispatcher; mutations retain SceneWriter and SQLite. A small relationship converter feeds the existing DependencyImpact operation through BIM Graph. It creates no executor, graph store or search subsystem. Parent/root edges and cut/host relationships are not physical contact or engineering acceptance.

385 preparable = 375 native/source + 10 existing local operations. Original runtime remains337 compatible contracts; exact tested candidate has288 add-on registrations +73 official compatible contracts =361.73 is compatibility, not73 live calls. Source-only relative to original:38; candidate lacks14 catalog entries. Quantity command remains discoverable but execution is quarantined in Python and C++. No new executor, journal, KG or engine.

Full Release candidate `4074a1926ec1b18ab89f2052e8309c62667aa170a836be8e70a2c90b945665e1`, compiled implementation `0c1c92548339d1389e68ec54ac1d870f7d706a49`, was installed with explicit user permission. Runtime build identity, registration, five actual exported input schemas and typed results matched. Five grouped reads are CALLABLE_VERIFIED: three new groups plus two enhanced existing groups. Scope-specific native facts:

- 86 Stair child records: native parent/root/declared owner agree with the independent existing membership query; native story matches all86 baseline rows. Riser/Tread/Structure parameters read without invoking a solver.
- 7 Roof/Slab memos: side overrides, edge trims and bounded pivot levels read. PolyRoof exposes5 raw memo slots representing4 unique pivot edges; closing slot is retained rather than counted as another physical edge. Shell remains unverified without a sample.
- 4 distinct Drawings: explicit owning Layout database fixed the previous native auxiliary errors. Status and full content box returned NoError for all4; context restored. Native updateStatus=-1 for all4 means “other”; up-to-date is NOT_VERIFIED. Only1 source link resolves in the captured public ViewMap, so3 unresolved links are not invented dependencies.
- 3 existing Wall/Slab hosts: modern connected-Opening query returns empty sets successfully. Positive Generic Opening cuts/extrusion remain NOT_VERIFIED because there is no sample.
- 1 pre-engine diagnostic reads type/identity successfully. Quantity engine is never called; no crash batch replay.

Captured new native replies feed the existing BIM Graph→DependencyImpact:96 nodes,87 verified dependency edges,42 entries in the selected Stair impact set. Existing membership alone also verified88 nodes/86 edges. No physical contact, resultant BREP or engineering acceptance inferred.

All258 original GUIDs and serialized native parameter rows matched before/after reads; saved PLN bytes unchanged across this cycle. Original APX SHA and Include registration restored. Read-only reopening with the original runtime is recorded separately in runtime evidence. No model-write API or Save was invoked. Build/raw evidence stays private; only hashes, counts, scalar facts and processed diagnostics are published.

Five focused changed-contract checks passed; independent PR95 160/160 audit is reused, not rerun. Windows CI and final exact-head publication/readback are recorded with the publication package. A11.S03 remains PARTIAL; no historical DONE is rewritten.


## Source reuse and next gaps for independent audit

| Source | Current gap / practical benefit | Dependencies | Effort / runtime / risk | Duplication check |
| --- | --- | --- | --- | --- |
| AC29 hierarchical editing + existing Tapir membership | Parent/root and Stair child parameters now integrated; Railing/CW subset awaits an existing live sample | Current grouped reader and membership contract | Implemented; new exact candidate live read required; no solver | Membership enumeration and existing CW frame geometry retained |
| AC29 Opening modern API | Host/cut/extrusion frames now integrated; positive Generic Opening sample still needed | Existing explicit authorized Opening sample | Small follow-up; native sample required; read only | Existing ModelDump host-only field retained; new query supplies cut set and frame |
| Existing envelope memo + AC29 Shell class structures | Shell bodyFlags/class axes and contour-edge details still omitted | Existing memo allocation checks, class-specific frame semantics | Small/medium; actual Shell sample needed; no write | No new geometry kernel or BREP claim |
| AC29 Drawing API + existing LayoutBook context | Status/content-box read in correct owning database; verify native errors and restore | Existing layout IDs, actual Drawing GUID, ViewMap | Implemented context wrapper; native verification required | Navigator/Layout helper reused; no updater/controller |
| AC29 LibraryPart_GetParams | Optional library-part default parameters without a placed instance | Existing GDL serializer and library identity | Small adapter only if useful; native library sample; handle lifecycle review | GetGDLParametersOfElements already reads placed instances, so do not wrap again |
| Existing API Quantities + official Element_Test/Plan_Dump examples | Identify failing type and safe ownership/mask contract before any future engine retest | Separate qualified diagnostic context and exact permission | Diagnostic stage implemented; engine remains blocked; high risk | Current BREP-based quantities retained; no duplicate calculation engine |

These proposals are review inputs, not automatically appended task IDs or a new roadmap.32 other APX provider records and thirteen unintegrated DevKit examples remain inherited evidence; no private ABI or licensing bypass was attempted. Native model writes still use the one SceneWriter; this package only adds reads and captured-data conversion. Source/code availability never grants execution permission on an arbitrary PLN.
