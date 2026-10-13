# Native architectural documentation follow-on

A working native plan, Section and true exterior Elevation share one new A2 Layout and are exported by Archicad Publisher as one PDF page. The user's partial-facade screenshot exposed incorrect finite marker placement; only the newly created Elevation was movedY=-5m. Rendered west facade now contains both stories, both visible windows and the complete roof. Its actual native PDF roof span8.029912m matches the model projection8.029888m within0.0001m. Visible-owner counts9→12 are supporting evidence, not full drawing acceptance.

## Actual native results

- True Elevation copied from a retained native template through the existing SceneWriter, not InteriorElevation/Morph substitution. Original121main-model GUID/BREP/material/story signatures unchanged, including original109;126current main identities persist after Save/Open. New Elevation plus4native subordinate Objects explain the increase. Layout Drawings, dimensions and navigator/database identities are separate GUID domains.
- One new native associative dimension reads the actual0.20000006m Slab thickness and5source-bound witness points.32native plan and34section Drawing fill contours read after known-success cache refresh; the two slab vertical levels agree with dimension witnesses within0.000001m. Drawing2D/paperXY and candidate inverse-transformUV are not project XYZ.
- Three new saved views and linked Drawings on one native A2 Layout. The initial oversized preliminary new Drawing is parked offsheet and preserved. Native Drawing source metadata returns an opaque differing GUID: NOT_VERIFIED. Changing only the new plan view scale100→125→100 changes its Drawing0.01→0.008→0.01 while the clip frame stays fixed, independently proving source behavior.
- Existing native Publisher1-layouts selected the new Layout and produced one A2 page; file bytes/pages/scale/render verified after Save/Open. Publisher2-views yielded65pages despite selecting two items, so that selected-subset path is not accepted. No global Publisher/MEP preference or APX edits.

## Explicit limits

Thirteen native Schedule definitions are discoverable; row read/configuration contracts remain unsupported. Existing six-type CSV facts are retained without duplication. Facade surface-fill contours, complete line/text primitives and owner-per-contour export remain unavailable through the installed interface; native PDF verifies facade scope. ModelVersion stays unchanged because the physical building was not edited. Prior PR70 native test Wall edit synchronization remains historical proof, not a new edit test. Explicit source rebuild/drawing update is reused; no watcher or second executor.

Native ambiguities were independently reconciled; original UNKNOWN_OUTCOME events remain historical and no Create/Modify was blindly replayed. Layout database recovery uses the same writer for a view-only activation, followed by complete signature checks. Prototype sheet has no normative/engineering acceptance. A11.S03 remains PARTIAL; A07.S01 dependencies preserved, S10 BLOCKED unchanged. Normative/search implementations and main/master untouched. Main APA orchestrator used the existing read-only Knowledge Graph with GitHub-current gates before claim130.

## Published code and verification

[draft PR73](https://github.com/dvikt33-ux/safe-bim-layer/pull/73), head `93557ed0cd59c471b0f903a03708ed88c8feb31b`, exact parent PR71 `88169d358e4c329f8959f557c944300adcec2df9`. Six code blobs match GitHub.17newtests;623/623Windows host and [Windows/Linux CI38367671224](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38367671224) PASS;102/102upstream graph tests and core/MCP smoke PASS in each environment. Raw model paths/PLN/full technical dumps stay local. Publisher safety booleans describe only the publication process; earlier approved isolated live test was changed and saved.

[Native sheet preview](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/native/APA-RUN-20261013-082134Z-native-documentation-followon/native-sheet-preview.png). Local native PDF hash `80eec0a47e40e2a78e92efe7b9f67ea132794c5abaa5008e0bea1705e51b5fca`. [Evidence](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-verified-results-hub-20261010/docs/research/apa-results/native/APA-RUN-20261013-082134Z-native-documentation-followon).

Next: supported native schedule row/configuration contract, then full vertical primitives/owner mapping. Future facade acceptance must include actual rendered extent on a verified projection axis, never owner count alone.
