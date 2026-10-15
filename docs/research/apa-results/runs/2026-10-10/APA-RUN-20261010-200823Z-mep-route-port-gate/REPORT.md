# APA-P10.A02.S04 — MEP routes, ports, distribution graph: verified source matrix

- **UTC research run:** 2026-10-10 / `APA-RUN-20261010-200823Z-mep-route-port-gate`
- **ПЛАН:** APA-P10 — Независимый технический аудит Archicad 29
- **ДЕЙСТВИЕ:** APA-P10.A02 — Инструменты и интеграции
- **ТЕКУЩИЙ ПОДШАГ:** APA-P10.A02.S04 — Native MEP/Tapir MEP команды, трассы, порты
- **Executor / claim_ref:** `chatgpt:apa-discovery` / `APA-RUN-20261010-200823Z-mep-route-port-gate`
- **Claim:** GitHub CAS READY → IN_PROGRESS, commit `1aea673dfcc91ada306c0e03c4beb80780ae84ef`, revision 24, readback PASS.
- **Source status:** `SOURCE_VERIFIED` for the exact pinned files/lines below. **OFFLINE:** NOT_RUN. **BUILD:** NOT_RUN. **LIVE:** NOT_VERIFIED. **PERFORMANCE:** NOT_MEASURED.
- **Supported source releases:** Graphisoft Archicad API DevKit `29.3100`; Tapir public tag `1.5.9` (MIT repository). The locally reported installed Tapir 1.5.10 was **not** matched to a source/binary SHA in this run. No paid AI/cloud dependency required for source work.
- **Source audit scope:** code/documentation read through connected GitHub file API, not search summaries.

## 1. Verified primary sources (exact pinned blobs)

