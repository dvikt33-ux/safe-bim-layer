# APA №2 — 20.10.2026 02Z. Инженерное подключение готовых решений

SOURCE-only: **30 технических проверок, 2 собственных контрааудита**. В этом цикле новых OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0. Без установки, кода, PLN/APX, main, PR merge и правок канона/NEXT. MODEL_MODE_NOT_VERIFIABLE.

Прочитаны [NEXT](../NEXT_RESEARCH_PRIORITIES.md), [матрица](../priority_matrix_20261018.json), [61 кандидат](../candidates.json), [№3 00Z](audit-2026-10-20-00.md), [поручения](audit-2026-10-20-00-tasks-2.md), [№1 18Z](research-1-20261019T18Z.md), [№2 01Z](research-2-integration-2026-10-20T01Z.md). Основной №1 20.10 01Z/02Z по точным путям NOT_FOUND. Канон PROJECT_PLAN.json на research/apa-verified-results-hub-20261010 прочитан: **rev197**, blob b079bb94; исторический rev182 только чтение.

**Новое для очереди:** [PR178](https://github.com/dvikt33-ux/safe-bim-layer/pull/178) SAFE-01 saved/reopened 69→119 GUID; [PR179](https://github.com/dvikt33-ux/safe-bim-layer/pull/179) group grid8×4 LIVE 44→172 GUID; [PR181](https://github.com/dvikt33-ux/safe-bim-layer/pull/181) batch individual copy; [PR184](https://github.com/dvikt33-ux/safe-bim-layer/pull/184) selected axis intersections; [PR185](https://github.com/dvikt33-ux/safe-bim-layer/pull/185)/[186](https://github.com/dvikt33-ux/safe-bim-layer/pull/186)/[188](https://github.com/dvikt33-ux/safe-bim-layer/pull/188) create/ungroup/move native groups; [PR189](https://github.com/dvikt33-ux/safe-bim-layer/pull/189) DXF preflight INSTALLED; [PR190](https://github.com/dvikt33-ux/safe-bim-layer/pull/190) group intent INSTALLED/READ_ONLY; [PR191](https://github.com/dvikt33-ux/safe-bim-layer/pull/191) Slab copy LIVE_PASS пока не заявлен. Это опубликованные свидетельства, **не выполненные нами тесты**.

**Приоритетная матрица (польза — экспертная, не ускорение):**
| Кандидат | Путь в существующий APA, готовый компонент | Решение / риск / критерий ГОТОВО |
|---|---|---|
| Publisher 100 | Bridge → Tapir1.5.9 GetNavigatorItemTree → SDK29 Navigator census | ADAPTER/HIGH: GUID whitelist, reject missing/[]/duplicate/child-error; Publish не вызывать |
| Hosted windows/doors 100 | PDFVectors/Router → Tapir CreateWindows/CreateDoors | REUSE+ADAPTER/HIGH: hostWallGUID, centerOffset, story, favorite; готовый PDF→host adapter NOT_FOUND |
| DXF XCLIP 99 | PR168 C1 → ezdxf1.4.5 XClip WCS → минимальный 2D clipper | ADAPTER/HIGH: RAW/VISIBLE/UNSUPPORTED; готовый end-to-end NOT_FOUND |
| DXF MINSERT 97 | PR189 installed preflight → ezdxf multi_insert → C1 | REUSE/MEDIUM: declared/unique/zero-spacing/INSUNITS |
| IFC ports 99 | Existing IFC V2 → IfcOpenShell0.8.5 get_ports + IfcRelConnectsPorts → BIM Graph | REUSE+thin reader/MEDIUM: IFC2X3/4, complete typed relation graph |
| PDF→IFC 98 | PDFVectors → ifcopenshell.util.element.get_referenced_elements → read-only sidecar | REUSE/MEDIUM: PDF SHA/page/revision→GlobalId, no add_reference |
| Hotlink graph 99 | Existing SDK29 Bridge → GetHotlinkNodes/Tree/Instances/ProxyElementTable/SourceStatus → BIM Graph | ADAPTER/HIGH: node→instances, proxy→source, cache/status/story |
| Massops/save 100 | Existing Router/SceneWriter → accepted native operations + #178 snapshot | REUSE/DEFER: exact saved SHA/GUID/BREP/reopen; не повторять; #191 отдельно pending |

**Контрааудит А:** Tapir tag1.5.9 MIT ≠ локальная сборка1.5.10; SDK29.3000 Graphisoft EULA ≠ SDK30; ezdxf1.4.5 MIT; IfcOpenShell Python0.8.5 LGPLv3+ с компонентным GPL-gate. Локальные APX/ABI build5101 не проверены. **Контрааудит Б:** не создавать второй Router/SceneWriter/DXF preflight; PR189 уже установлен, PR190 READ_ONLY, PR191 не LIVE; Publisher [] может опубликовать весь set, XCLIP игнорируется recursive_decompose, get_connected_port даёт один peer, cooperative lease не OS-lock. 8 GB VRAM не требуется по контракту, 48 GB RAM не измерены.

**Гейты будущего подключения:** SOURCE tag/SHA/license/GUID/units → OFFLINE negative fixtures → BUILD SDK29 только при пробеле → INSTALLED staged existing Router с сохранением прежних contract hashes и backup → LIVE только разрешённый disposable PLN one-shot → ACCEPTED независимый GUID/BREP/owner/material/SQLite/snapshot SHA и GUI reopen. UNKNOWN: stop/no replay; откат feature flag OFF, immutable originals.

**№1 спросить:** error-aware Publisher census; PDF wallGUID/offset resolver; XCLIP 2D clipper; SDK29 Hotlink read-only wrapper; local Tapir1.5.10 manifest; IFC2X3/4 references; PR191 LIVE. **№3 передать:** Publisher, hosted, Hotlink, IFC ports, XCLIP, PDF sidecar, MINSERT, Slab status boundary. Только утверждение, не внедрение.

Детальные 30 проверок с первоисточниками и параметрами — в приложении к этому часу. PUBLICATION_READBACK_PENDING.
