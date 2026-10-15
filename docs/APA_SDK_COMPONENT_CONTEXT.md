# Native component, envelope and Drawing integration

Exact PR94 base: `d758957f97cf1e347262da6f7e7b325ae6609ea4`. A11.S03 remains PARTIAL.

Existing hierarchical membership, element GDL parameters, material attributes, Navigator and ViewMap contracts are reused. Three new grouped read contracts add component parent/root and missing Stair/Railing/CurtainWall scalar parameters; modern AC29 Opening cut/host relationships and extrusion frames; and quantity pre-engine identity diagnostics without an engine call. Existing envelope query adds indexed trims, side surface overrides, bounded pivot-level overrides and Shell base plane. Existing Drawing query accepts an explicit database ID, runs the native status/content-box calls in that database through the existing context helper, restores it and reports restoration failure.

The same dynamic catalog provides lazy schemas. Native calls retain the existing read dispatcher; mutations retain SceneWriter and SQLite. A small relationship converter feeds the existing DependencyImpact operation through BIM Graph. It creates no executor, graph store or search subsystem. Parent/root edges and cut/host relationships are not physical contact or engineering acceptance.

Status at initial publication: 385 preparable = 375 native/source + 10 existing local operations; three new SDK groups source-only until an exact compiled candidate is installed and read back. Original runtime remains 337 compatible contracts; the PR94 tested prototype had 358. Quantity execution remains quarantined in Python and C++. Independent PR95 160/160 audit is reused, not rerun. Four focused changed-contract checks passed locally.

Existing authorized test model identity and all258 GUID/native serialized parameter rows matched the accepted baseline on read-only inspection. Existing native membership returned two Stair groups; no model mutations, APX replacement or new project creation occurred during this initial checkpoint. Full Release candidate and precise new-binary runtime permission are pending. No LIVE_PASS for the new commands.