| ID | Source URL / exact read portions | Git blob SHA |
|---|---|---|
| M1 | [Tapir 1.5.9 MEPCommands.cpp lines 232–274, 322–375, 429–485, 536–570, 661–750, 998–1070, 1157–1215, 1310–1346](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/MEPCommands.cpp#L429-L485) | `041b711fae03160eb0fda8b06a82da981f9fe0e3` |
| M2 | [Tapir 1.5.9 AddOnMain.cpp lines 1192–1226](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AddOnMain.cpp#L1192-L1226) — registrations | `9f44c2c28da71dee2ff398a34bca18d17451317c` |
| M3 | [Graphisoft AC29 Port class](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_port.html) — GetConnectedPortId, GetConnectedMEPElementId, IsPhysicallyConnected | `22a2a7c0bc86c13b03320d1eb95b64f3f3e558c4` |
| M4 | [Graphisoft AC29 DistributionSystemsGraph](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_distribution_systems_graph.html) — GetSystems, GetElements, GetPorts, CreateDistributionSystemsGraph | `91c4efd3193f4ac0b9ceac4a2a07a87b49bd0795` |
| M5 | [Graphisoft AC29 RoutingElement](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_routing_element.html) — GetRoutingNodeIds, GetPolyLine, ConnectLogically example | `14c7d2ae68d4ed1f692c9f24b394fe56caa860cd` |
| M6 | [Graphisoft AC29 Transition](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_transition.html) — GetRoutingNodeId, GetNarrowerPortID, GetPreferenceTable | `19474cf0273a9d7b226ddcbaafad5f15b3a57012` |

**Prior art, not a novel claim:** [Earlier recovered MEP Transition analysis](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-10/apa-recovery-20261010-132700-hotlink-mep-277e19.md) (REPORTED_FROM_CHAT). This run adds independently read Tapir runtime command bodies, graph-vs-port separation, batch/error semantics and exact blob hashes.

## 2. Capability and compatibility matrix

| Capability / command | Data or action read in pinned source | AC29 feasibility | Important limitation | Decision |
|---|---|---|---|---|
| Tapir `GetMEPElements` (M1 lines 232+) | Enumerates `API_ExternalElemID` elements; filters types/domains; returns elementId, type, domain | `#ifdef ServerMainVers_2800` (28+) | Enumerating elements does not demonstrate physical network connectivity | **Take existing** |
| Tapir `GetMEPRoutingElements` (M1 lines 322+) | `RoutingElement::Get`; reads polyline, MEP system, segment shapes/sizes, node positions | Source guarded AC28+ | Missing per-segment/node details if native Get fails: source `continue`; downstream must check coverage | **Integrate** |
| Tapir `GetMEPPorts` (M1 429–485), AC29 Port (M3) | Port GUID, location/orientation, shape, width/height, domain, system, `IsPhysicallyConnected`, optional connected port/element GUID | Source guarded AC28+ | `Port::Get` error silently skips port (lines 453–456). Success payload is `ports` list without parent `elementId`; preserve input index and count-check before building topology | **Integrate with validation** |
| Tapir `GetMEPDistributionSystems` (M1 536–569), AC29 Graph (M4) | `CreateDistributionSystemsGraph`; systems with domain, category, member element GUIDs | Source guarded AC28+; AC29 SDK docs | Tapir response enumerates *system memberships*, not individual connected-port edges. Cannot infer physical connection solely from it | **Reuse as network membership** |
| Tapir `CreateMEPRoutingElements` (M1 661–750) | Native `RoutingElementDefault::Place` for `Ventilation/Piping/CableCarrier`, 3D nodes, section | Source guarded AC28+ | Per-element errors and `continue`; lambda returns `NoError` at line 747; outer `ACAPI_CallUndoableCommand` result unused in observed body. Not evidence of batch atomic success | **Reserve writer with GUID readback** |
| Tapir `ModifyMEPRoutingElements` (M1 998+) | Changes system and segment cross sections | Source guarded AC28+ | Multiple Modify calls may yield partial changes; check all executionResults and before/after | **Defer writer** |
| Tapir `ConnectMEPElements` (M1 1157–1215) | Calls `RoutingElement::Modifier::ConnectLogically`; returns optional deleted/split route and created branch GUIDs | Source guarded AC28+ | **Logical** connection is not physical connection; GUID identity may change — user must reconcile deleted/split/created IDs | **Integrate only with mutation journal** |
| Tapir `GetMEPPreferenceTables` (M1 1310+) | Reads pipe and duct preference tables | Source guarded AC28+ | Explicit `CableCarrier` rejection with `APIERR_BADPARS`; not universal MEP table API | **Take existing for pipe/duct** |

**No new installation or APX compilation.** The manually available MEP Designer tools do not prove these Tapir commands run on the installed build.

## 3. Three concrete source-verified engineering conclusions

### A. Native MEP graph already gives system membership; custom topology reconstruction is not the first step

M1 lines 539–566 call Graphisoft `CreateDistributionSystemsGraph()` and return each `DistributionSystem`'s domain/category and member element GUIDs. M4 additionally documents `GetPorts()`, which **Tapir command does not expose in its distributionSystems response**. The direct AC29 API and Tapir JSON command therefore overlap but are not identical.

**APA benefit:** reuse the native grouping of network members. To audit continuity, combine this result with port-level `GetMEPPorts` and `IsPhysicallyConnected`. This avoids writing a system-membership extractor; it does **not** remove the need for QA graph checks.

### B. MEP port responses are potentially lossy

In M1 lines 452–456, `Port::Get(portId)` failure is handled by silent `continue`, not error output. In M1 lines 458–483, the success object contains `ports` but no explicit parent `elementId`; the ordered outer array mirrors input request iteration, while a failed *MEP element* gives an error entry. A consumer that merges by assumed port count or by arrays without retaining the input index could silently miss ports or misattribute them.

**APA benefit:** validate number of returned element entries against submitted GUIDs, associate each response by request index, count/compare known native port IDs, and mark incomplete port extraction `NOT_VERIFIED` rather than silently creating a false complete topology. **No claim of observed corruption**: this is source-based hazard analysis.

### C. Logical connection and route creation require a GUID mutation ledger

M1 lines 1184–1210 call `ConnectLogically` and may return `deletedRoutingElementId`, `splitRoutingElementId`, `createdBranchId`. Separately, M1 lines 672–750 place multiple routes in an undoable command; per-item failures continue and the enclosing lambda returns `NoError`, so do not assume all requested routes succeeded. The result type explicitly indicates possible identity changes — not proof that they occurred in our model.

**APA benefit:** for future isolated writer tests, compare before/after sets of all MEP GUIDs and port connections, not just old route GUID. Check individual results, physical connectivity, home story and geometries; reject writer-success claims without model readback.

## 4. Architecture decision (avoid reinventing)

1. **Native Model Dump remains geometry/material/story source**, with existing live evidence; never replace it with network graph alone.
2. **Tapir MEP JSON is the low-development-cost first read interface** for system groups, route geometry and port attributes. New native adapter **only** if a proven gap (e.g., exact port completeness) remains.
3. **Graphisoft AC29 MEP API** is the source of truth for native graph/port semantics; use alongside Tapir to verify potentially omitted metadata.
4. **IFC/IfcOpenShell graph** is a separate coordination/export layer, not a substitute for in-PLN port IDs; requires mapping and IFC coordinate checks.
5. **Reject** own monolithic MEP route planner/physical connectivity engine for MVP until gaps and benchmarks substantiate it.

No numeric speedup, licensing entitlement or run-time performance is asserted. Tapir repo LICENSE in prior research reported MIT; SDK governed by Graphisoft terms; external paid AI not required.

## 5. Next independent technical test / acceptance gap

**Gate 1 SOURCE (current):** pinned GitHub files/sections/SHAs and command matrix verified.

**Gate 2 OFFLINE (NOT_RUN):** build a synthetic 2-route+branch JSON fixture with deliberately missing `Port::Get` and logical-only connections. Test that APA importer flags incomplete port coverage, does not confuse port edge with system membership, preserves response/index associations, and creates an audit report.

**Gate 3 LIVE read-only (NOT_VERIFIED):** after permission to use isolated Archicad 29 test PLN, verify installed Tapir 1.5.10 source/binary provenance; issue `GetMEPElements`, `GetMEPRoutingElements`, `GetMEPPorts`, `GetMEPDistributionSystems`; cross-check GUID counts, system categories, port physics and before/after GUID inventory. Do not modify or save PLN.

**Gate 4 writer (requires separate permission):** isolated disposable PLN, `CreateMEPRoutingElements` + `ConnectMEPElements` with per-item outcomes, model GUID delta, new/removed/split/branch GUID journal, physical port connectivity readback and Undo.

**Remaining acceptance for APA-P10.A02.S04:** source matrix complete on public API, but *installed* 1.5.10 parity, independent OFFLINE and LIVE are NOT_VERIFIED. Recommended controller status: `PARTIAL` rather than `DONE_PUBLISHED` pending audit/acceptance.

## 6. Reviewer handoff and new-task screening

Auditor: verify GitHub pinned blob SHAs and M1 line anchors, distinguish group vs graph-edge semantics, check `GetMEPPorts` missing port error handling, independently inspect Tapir 1.5.10 deployed binary, then assign tests only after prerequisites. No simulated output is LIVE.

Candidate new task check: port-count, writer GUID mutation ledger, preference limits and native graph cross-check all belong to existing MEP `APA-P10.A02.S04`, catalog `APA-P50.A02.S01`, and validation `APA-P20` work. **No additional TASK_PROPOSAL_V1** (avoid semantic duplicate).

**Safety:** no changes to main/master, PLN, APX, production branch, software; no Work/Codex/paid AI/API/local LLM.
