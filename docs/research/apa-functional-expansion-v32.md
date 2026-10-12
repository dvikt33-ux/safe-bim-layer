# APA A11.S03 — functional expansion v3.2

Continues verified PR55 `3191e7ce5071e6de7401f6e520fbd8f3ef2a1ea2` on a new feature branch. The accepted core and single SceneWriter remain in use. The canonical roadmap's current section was corrected from historical316/18/40 to371tests/27primary/59GUID before this package.

## Working independent IFC path

`archicad_connected_ifc.inspect_quantified_exchange` reads the actual retained IFC and shares its GUID map with the freshly captured native59baseline. It returns actual material names/layers, classifications, source quantity sets, measured IFC mesh area/closed volume, planar native BREP quantities including face holes, Opening hosts, port ownership and port/element connections. Measured quantities remain separate from absent source qsets. Open, curved or unverifiable bodies retain explicit gaps. No loads, structural calculations or receiver semantics are invented.

The real saved IFC has32elements,18material assignments,27classified elements,4owned ports,1port connection and6Opening-host relations.12native/IFC area-and-volume comparisons match;0verified comparisons mismatch. Source quantity sets are absent. This is actual file processing, zero new Archicad writes, and is not post-crash live acceptance. A read-only CLI accepts `--ifc`, optional `--native`/`--native-map` and a new `--output` path.

## Details to the retained executor

All73v2.12context records feed a bounded model-derived junction matrix for the existing A04.S01-S03 tasks. Detail families retain exact source IDs, qualified/unqualified hosts and original compile blockers. A new bounded source-section compiler joins ARMO page3 entityc4/factPF001 to an actual planar roof:25×150mm source section,10m model-derived span, slope-derived axes, native story and explicit project material selection. It returns the existing validated BIM Graph/CreateMorphs recipe and SceneWriter plan.

The native adapter checks source fact/archive, host geometry/story/materials, exact placement and fresh typed project material resolution before writing. Changed geometry, source dimensions or placement invalidate the operation. This is an independent geometric-part recipe;8missing assembly dimensions, manufacturer material suitability and engineering acceptance remain unresolved. No new source-section part was written in this cycle because native recovery stopped. The prepared reference material is explicitly not a manufacturer-approved timber selection. c5is rejected without an actual rafter/orientation binding.

## MEP observations and fixes

The dedicated reader now handles multiple disconnected distribution-component rows sharing one system attribute. Reciprocal peer position/section/direction are checked directly; different-position links cannot become false PASS. Collinear physical-port segments map trimmed ducts to logical polylines, while overshooting ducts remain unmapped. Branch observations use actual native fitting bodies and conservative architectural AABB screens, separately from exact collision checks. The terminal/equipment CreateMEPElements adapter is explicit opt-in and remains OFFLINE/SOURCE scope; no terminal was created or connected.

Native probe: CP-SAT rejected an endpoint at x=52m crossing the east wall before any write. A shorter new trunk/branch was created through the existing writer, then a distinct Connect operation on those new routes created a native tee and split route. Captured state:5routes/5segments/6physical members/75GUID, all59baselineGUID/geometries preserved. The installed tee default spans1.5m and exceeds the bounded available space: only2of3ports connect, the new split duct overshoots its logical route, and the tee AABB intersects the east wall. The network is disconnected and NOT_ACCEPTED. No blind Create/Connect retry occurred.

An attempted read of the new MEP fitting's GDL parameters timed out and the isolated Archicad process subsequently closed; Bug Reporter confirmed an unexpected closure. The adapter now rejects unknown native types before a general GDL-parameter read and uses dedicated MEP APIs. The installed APX was not changed. Temporal association is observed; the crash's internal cause is not proven.

## Persistence and continuation

The on-disk PLN remains the last accepted27primary/59GUID revision, SHA256 `da37fa0fe9b1b255f1618a881a79eb9d4ae8b66993a99cb75fdba30cddc69bb4`. New native probe changes were not saved or reopened and must not be counted as persistent functionality. Original journal outcomes/raw captures remain local; source/publication evidence separates failed native probe, working actual IFC processing and offline Details preparation.

An exact-PLN recovery launch did not expose a usable working window/API. A second visible launch was rejected by automatic approval review due to concurrent lock/recovery conflicts. No workaround or duplicate launch followed. Native continuation requires settling that test instance, reacquiring exact project/process/port/Tapir identity and all59GUID/geometries, and choosing branch geometry large enough for actual native fitting extents before a fresh, non-replayed intent. Then qualify a terminal and a project material for the independent source part, save/reopen and verify the resulting native network/parts.

A11.S03 remains PARTIAL; A04.S01-S03 are not declared complete from a bounded matrix/graph. S06-S09 retain source/provider/SAM/receiver dependencies. S04 optimization is not entered; the measured baseline/file processing timings are evidence only. Main/master, other PLN and installed APX were not modified.
