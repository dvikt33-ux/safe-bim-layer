# APA AC29 — Researcher 2 integration cycle, 2026-10-18 19Z

**30 real SOURCE contract checks; 2 independent audits.** No new OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED. No install, native operation, code change or speed measurement. GPT web browser + Opera + GitHub used. MODEL_MODE_NOT_VERIFIABLE.

Read first: [queue](../NEXT_RESEARCH_PRIORITIES.md) blob 677b5c15, [matrix](../priority_matrix_20261018.json) blob 9cb5e6f2, [61 candidates](../candidates.json), [researcher 1 19Z](research-1-20261018T19Z.md) blob ecdbe275, [auditor 3 18Z](audit-2026-10-18-18.md) blob 9a7cfb2f, [coordinator tasks](audit-2026-10-18-18-tasks.md) blob 0fee19f0. Auditor 19Z publication NOT_FOUND when checked. Canonical PROJECT_PLAN revision182 blob c2ab2f9d read-only.

## New finding: PR164 forensic receipt RECOVERED
[19:09:24Z reconciliation](https://github.com/dvikt33-ux/safe-bim-bridge/blob/feature/apa-ac29-apx-build-mailbox-20261018/safe-bim-mailbox/apa-ac29-group-acceptance/results/group-scenewriter-native-clone-20261018-01-readonly-reconciliation.json), blob 0e4a3514, now exists (auditor 18Z had found 404). Fields: port=19724; acceptedGuidCount=44; sqliteSceneEntries=0; sqliteStepEntries=0; writerNativeMutationDispatches=0; nativeBrepSignaturesMatchPreWriteTrace=true; liveTapirProviderVersion=1.5.10; originalRouterProviderVersion=1.5.8; savedScratchUnchanged=true; automaticRetry=false; otherActorsNotCovered=true. **Prior STOPPED remains; Clone NOT authorized.** Receipt is published prior LIVE read-only evidence, not a new LIVE action by this cycle.

## Nine integration decisions

| Existing APA → ready tool → result | Benefit / effort / choice | Gate |
|---|---|---|
| PR164 reconcile → SQLite/trace/ModelDump → receipt | 99 БЫСТРО reuse | 44 GUID/BREP, no dispatch; no Clone retry |
| Router/Bridge → Tapir 1.5.9 IFC ID commands → BIM Graph | 97 АДАПТАЦИЯ adapter | 0..N, ifcId/externalIFCId, active catalog/binary SHA |
| PR165 Router → ezdxf 1.4.5 multi_insert → JSON | 94 АДАПТАЦИЯ adapter | 2×3=6, OCS/WCS, INSUNITS, XCLIP |
| Tapir 1.6.0 translator names → AC29 export presets → IFC manifest | 92 АДАПТАЦИЯ adapter | only name/preview in API; six-preset serializer NOT_FOUND |
| PR166 IDSReportODS → IfcTester → TDF ODF Validator 0.13.0 | 88 АДАПТАЦИЯ adapter | ZIP CRC ≠ ODF schema; JRE11, license/deps |
| Tapir native Issues or IfcTester IDS → BCF2 ZIP → bcf.bcfxml/XSD | 87 АДАПТАЦИЯ adapter | empty native Issues means ALL; XML/link/schema QA |
| PR166 IFCSelect/IFCSchemaValidate → IfcOpenShell → JSON | 86 БЫСТРО reuse | express_rules=false, geometryChecked=false |
| PR165 IFCGeoReferenceAudit → util.geolocation → XYZ/ENH | 79 АДАПТАЦИЯ defer | pinned installed 0.8.5 source NOT_VERIFIED |
| Router catalog → GetAddOnVersion → provider identity receipt | 96 БЫСТРО reuse | port+binary SHA+command list, 1.5.10 vs 1.6.0 |

Detailed [30 checks](research-2-integration-2026-10-18T19Z-evidence.md) and [two audits](research-2-integration-2026-10-18T19Z-audits.md). Scores are engineering estimates, not speedup. Existing Router/SceneWriter/BIM Graph, PR154/162/165/166 retained; no second writer. Three external links maximum.

**Gates:** SOURCE version/schema/license → OFFLINE immutable fixtures + SHA/readback → BUILD SDK29/Win11 only if approved → INSTALLED binary/hash/catalog → LIVE approved scratch PLN only → ACCEPTED independent GUID/geometry/units/relations. PR165 12/12 synthetic installed-smoke is prior receipt, not native LIVE. AC30 excluded.

**Researcher 1 questions:** exact Tapir 1.5.10 binary/source and backports; six IFC translator presets API; IfcOpenShell 0.8.5 Windows wheel/source SHA; BCF-XML 2.1 license; ezdxf XCLIP/WCS supported QA.

**Coordinator 3 handoff:** PR164 forensic RECOVERED (no retry), Tapir IFC IDs, MINSERT, translator provenance, ODS validator, BCF ZIP/XSD, geolocation pin. Main, PLN/APX, code, queue and plan182 unchanged.
