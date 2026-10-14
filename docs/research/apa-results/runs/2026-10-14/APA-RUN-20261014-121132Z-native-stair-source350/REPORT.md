# Source-compatible native Stair:350mm going after Save/Open

[Draft PR81](https://github.com/dvikt33-ux/safe-bim-layer/pull/81), head `3221b8e7a0b775ece1018caf622a32c6ca9cb9dc`, exact parent PR80 `cb73cd578c7cd7577f80397920d9e81b8d09c6e1`. Main orchestrator used the existing read-only Knowledge Graph/GitHub plan and CAS claim revision154. No second generator, controller or executor.

## Working result

One new true native Stair was created through the existing SceneWriter/SQLite in the existing authorized test PLN. Explicit test parameters: height3.3m,22rises of150mm, going350mm, width1m, walking line7.7m. Current Favourite is source-hashed. The old20-rise Stair remains unchanged: its165mm rise plus350mm request gives2R+G680mm, above its own captured native maximum650mm. The new explicitly22-rise scenario gives650mm; no parameter was silently substituted and no global preference changed.

Independent built-in properties read going350mm, rise150mm, width1m and walking length7.7m. Actual native StairStructure BREP contains22horizontal levels;20regular successive front-edge pitches measure350mm, and21level differences150mm. The final structural top transition is 0.309807621m, separately NOT_VERIFIED as a default-going measure. Union surface spans are not substituted for tread going. Surface attribute readback is Бетон -04; this is not a structural BuildingMaterial or engineering acceptance.

SaveProject/OpenProject through the same journal and a separate independent read confirm all255 inventory signatures and the previous145 geometry/material/story signatures unchanged. Native collision query against retained physical elements returned0pairs. Saved-file SHA256 `01f47ad21aa5aa6975d824cf9999b56b7e89578ce1baa7e4b594ab49bc22b59e`. One Create, no Create replay, no deletion, no newPLN/APX change. Existing accepted building/Grid/Stair/Slab and separate168project preserved; TRC excluded.

## Honest remaining boundary

The operation generated1root+45listed hierarchical members+64bodyless Objects.54Objects have explicit native owner references into the listed Stair members;10reference readable native parents omitted from generic dump/hierarchy enumeration. Specialized connected-element queries returned empty lists. Their ancestry to this Stair is NOT_VERIFIED; empty bodies do not establish annotation status. Full inventory acceptance stays NOT_VERIFIED.

The original Create strict-inventory callback stopped on the additional Objects and retains PARTIAL_OR_UNKNOWN_OUTCOME in the journal. Its known root, dimension/BREP facts, collision check and successful Save/Open are subsequently recorded as independent evidence; history is not rewritten and Create remains non-replayable. All255elements are retained. This detached specimen does not prove a new physical building connection. ExactSDK detached solver/edit remainsBLOCKED; A11.S03 PARTIAL; A07/S10 historicaldependencies unchanged; engineeringNOT_VERIFIED.

## Validation and continuation

723/723Windows host tests and [Windows CI](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38561303098) PASS,5new source/inventory regressions. An initial sandbox-only suite encountered24temporary-file access errors; the unchanged suite passed on the actual Windows host.16affected tests pass. Published four code/document files were read back byte-exact.

Next: read-only specialized ancestry for10supportObjects before full inventory acceptance; independent native SinglePlaneRoof contour/slope editing next. No normative/search/KG implementation, documentation/layout, main or protectedAPX changes. Publisher safety flags below describe artifact-only publication, not the separately authorized native Create/Save/Open documented here.
