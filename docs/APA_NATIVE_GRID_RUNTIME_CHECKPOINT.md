# True Grid runtime checkpoint

The existing SceneWriter created one genuine editable Archicad Grid Element,
edited its placement with the same GUID, and saved/reopened the existing
authorized test project. Both repeated ownership checks made zero Create calls.
The original 143 GUID and geometry/material/story signatures remained unchanged;
the saved inventory is 144. This is native CRUD/persistence LIVE_PASS, not a
large-model performance test. The exact rendered axis span remains NOT_VERIFIED:
the native model dump exposes marker bodies, not the complete GDL wire graphics.

The loaded candidate was identified by its SHA256 and actual process module,
not the shared Tapir version. Grid has Object type 6 and GREL variation
0x4752454c; this distinguishes it from a Generic Object. Its library defaults
were read before creation, and default settings were preserved. No Morph or
visual replacement was used.

## Existing orchestrator and graph integration

Use `prepare_axis` with a mapping qualified against the freshly read Grid
defaults, then `apply_native_axis_grid` through the existing main orchestrator.
Use `edit_axis` for owned placement changes. For this loaded library,
`synchronize_native_axis_geometry` runs the existing native
`SetGDLParametersOfElements` parameter script on only the owned Grid. It updates
the BIM Graph operation, semantic coordinate, source hash and native GUID binding.
The generic parameter editor is not enabled for other elements.

`Object.angle` and `AC_Angle` are distinct fields. The Grid SDK memo uses radians;
the installed GDL ChangeAParameter path consumes degrees. The live correction
sent 90 degrees and read 1.570796327 radians. An earlier radians-as-degrees
attempt was recorded UNKNOWN_OUTCOME after a mismatched readback. Independent
reading reconciled its actual result; a separate corrective intent passed.
No historical unknown receipt was erased or replayed.

A placement drift observed during UI inspection was independently reconciled
on the newly owned Grid only. Its cause remains NOT_VERIFIED. All retained
elements were checked before the corrective placement operation.

## Exact Stair runtime blocker

One detached native solver request for 3.3 m height, 22 risers of 0.15 m and
0.35 m going ended in connection reset; the Archicad process disappeared.
The saved project bytes remained unchanged. No new Stair Create or accepted
Stair Modify was sent. Favourite rule compatibility is not native acceptance.
The terminating module/cause is NOT_VERIFIED; no blind solver retry is permitted.

New exact Stair writes now require a hash-pinned detached result bound to the
requested dimensions, Favourite bytes, target project, saved model, retained
signatures and current schema. Failed, missing or stale probes are denied.
The known terminating candidate cannot qualify itself. Completed verified
SQLite results still reuse their GUID without another solver or Create.
Existing native Stair baseline readback is local while requests use world
coordinates; the old reader lacks a qualified base-plane transform. No guessed
transform or hidden size correction is accepted.

The next step is to fix/qualify detached SDK memo preparation and expose the
native base-plane frame in a new candidate, then validate a detached result
before any exact Stair write. Installation of a different APX requires separate
authorization. Roof contour/slope work follows this native checkpoint.

The original APX and its registration are restored. The candidate's additional
runtime commands therefore are not claimed to remain installed. A11.S03 stays
PARTIAL; source dimensions and engineering suitability of the new Stair remain
NOT_VERIFIED. Normative, Knowledge Graph/search, documentation and TRC code are
outside this cycle. CI now runs on Windows only as explicitly requested;
historical Windows/Linux results are preserved.
