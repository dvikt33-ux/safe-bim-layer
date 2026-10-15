# APA native architectural documentation package

Working end-to-end adapter on the exact PR68 head: existing SceneWriter + SQLite journal + Native Model Dump produce a shared version of native floor-plan data, rebuilt native section/projection databases and six CSV specifications. No second drawing engine or executor. Normative and GitHub-search development excluded.

## Actual live result

- One floor0 native associative saved plan; one newly created native Section; one native InteriorElevation used as an exterior projection, with explicitly limited coverage. Four explicit saved ViewMap entries. Reused true exterior Elevation is empty for the selected building: NOT_VERIFIED as a facade.
- Selected19 primary elements:9 Walls,2 Slabs,2 Columns,4 Windows,1 Door,1 Roof. Six specifications share one modelVersion. Wall/Slab quantities come from actual resultant planar BREP, not box volumes. Bodyless Column parents and unsupported Door quantities remain unverified.
- New separate native Wall changed height1.0 to1.2m: actual joined volume0.085 to0.102m3; native plan cut fills15 to16. Existing Column plan join changed while its physical3D signature remained unchanged. Explicit refresh regenerated section/projection and independently read native owner links; this does not prove full vertical drawn coordinates.
- Save/Open and final independent readback PASS. Original109 GUIDs/geometry/materials/stories unchanged. Full inventory121 includes new Wall, Section/InteriorElevation and9 native subordinate/marker Objects. Persistence protected112 explicit identities, plus ViewMap/database checks. No new Wall volume collision. No Morph created.

## Acceptance boundaries

Native Section contains16 selected owners; exterior InteriorElevation projection contains4 selected owners (Column/Door/Wall/Window). No claim of a complete facade, native interactive schedule rows, vertical2D coordinates, rendered/visible UI acceptance or published PDF. Existing schedule tree/publisher names are discovery only. Refresh is explicit, not a background watcher. Damaged display labels from Native Model Dump are not promoted; numeric stories and attribute identities are retained. Normative/engineering acceptance NOT_EXECUTED.

Historical ambiguous ledger events are preserved. Initial Section APIERR_BADDATABASE was independently reconciled as no effect; corrected database-bound scenario then succeeded. Successful test Wall modification had a strict readback-field mismatch and was independently reconciled without repeating Modify. Save/Open succeeded and final public adapter refresh ran sequentially after Open.

## Verification and continuation

14 new tests;587/587 Windows host and Windows/Linux CI PASS. Six code blobs match GitHub. New draft PR70 is based on the exact PR68 commit29aa06a6e9bbef0d991bea922e1ad4101ab29bdd. Native identity tokens are hashed; raw requests/responses, model paths and PLN stay local.

A11.S03 remains PARTIAL; A07.S01 not closed and dependencies preserved. A11.S10 remains BLOCKED. Next: qualify true exterior Elevation placement, vertical primitive readback and native schedule row contracts through the same executor; then publisher output with actual file readback. No repeat of the completed normative/geometry work.

Publication safety flags describe only the publisher process (zero native calls). The preceding authorized isolated test PLN was modified and saved; this is explicitly recorded in native-readback.json.

Code: [draft PR70](https://github.com/dvikt33-ux/safe-bim-layer/pull/70), head `f5aa4754a0ace251e8541001f17f6fa8eddfe8e5`. CI: [Windows/Linux](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38323722458). Evidence: [APA-RUN-20261012-235115Z-bim-documentation](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010/docs/research/apa-results/native/APA-RUN-20261012-235115Z-bim-documentation).
