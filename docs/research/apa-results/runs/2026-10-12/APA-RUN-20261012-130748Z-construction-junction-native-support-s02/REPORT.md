# A04.S02 — working source-bound support junction

The existing ARMO c4 batten25×150mm is now physically supported by a new native c5 counterbatten50×50mm. Details source ARMO_SELFLOCK_ROOF__P0003, page3 PF001/PF002 provides both sections and the explicit support relation. The5.9801000489m span and placement follow actual accepted batten/roof and endpoint-wall geometry. No source construction dimension is invented.

SceneWriter created one editable Morph using the accepted structural-timber Building Material on story1; the existing Archicad v2.0Beam classification was assigned only to this member. Native shared-face readback proves0.007500000016m²contact (75cm²); native collision readback is empty for the new member. Logical source relation, actual contact, intersection and structural capacity remain separate.

All95accepted GUID and body signatures are preserved. The saved/reopened model has96GUID and38shared-context records; the branched MEP network remains identical. Save returned success. First Open timed out at15seconds; exact current/saved state and ready project UI were reconciled before one separate controlled45-second Open, which acknowledged success. All96body signatures, material, story, classification, contact, network and saved file hash match after reopening. One Create, one classification Set, one Save, two Open attempts; no Create/Modify/Set replay.

The source archive and dependent native body/material/story pins invalidate stale graph plans. Existing source context, CSE selection, Native Model Dump, NetworkX, Shapely, BIM Graph and SceneWriter are reused. Existing classification systems and user defaults remain unchanged; no installed APX or main change.

426/426 tests PASS locally and on Windows/Linux CI38251796931, including23construction-junction tests. Published code blobs were fetched independently and match the commit. Native classification provider direct rows are validated strictly alongside the catalog wrapper; the observed discrepancy was reconciled without setter replay.

S02 meets its selected editable, parameterized, classified, sourced and invalidating sub-junction criterion. Full roof assembly, fixings, timber grade, rafter bearing and structural capacity remain ENGINEERING_NOT_VERIFIED. Other junction families are not declared complete. S03 follows with independent family qualification.


Evidence: [APA-RUN-20261012-130748Z-construction-junction-native-support-s02](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010/docs/research/apa-results/native/APA-RUN-20261012-130748Z-construction-junction-native-support-s02). Draft PR57, head b17c460e92e794de94149c8405a8fb48d885ab27. Stable SHA tokens replace private native identities; raw payloads stay local. Publication makes zero native calls.
