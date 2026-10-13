# Existing-project Grid/Stair checkpoint and safe module recovery

[Draft PR77](https://github.com/dvikt33-ux/safe-bim-layer/pull/77), head `c1b4e1a565bcd903273933d8917608df156ac600`, exact parent PR76 `bc8f8575ed65e308e10c5ac5f573b7d8ad9466a6`.

## Working code

Completed exact Stair operations now reuse their existing SceneWriter SQLite GUID without a new Create. Source hash, original target binding, current saved-file hash, retained signatures, exact native dimensions and Favorite rules must still match. Unknown outcomes, changed source and native drift are denied. Eight new tests exercise actual SceneWriter/SQLite completion and rejection paths. **697/697 host and Windows/Linux CI PASS**,102 upstream graph tests and actual core-MCP integration in both CI jobs. [CI](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38459091689). This is OFFLINE_PASS; new native Stair repeatability is NOT_VERIFIED.

The recipe now uses the existing authorized test PLN. No new PLN, building, Grid, Stair or Morph was created. Accepted Stair remains unchanged. PR76 C++/compiled candidate is preserved byte-for-byte.

## Native preservation and deployment outcome

Actual candidate SHA256 `8ad672092aa93e4bf1b4d469cbf7840cb60acd538820183bb68d5d6786ea221d` verified. User explicitly authorized temporary test-instance switching without overwriting the installed file. The original Tapir was disabled using the manager and Archicad's required Save/Open. After selecting the external candidate, the manager displayed the original installed path for both Tapir entries. **Automatic approval review rejected applying the ambiguous configuration because it could load the original module instead of the authorized candidate.** No candidate load or new model write was attempted after the rejection.

The original module was restored. Two recorded UI deployment Save/Open cycles overall are distinct from SceneWriter model operations; its journal is unchanged: PASS52/UNKNOWN_OUTCOME3. No blind replay or historical journal deletion. Independent native readback proves all143 accepted GUID/geometry/material/story signatures and native story structure unchanged. Separate accepted168 saved bytes match. Installed APX bytes remain unchanged; other instances were not reconfigured. Backup bytes were verified and remain local.

Current saved PLN SHA256 `b1f0b8e415f3e07f5a9c5c488a212456972f0a1c37afcebfef6554fdec08eecd` differs from the prior saved hash as expected after Save; retained model signatures match exactly. Fresh installed export has263 old commands and none of the8 new Grid/Stair endpoints. A version number alone does not qualify the candidate. **PRESERVATION_PASS** applies to retained143; **Grid LIVE_PASS, new Stair SOURCE_DIMENSION_PASS and live REPEATABILITY_PASS remain NOT_VERIFIED**. Engineering suitability is NOT_VERIFIED.

## Continuation

Unambiguously load the exact candidate in the existing authorized test instance, then verify actual process module path/hash, fresh schema and all old/new commands. Do not overwrite installed APX or affect other instances without separate permission. Obtain actual GREL defaults/parameter roles; use detached native solve for3.3m/22risers/0.15m/0.35m before a single new Stair. Create/edit/read true axes, independently verify rendered span, run zero-Create reuse and SceneWriter Save/Open with all143 signatures preserved. No new test PLN is required. SinglePlane Roof follows actual Grid/Stair acceptance.

A11.S03 remains PARTIAL; historical DONE tasks, A07 dependencies and S10 blocker are preserved. Normative, Knowledge Graph/search and documentation implementation are unchanged. Main orchestrator used read-only current GitHub Knowledge Graph revision139 before CAS140. Raw projects, private paths and dumps are not published. Publisher safety fields apply to this artifact-only publication operation; the earlier authorized UI Save/Open/file-hash change is explicitly reported above.
