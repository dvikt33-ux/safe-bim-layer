# APA-P70.A11.S01 — working connected component package v3.1

The master v3.1 strategy is implemented as a compatible execution package over
the accepted native core. Existing Project Accelerator, authored native typed
readback, BIM Graph, SceneWriter/SQLite, Model Dump normalizer/topology, owned
ColumnSegments and Roof/Morph donor geometry helpers are reused. New thin
adapters share absolute metre XYZ, native GUID/story/material/host facts.
Donor standalone transports/deletions are never invoked. Optional roof/morph/
mep switches are independent; the original writer defaults remain unchanged.

Functional connections: selected Details v2.12 IR/entity/fact joins tied to a
native Roof; native Roof/Morph/single Ventilation route creation/readback;
explicit Morph body repair; actual physical-duct GUID ownership and port/system
readback; IfcOpenShell local IFC parsing/GUID/world-bound comparison; OR-Tools
CP-SAT candidate selection over actual native obstacles. All model writes use
the same durable SceneWriter ledger. No new scheduler, executor, own solid engine
or own pathfinder. The reusable CLI was tested through preflight and one actual
CreateMorphs with prior connected prefix retained.

## Native scenario and interaction

AC29 build5101 RUS / installed Tapir1.5.10 on the expressly authorized isolated
writer test model. Basic single-plane Roof: source upper-floor footprint
40..50/40..48m, pivotZ6m, thickness0.2m, slope0.15rad. Source-bound ARMO fact
25×150mm gives a2m project-length diagnostic Morph, with explicit project
material/placement. It intentionally overlaps the Roof for positive native
collision calibration; it is not an ARMO manufacturer assembly approval.

One Ventilation route between42,46,2.5 and48,46,2.5m has native nominal section
0.2×0.15m, pinned current system, one segment/two nodes/one physical duct and two
matching endpoint ports. Ports are physically unconnected; no full MEP network
claim. Generic GetDetails reports Unknown/nativeType150 and GetMEPElements
omits these current elements; dedicated native getters, physical BREP and exact
system/endpoint evidence provide bounded readback. Actual duct/flange envelope
is0.262×0.212m. CP-SAT uses it plus0.05m test clearance, selectsY46 among
Y42/44/46; Y44 is blocked by both native columns. Native selected polyline matches
the OPTIMAL candidate. Independent duct-vs18core native collision query returns
zero rows; Roof/Morph calibration independently returns hasBodyCollision=true.

The installed CreateMorphs size shortcut produced a5-face open surface despite
eight box vertices. It was refused. Read-only reconciliation kept its GUID,
then one distinct journaled ModifyMorphs body supplied the missing bottom face.
Actual BREP became6-face closed with verified edge incidence. The compiler now
expands size to explicit6-face body before graph validation/hash; a separate
0.1m diagnostic cube through the reusable CLI proved native creation of it.
Memo isClosed=false still disagrees with BREP.closed=true; this remains explicit
and is not silently promoted. Two diagnostic Morphs are retained as test evidence.

Total this integration:4nativeCreates and1explicitModifyMorphs, no blind retry,
plus separately journaled local Save/Open and IFC exports. Final model has
22primary/48total native GUIDs, while all original40 geometry/material/story/
host facts and the previously accepted selected GDL/library identities remain
intact. The CLI addition independently retained all47previous geometry records.
Final SaveProject and OpenProject each returned explicit success and all22
primaries/48GUIDs were independently re-read after each. An earlier15s Open
timeout was reconciled read-only after identity verification, never retried.
Latest saved/reopened PLN SHA256 `3164f8ea86c9df4491d4b66c852c6b247d6769faf857a5f3381867e3aa801f2d`; final bound plan
`b803ed3441168410d8337035b28f01e726c88f45db69d6fae83e82180c515c29`.

Final local IFC2X3 is parsed by IfcOpenShell0.8.5, length unit millimetres with
scale0.001. All22coordinated entries match actual native absolute metre world
bounds within1e-5m, including one explicitly mapped physical duct. The routing
container IFC identifier is absent from export; its physical IfcFlowSegment is
mapped by its own independently read native/IFC identity. This is identity and
world-bound verification, not full face/quantity/semantic or structural equivalence.

Details archive source SHA is checked; selected ARMO IR executes real joins
between entities and two parameter facts. Eight required entities still lack
dimension facts; source commit=false is preserved and blocks whole-assembly
compilation. The selected cross-section specimen does not override that gate.
Release has1142ordinary IR plus73Porotherm context records; the latter need a
separate adapter. Manufacturer assembly engineering remains NOT_VERIFIED.

## Code, tests and evidence

[Draft PR53](https://github.com/dvikt33-ux/safe-bim-layer/pull/53), stacked on draftPR51, head `286b1ae8614421b927af95c4c278147c8d55baba`. Ten allowlisted
code/test/workflow/document files; new additions scanned for private paths and
secrets. [Linux CI38189925845](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38189925845) passes all340tests,
schema/graph contracts and PowerShell syntax.24new focused tests and11retained
SceneWriter tests pass locally. Full Windows discovery ran340tests with28
historical SQLite temporary-directory cleanup errors; Windows full PASS is not
claimed. Current model/interface code was replayed against final captured native
responses and local IFC; publication action makes zero live Archicad calls or
PLN writes. Earlier actual native mutations are documented separately above.

[Selected acceptance](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/native/APA-RUN-20261012-010000Z-compatible-integration-v31/acceptance.json),
[scoped native/IFC/Details/solver proof](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010/docs/research/apa-results/native/APA-RUN-20261012-010000Z-compatible-integration-v31),
[checksums](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/native/APA-RUN-20261012-010000Z-compatible-integration-v31/EVIDENCE_SHA256.json).
Full88raw files stay unchanged in a local archive. Only7selected proof files
plus manifest are published. No PLN/IFC/GSM/LCF/image, filesystem paths, full
catalogs, unrelated baseline payload, original native GUIDs or original IFC IDs
are exported. Public model identities are consistently SHA-tokenized. This is
a privacy-reduced selected proof, not a complete raw project export. Observed
small-model timings are recorded; no large-model speedup is claimed.

## Remaining gaps and next package

Shell creation, generic Opening typed readback and SEO execution were not run.
SAM/SAF solver handoff remains source-only. Details whole assemblies and73context
records need adapters/explicit missing parameters. One straight route is not a
connected/branched MEP network; endpoint ports remain unconnected. Normative
engineering, visible UI, large-model performance and installer remain unverified.
Earlier material/GDL/core functions are retained. Source71/current263command
schema were reused; research-only interfaces are not presented as working code.

This completes A11.S01's bounded compatible-component package acceptance.
Next: A11.S02 shared-system acceptance, documenting actual module gaps before
gap-driven A11.S03 work. Core acceptance is preserved; main/APX/earlier tested
branches and original LCF are unchanged. No paid service or delegated agent.
