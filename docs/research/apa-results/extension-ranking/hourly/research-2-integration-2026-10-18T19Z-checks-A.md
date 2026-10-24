# Checks 01–10: PR164 reconciliation and native IFC IDs

01 Q: forensic receipt exists? Source: https://github.com/dvikt33-ux/safe-bim-bridge/blob/feature/apa-ac29-apx-build-mailbox-20261018/safe-bim-mailbox/apa-ac29-group-acceptance/results/group-scenewriter-native-clone-20261018-01-readonly-reconciliation.json blob 0e4a3514, at=19:09:24Z. Verdict RECOVERED; next inventory.
02 Q: accepted geometry? Same receipt acceptedGuidCount=44, nativeBrepSignaturesMatchPreWriteTrace=true, 2 group members. Verdict read-only LIVE receipt; next journal.
03 Q: writer dispatch? Same receipt sqliteSceneEntries=0, sqliteStepEntries=0, writerNativeMutationDispatches=0, traceReadEntries=24. Verdict no dispatch in stopped attempt; next version.
04 Q: version drift? Same receipt originalRouterProviderVersion=1.5.8, liveTapirProviderVersion=1.5.10, port=19724. Verdict confirmed by receipt; binary hash still unknown; next file integrity.
05 Q: saved PLN? Same receipt savedScratchUnchanged=true, originalFunctionalTestPlnUnchanged=true, savedScratchSourceSha256=3a74d7cb17e460378eacfa8f933aeae29a5ca39fbf2bc73633115c9fee728750. Verdict scoped integrity; next other actors.
06 Q: globally no writes? Same receipt otherActorsNotCovered=true, automaticRetry=false, modelWriteReplayAuthorized=false. Verdict no global claim or replay; next code.
07 Q: reconciler native mutation? https://github.com/dvikt33-ux/safe-bim-layer/blob/b156ae3787403d0e68d7af3135b8208eea90e247/scripts/apa_ac29_group_scenewriter_reconcile_readonly.py#L101-L153 uses sqlite mode=ro and GetModelDumpV1, no Clone; publish writes evidence JSON. Verdict reuse; next IFC mapping.
08 Q: Tapir IFC→native input? https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/IFCCommands.cpp#L23-L40 requires ifcIds:string[]. Verdict SOURCE; next cardinality.
09 Q: IFC→native output? Same file L43–94 elementsByIFCIds[] with nested elements[]; FindElementsByGlobalId returns 0..N. Verdict not scalar map; next reverse.
10 Q: native→IFC input? Same file L109–138 requires elements array, returns elementIFCIds. Verdict SOURCE, local command availability unknown; next externalIFCId.
