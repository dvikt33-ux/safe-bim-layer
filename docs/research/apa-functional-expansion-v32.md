# APA A11.S03 — functional expansion v3.2

Continues verified PR55 on the separate PR56 feature branch, using the existing BIM Graph, CP-SAT, Details archive, SceneWriter, SQLite journal and installed Tapir. Full Windows host validation: **403/403 PASS**, including 32 expansion tests. S03 remains PARTIAL because terminal/provider, full manufacturer and engineering requirements remain open.

## Native end-to-end result

After the user reopened Archicad, read-only recovery found 69 GUID: all 59 accepted baseline identities and bodies were unchanged, and two previous Create results were recovered. The failed historical Connect was absent. Neither old Create nor Connect intent was replayed. Two new journaled Modify operations moved only those additional routes into free space selected by existing CP-SAT. A distinct Connect in changed geometry created a native tee with all three physical ports connected. A new four-node route with two native elbows joined the branch to the accepted network. A further route was reconciled into a rectangular extension.

Dedicated native routing, system membership, reciprocal port position/size/direction and resultant bodies prove connectivity. Exact native MEP-to-architecture collision readback is empty. Explicit orthogonal polylines reuse CP-SAT through coordinate permutation; no new pathfinder was built. Actual fitting extents determine acceptance.

One native default terminal was created and independently read back. AC29 omits it from GetMEPElements. Typed creation, native type150/body and dedicated ports qualify a component; its exact subtype remains unverified. Its actual port is circular 0.2 m and offset from insertion. A requested circular 0.2 m route instead read back as 0.8 m from the native preference default. A new Modify intent reconciled that known result into the working rectangular extension, without Create retry. The terminal remains **open, outside the explicit routed graph**, and is returned in outsideRouteScopePhysicalGuids. Complete system scope remains the reader default; opt-in route scope always reports exclusions. This is not a terminal-connected complete HVAC system. Diameter preference/transition qualification needs a ready provider path; no APX/default-table change was made.

## Details to native source part

All **73 Details v2.12 context records** participate in source/fact/host/material joins and a bounded junction-family matrix for existing A04.S01-S03. ARMO page3 entityc4/factPF001 supplies the confirmed **25×150 mm** section. The measured planar roof supplies the **10 m** span, slope, home story and footprint. Fresh typed lookup selects actual project structural timber.

Existing BIM Graph/CreateMorphs and SceneWriter created one native source part. Live readback showed Tapir axis fields are placement-matrix **rows**. The adapter now verifies that contract and the compiler transposes the roof basis. A new in-place Modify corrected the already-created part. The middle candidate intersected the retained diagnostic Morph; a distinct placement intent selected a measured roof quarter-span. Final native vertices, closed BREP edges, timber material, story and logical roof/source binding match, with empty exact collision readback. All original bodies and the diagnostic object remain intact.

The guard reacquires source/archive, host geometry/material/story and project material before writing. Changed dimensions or placement invalidate the operation. Native-bound candidate screening is followed by exact collisions. This is an independent geometric part, not a complete assembly or native roof-child relationship. Eight required dimensions, manufacturer material approval and c5 rafter orientation remain missing. A04 tasks are not marked complete from a bounded matrix.

## Save, reopen and actual IFC

The authorized isolated PLN was saved and reopened once. Independent readback preserved **37 context records / 95 GUID**, all 95 resultant geometry signatures and the routed graph. All original48 and baseline59 identities/bodies remain intact. Persisted SHA256: dea93fe0fd520747bf4fee5f12d86372f57d972a7021b65029419d2d127892c8. A local journal column error occurred after successful native verification; read-only reconciliation marked persistence complete without repeating Save/Open.

A new actual IFC export was parsed with IfcOpenShell. **37/37 native world-bound mappings** match, including **7 physical route mappings** and the Opening host cut. Multi-member route fallback reads actual exported ducts. The file contains **44 elements, 19 material assignments, 39 classified elements, 26 owned ports, 11 port links and 6 Opening-host relations**. Twelve verified native/IFC area-and-volume comparisons match; zero verified comparisons mismatch. Source qsets are absent. The new timber proxy's closed IFC mesh measures **0.0375 m³** and **3.5075 m²**; native quantity comparison stays unverified because the dump marks its body curved. The terminal exports as IfcDistributionFlowElement, without qualified terminal subtype.

Quantities, source qsets, materials, classifications, hosts and port connectivity remain distinct. Full receiver semantics, loads, norms and calculation results are ENGINEERING_NOT_VERIFIED. Raw payloads, personal paths and PLN/IFC binaries stay local; selected publication evidence uses stable SHA tokens and hashes.

## Historical probe and continuation

The separately published first probe used insufficient space for the installed 1.5 m tee, produced a disconnected/overshooting branch and was not accepted. A general GDL query on unknown MEP timed out before isolated process closure; internal cause is unproven. That query is quarantined. Automatic approval review rejected a duplicate recovery launch; it never executed. The user reopened the correct project, enabling fresh identity/body checks and this successful continuation. Historical outcomes remain preserved.

G01 retains SQLite proof. G02 and G04 now have independently working native parts and a routed graph with contextual/terminal gaps. G05 retains Opening/SEO proof; Shell/edit contracts remain unavailable. S06-S09 preserve manufacturer, provider, SAM/SAF and receiver dependencies. Terminal diameter/transition is recorded separately without blocking independent Details/IFC work. S04 remains gated on real S03 completion. Main/master, other PLN and installed APX were not changed.
