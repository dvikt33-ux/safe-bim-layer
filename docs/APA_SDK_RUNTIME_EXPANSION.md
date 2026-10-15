# APA SDK runtime expansion

The PR #88 candidate was loaded in the authorized existing test project. All six added SDK/DevKit queries were registered, called, and validated against their result schemas. Four queries also have scoped native fact checks. The candidate exposes 281 registered add-on commands; with 73 compatible official API contracts, 354 native commands are available in that candidate. This does not make every command LIVE_VERIFIED.

The test made no model API writes. Independent inventories retained all 258 GUIDs and serialized element parameters. The saved file bytes changed during the earlier application close/open; the cause is NOT_VERIFIED. Bytes remained unchanged during the six SDK reads. No independent physical BREP comparison was run. License query responses and identifiers are suppressed.

The original APX and Include registration have been restored and checked. The read results are recorded in `docs/evidence/APA_SDK_RUNTIME_READ.json`; restoration is recorded in `docs/evidence/APA_SDK_APX_RESTORATION.json`.

Provider attachment now stages a complete batch before committing it. Duplicate commands and conflicting schemas leave the prior catalog and fingerprint unchanged. Ambiguous common-schema names receive distinct aliases without rewriting previously attached contracts. Two focused tests exercise the defects identified in PR #87.

Further SDK groups are being connected through the existing manifest, dynamic router, and BIM Graph. Unbuilt or uninstalled work is excluded from native acceptance. A11.S03 remains PARTIAL.
