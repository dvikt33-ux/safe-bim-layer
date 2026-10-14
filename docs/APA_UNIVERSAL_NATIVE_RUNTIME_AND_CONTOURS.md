# Runtime identity and authored floor contours

This package extends the existing orchestrator, BIM Graph, SceneWriter and SQLite
journal. No additional generator, transaction mechanism or controller is added.

## Runtime qualification

The existing SDK overlay builder now stamps a SHA256 identity over the actual
copied C++ and resource snapshot. `GetAPARuntimeInfoV1` exposes that identity,
the source revision, SDK major and the real shared MDID. Fresh schema export
pins the response; the SDK Grid/Stair adapters compare it again before dispatch.
A shared Tapir version string cannot qualify a different binary. Legacy stock
commands remain independently available through their established contracts.

For deployment, record the actual process module path and file SHA, compare them
with the built APX receipt, read the embedded identity and fresh command export,
then allow only matching commands. An installed file hash alone does not prove
which binary the running process loaded. The installed and external Tapir share
an MDID and must not be loaded together. Keep one selected registration, close
Archicad before any authorized replacement, preserve the old file/registration,
and read back their restored bytes. Existing single-file deployment helpers and
receipts are reused. This package grants no installation permission.

## Stair crash boundary

The previous exact adapter reused the stock `CreateStairs` setter, which
explicitly clears baseline edge/vertex arrays because `Element_Create` derives
them. It then called `SolveStair` before creation, while the walking-line memo
still described the old Stair. These are concrete unqualified inputs; they are
not a proved faulting instruction or a confirmed root cause of the process exit.

The new candidate checks coordinate/ending capacities, contour/arc counts and
edge/vertex buffers before the solver. Missing buffers return
`NativeStairMemoUnqualified_NoSolver_NoCreate` with memory-layout diagnostics.
No arbitrary metadata, walking line, rule override or guessed geometry is
generated to bypass the gate. Native readback also exposes the actual base-plane
frame, local baseline and transformed world XY baseline. This is a safer
diagnostic candidate, not a claim of exact Stair creation LIVE_PASS. A different
candidate requires separate deployment approval and controlled qualification;
the original terminating request is not repeated.

## Source contours and targeted edits

The current `building-shell-v1` primitive accepts explicit `floorPlans` instead
of generating rectangular floors. Each record supplies a stable ID, the actual
story binding, thickness, outer polygon and all holes. The ordinary main
orchestrator compiles these into the existing native `CreateSlabs` graph and
SceneWriter. No walls or extra building are invented when only floorplates were
requested. Different records can have different contours and elevations.

The authored whole-model route accepts the same per-story contours. Existing
Shapely validation rejects self crossings, touching/overlapping/outside holes,
walls over voids and rooms over voids. All configured stories need explicit
contours; no missing contour or dimension is guessed. Engineering acceptance
remains separate.

`prepare_model_parameter_edit` uses the original source graph and native GUIDs
to emit only affected edits. A slab contour/hole change produces `ModifySlabs`
with **polygonOutline and holes together**; the runtime contract removes holes
when replacing the outline without resending them. No Create or whole-model
rebuild follows from a parameter edit. The existing owned-element/retained-GUID
gate, identity checks, current saved hash and SQLite intents remain mandatory.

Independent verification checks every native hole rather than only the outer
outline. For explicit source holes, actual native top-face contours must match
the full expected footprint and voids. Bounding boxes or logical links cannot
substitute for this physical geometry check.

## Live-model preflight issue

The existing universal bounding-box query returns empty sentinel extents for
hidden Stair Tread/Riser children. The scan now requires a slot-complete native
dump, no actual body, a true Stair owner, and matching specialized native
membership before recording those bodyless children. It continues checking
the real parent/structure geometry and refuses unknown ownership or actual
collisions. Bodyless children are not mislabeled as 2D annotations.

## Validation boundaries

Windows SDK build, offline tests, original-runtime readback and newly authorized
model changes are separate evidence classes. The supplemental original-runtime
readback preserved all144 GUID and original143 geometry/material/story signatures.
The new candidate is not installed by this package. The existing test PLN is
the sole native target; the separate168-GUID project and TRC are excluded.

The bounded next live scenario uses one explicitly test-sized L-shaped Slab,
its true opening, a contour/hole edit with the same GUID, then Save/Open and
independent BREP readback. It requires separate user authorization before any
write. No roof, normative, search or documentation subsystem is rewritten.
