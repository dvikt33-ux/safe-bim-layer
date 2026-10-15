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


## Authorized runtime continuation: final current result

After the initial published checkpoint, the user explicitly approved the exact 71b8529a candidate for read-only owner/root-memo and selected-library-script diagnosis. Runtime identity matches the compiled source/build identity; GenerateDocumentation exports 293 commands. The two extended existing commands execute through the same dynamic router. The original APX and all 77 registration values are subsequently restored; a new original-runtime process exports 264 commands.

The native parent query confirms the generated Object owner is a RailingRail settings component. Both its own and the generated Object AddPars contain bmatRail/bmatFixing at BuildingMaterial 36. Root rail memo succeeds and contains one physical Rail, but does not contain that settings owner. Substituting the physical Rail GUID would therefore be unjustified. Stored memo flags differ from active script-evaluated flags: raw flags 1 do not override bmatFixing Disabled/Child in GetActParameters. No material setter is executed. Top-level master and parameter scripts are publicly readable but delegate to macros; no direct controlling rule for the two parameters is established. Raw library text remains private.

Actual owner memo and typed material facts now feed the existing graph: 352 nodes, 482 edges, 134 potential impacts from the previously observed Rail edit. Settings ownership, physical memo membership, stored parameter observations and write permission remain distinct. This supersedes the preliminary 347/474/132 slice without adding the two snapshots together.

Persistence is PARTIAL. After UI exit, the test-copy file hash changed from afcbdaaea880... to 0a9c01419823.... Neither native API trace contains a mutation or Save call. The cause of the saved-file change is NOT_VERIFIED; no rollback or overwrite is attempted. Both file checkpoints are retained privately. Independent readback after reopening with the restored original APX matches all 409 native signatures and all 128 GDL parameters exactly. The separate source PLN is unchanged. This proves native geometry/material/relationship retention, not byte-for-byte persistence. No next native mutation is authorized or attempted before this discrepancy is reconciled.

Final runtime evidence: [owner/library readback](evidence/APA_NATIVE_OWNER_LIVE_READBACK.json), [persistence discrepancy and independent readback](evidence/APA_NATIVE_OWNER_PERSISTENCE.json), [diagnosed connected flow](evidence/APA_NATIVE_OWNER_DIAGNOSED_FLOW.json). The earlier BUILD_NOT_INSTALLED evidence records the pre-approval checkpoint; this continuation governs the later deployment status. Material recovery remains BLOCKED/NOT_RESTORED. Quantity engine and offline tests are not invoked.
