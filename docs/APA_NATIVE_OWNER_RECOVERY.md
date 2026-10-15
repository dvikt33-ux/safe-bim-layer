# Native owner recovery and compound MODIFY after PR109

Current native read confirms all 409 GUID signatures and all 128 placed parameters unchanged from PR109. The generated Railing Object names a different native RailingRail owner from the physical Rail edited in PR108. The actual settings owner is absent from the ordinary physical-element inventory. Its root membership and material memo must therefore be queried explicitly; the previous physical Rail is not a proven settings owner.

The two material assignments remain at index 36; the expected BuildingMaterial GUID currently resolves uniquely to index 37. The existing generated-Object setter already returned APIERR_NOTSUPPORTED and is not retried. bmatFixing is Disabled; equal values or parameter names do not prove propagation. Geometry, Rail 0.17 m, Shell 4.5 m, source saved PLN and original APX remain unchanged in this package.

## Implemented product behavior

- Existing GetNativeAssemblyEditStateV1 now has a read-only generated-Railing-Object state: declared owner, native parent/root, independent Object/owner AddPars, root Railing rail memo, stamps, typed material identities and bounded allocations. It does not expose a material mutation.
- The existing library-default command optionally reads the selected library part master and parameter scripts through the public SDK. Only one explicit library part is accepted; text is bounded and remains private. Protected/unavailable sections retain native errors. No script execution, password bypass or GDL interpreter.
- Owner-aware recovery preparation resolves exactly two typed material changes from current attribute identity, snapshot hashes and current scope. It returns BLOCKED with no mutation ticket until a supported native owner write and fixing dependency are qualified.
- Compound MODIFY now requires resultant BREP, per-element materials, GDL, ownership, dependent changes and a complete before snapshot by default. Missing or empty proof cannot produce PASS. Unexpected child GUID changes require reconciliation. Existing SceneWriter and SQLite retain the original intent in failure/success results; old ledger rows remain untouched. One old failed material setter is matched to its independent no-effect proof; legacy unscoped rows remain NOT_VERIFIED.
- Existing CW polygon/pattern handling bounds SDK allocations. Existing Shell adds Extruded shape direction and class-specific Revolved distortion/segmentation fields; Ruled morphing rule remains read-only. These are BUILD_PASS, not LIVE_PASS.
- The existing DependencyImpact consumes native generated-owner and observed edit-effect relationships, generated GDL observations and typed MEP dimension/system facts. Current captured slice: 347 nodes, 474 edges, 132 potential impacts from the previously edited Rail. Observed side effect is not a guaranteed future rule or authorization for dependent writes. This slice replaces, rather than adds to, previous graph counters.

## Source limitations

A [Graphisoft developer reply](https://community.graphisoft.com/t5/Archicad-C-API/Writing-GDL-AddPar-values-e-g-material-override-to-Railing-sub/m-p/715108/highlight/true) proposes editing AddPars on the editable component obtained from owner memo. The [AC29 follow-up](https://community.graphisoft.com/t5/Archicad-C-API/Writing-GDL-AddPar-values-e-g-material-override-to-Railing-sub/m-p/712199) reports APIERR_BADPARS on that route. This is a proposed contract, not a qualified recovery. SubElement enum names do not establish valid owner/component indices. No random masks, direct Disabled writes, regeneration, Undo or root-wide rollback are attempted.

## Acceptance and continuation

Full Windows Release build succeeds. New binary is not installed, registered or callable-verified. Next: exact-binary approval for a read-only owner/root-memo and selected-library-script diagnosis in the existing copy, restoration of original APX/registration, then qualify the smallest supported material recovery before requesting its write. Pending exact PR104 binary approval is separate and not repeated. Materials are NOT RESTORED. Full assembly MODIFY, positive MEP, IFC export and A11.S03 remain incomplete.

No offline tests, workflow dispatch, quantity computation, model writes, Save/Open, new samples or APX changes in this package. Existing code, journal, original projects and historical evidence are retained.

Evidence: [build](evidence/APA_NATIVE_OWNER_BUILD.json), [current native state](evidence/APA_NATIVE_OWNER_CURRENT.json), [actual-data preparation and graph](evidence/APA_NATIVE_OWNER_PREPARATION.json), [acceptance contract](evidence/APA_NATIVE_OWNER_ACCEPTANCE.json), [public-source qualification](evidence/APA_NATIVE_OWNER_SOURCE_AUDIT.json).
