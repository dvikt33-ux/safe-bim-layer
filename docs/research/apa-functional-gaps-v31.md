# Functional gap package over PR54

This package continues the accepted core through the existing native context,
Model Dump, NetworkX/Shapely, CP-SAT, BIM Graph and SceneWriter. It adds source
joins and independent observations, rather than another executor or tracer.

`archicad_details_context.py` checks the pinned v2.12 archive and source PDF
hash/page/fact joins for all73Porotherm context records, evaluates each native
wall's geometry/material/product context, and exchanges a detached detail/host
record. Candidate AABB proximity is explicitly weaker than exact joint
geometry. Existing RC walls do not become Porotherm by inference. Each source
compile gate survives independently. The selected ARMO adapter still reports
eight missing required dimension entities and source commit=false.

`archicad_native_mep_network.py` combines dedicated routing node/segment GUIDs,
native distribution membership and actual reciprocal physical-port references.
Coincident ports alone do not prove connectivity. The existing connected CLI
now accepts multiple routes in one pinned native system. On the authorized
isolated scenario a CP-SAT-selected1m extension connected automatically to the
accepted6m duct: two routes, two segments, four routing nodes, two physical
ducts, one reciprocal native join. Both original endpoints/GUIDs survive. Two
outer ports remain open; terminal equipment and engineering approval are not
claimed. A redundant ConnectMEPElements would risk merging ownership, so the
adapter returns ALREADY_NATIVE_CONNECTED without another write.

The shared SceneWriter gains opt-in, schema/hash/journal-bound native operations
for Opening/SEO and MEP connection/modification. Each intent reserves a durable
step before one dispatch and independently reads native state; uncertain
outcomes never replay. A wall verifier now correctly checks omitted offset and
arcAngle defaults against native zero instead of failing after creation.

The live package creates a separate2×2×0.3m diagnostic wall, one0.4×0.6m Generic
Opening and two explicit closed Morph specimens. Hosting is independently
queried; both actual inner face contours prove X64.8..65.2m,Z1..1.6m and the
0.3m host penetration. SEO Subtraction reduces the2m target cube to X70..71m,
Y60..62m,Z0..2m while preserving target/operator GUIDs, native links and materials.
No original48GUID geometry changes. Three stopped verifications were reconciled
read-only (GUID casing, omitted Wall defaults, wrong verifier bounds shape);
their successful native operations were never repeated or hidden in history.

`archicad_functional_gaps.py --receipt <local-receipt.json> --output <new-dir>`
reuses the accepted22element native core and independently verifies the new
network, new primary identities, source applicability, Opening/SEO and native
duct-vs-core collision query. It reads only; the receipt includes actual source
plan, geometry signatures, inventory, identities and pre-operation bodies.
Freshly verify the allowed isolated project before using that receipt.

The saved/reopened model has27primary elements and59totalGUIDs. Opening creates
two native owned annotation objects as well as its own GUID; these are accounted
for. Save/Open preserve the complete inventory, geometry, links and port IDs.
PLN SHA256: `da37fa0fe9b1b255f1618a881a79eb9d4ae8b66993a99cb75fdba30cddc69bb4`.
The intentional existing Roof/Morph collision remains test calibration.

IFC2X3 export matches26whole native/physical element world bounds plus the
Opening's effective host-cut extents. Its standalone IFC cutter is0.9m deep,
while the actual wall penetration is0.3m; both bounds and0.3m overshoot are
retained explicitly. Matching uses the actual IfcRelVoidsElement host and the
intersection with that host's bounds. The exported network contains a real
IfcRelConnectsPorts relation. Native material assignments and structural data
are read from actual IFC entities. This export contains no analytical members,
analysis models or load groups; none are invented. Full IFC semantics,
quantities, face equality and engineering acceptance remain NOT_VERIFIED.

G01 is already repaired by PR54. G02's context adapter, bounded G04 network,
Opening/SEO subset ofG05 and G08 interpretation now work. Current provider
has no CreateShells/ModifyShells/ModifyOpenings contracts. Ready SDK source is
not an installed capability and the APX remains unchanged. Manufacturer source
dimensions, native SAM/SAF export/qualified mappings, licensed solver/approved
loads and remaining MCP/Twinmotion interfaces remain explicit dependencies.
S03 remains PARTIAL; S04 performance and the installer wait for acceptance.
