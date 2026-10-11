# APA — реестр реально опубликованных материалов

**Срез:** 2026-10-10. Этот реестр различает **файл найден и прочитан** от **его технический вывод независимо проверен**. Не делать вид, что все прошлые исследования доступны или проверены.

## Текущий центр

| ID | Материал | Где лежит | Состояние публикации | Проверка содержания |
| --- | --- | --- | --- | --- |
| HUB-001 | [README](README.md) | canonical hub | GITHUB_READBACK_VERIFIED | Прочитан; служебная навигация |
| HUB-002 | [Реестр APA-01…APA-12](2026-10-10-research-register.md) | canonical hub | GITHUB_READBACK_VERIFIED | Много REPORTED и SOURCE_CANDIDATE; независимые LIVE не подтверждены |
| HUB-003 | [CURRENT_BLOCKERS](CURRENT_BLOCKERS.md) | canonical hub | GITHUB_READBACK_VERIFIED | Сводка; не самостоятельное LIVE-доказательство |
| HUB-004 | [PUBLISHING_PROTOCOL](PUBLISHING_PROTOCOL.md) | canonical hub | GITHUB_READBACK_VERIFIED | Правила публикации |
| HUB-005 | [APA-DOC-PIPELINE-01: Publisher/Layout](runs/2026-10-10/apa-technical-20261010-094254-publisher-layout-01.md) | canonical hub | GITHUB_READBACK_VERIFIED | SOURCE claim, installed APX LIVE NOT_VERIFIED |
| RUN-SDK-GET3D-20261010 | [AC29 3D/Opening API: два Get3DInfo и нативные связи](runs/2026-10-10/apa-sdk-20261010-102452-get3d-connections-source.md) | canonical hub | GITHUB_READBACK_VERIFIED; [commit d65c5bd](https://github.com/dvikt33-ux/safe-bim-layer/commit/d65c5bd327d077d7873ff720cda6dac3bf8a22cb) | SOURCE_VERIFIED official docs; SDK header/BUILD/LIVE NOT_VERIFIED; **не** полный Deep Research |
| OPS-001 | [MASTER_PLAN](MASTER_PLAN.md) | canonical hub | GITHUB_READBACK_VERIFIED | План, не исследовательское доказательство |
| OPS-002 | [BRANCH_REGISTRY](BRANCH_REGISTRY.md) | canonical hub | GITHUB_READBACK_VERIFIED | Частичная карта веток |
| OPS-003 | [RESEARCH_TEMPLATE](RESEARCH_TEMPLATE.md) | canonical hub | GITHUB_READBACK_VERIFIED | Шаблон |
| OPS-004 | [CURRENT_STATUS](CURRENT_STATUS.md) | canonical hub | GITHUB_READBACK_VERIFIED после создания | Операционный статус |
| OPS-005 | [AGENT_PROTOCOL](AGENT_PROTOCOL.md) | canonical hub | GITHUB_READBACK_VERIFIED после создания | Инструкция всем исполнителям |
| OPS-006 | [AUTOMATION_AND_GATES](AUTOMATION_AND_GATES.md) | canonical hub | GITHUB_READBACK_VERIFIED после создания | Проект автоматики, не действующий сервис |
| OPS-007 | [RESEARCH_QUEUE](RESEARCH_QUEUE.md) | canonical hub | GITHUB_READBACK_VERIFIED после создания | Очередь задач |

## APA Research OS — материалы из переданного аудита

| ID | Материал | Публикация | Достоверность |
| --- | --- | --- | --- |
| OS-AUDIT-001 | [Сохранённый аудит APA Research OS](runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md) | GITHUB_READBACK_VERIFIED, [commit 9b07679](https://github.com/dvikt33-ux/safe-bim-layer/commit/9b076792124d99d67dcc0f01554b4834fc3ed8cb) | USER_SUPPLIED_REPORT, нормализованная версия; исторические claims REPORTED |
| OS-INV-001 | [72 branch heads + PR map JSON](inventories/BRANCH_HEADS_20261010.json) | GITHUB_READBACK_VERIFIED, [commit 7dc6544](https://github.com/dvikt33-ux/safe-bim-layer/commit/7dc65444282d6bf6f14013fd8621328ee08b18a9) | GitHub API branch/head/PR SOURCE_VERIFIED; ancestry/artifacts NOT_VERIFIED |
| OS-INV-002 | [FULL_BRANCH_INVENTORY stage 1/2](inventories/FULL_BRANCH_INVENTORY.md) | GITHUB_READBACK_VERIFIED, [commit 895846f](https://github.com/dvikt33-ux/safe-bim-layer/commit/895846f096aea4440a7e292f8cc89adab79c78d9) | Все 72 имена/SHA, не полная forensic classification |
| OS-SCHEMA-001 | [RUN_EVENT_V2 JSON Schema](protocol/RUN_EVENT_V2.schema.json) | GITHUB_READBACK_VERIFIED, [commit 2ff4dcf](https://github.com/dvikt33-ux/safe-bim-layer/commit/2ff4dcfde139c5f9b52df31ba07b59de9ca6dcd6) | Схема, не работающий publisher |
| OS-CONTRACT-001 | [Publisher / crash recovery](protocol/PUBLISHER_CONTRACT.md) | GITHUB_READBACK_VERIFIED, [commit b736f23](https://github.com/dvikt33-ux/safe-bim-layer/commit/b736f23cf8573febfd6722e42e9db4b63c986f22) | Дизайн и gates; runtime NOT_DEPLOYED |
| OS-POLICY-001 | [Evidence policy](protocol/EVIDENCE_POLICY.md) | GITHUB_READBACK_VERIFIED, [commit d6e60fb](https://github.com/dvikt33-ux/safe-bim-layer/commit/d6e60fb1044489fc88eb8015455464ae04f7f7cb) | Политика, не live-test |
| OS-RECEIPT-001 | [Readback receipt исходного аудита](receipts/APA-RUN-20261010-102800Z-research-os-audit-readback.json) | GITHUB_READBACK_VERIFIED, [commit b64a491](https://github.com/dvikt33-ux/safe-bim-layer/commit/b64a4913249af780abac4b330b3958b5d1f93841) | GitHub blob SHA подтверждён; SHA256 NOT_COMPUTED; index pending |

| OS-PUB-001 | [GitHub Actions automatic publisher workflow](../../../.github/workflows/apa-research-publisher.yml) | DEPLOYED on canonical research branch, [commit 901dd97](https://github.com/dvikt33-ux/safe-bim-layer/commit/901dd973293f3200749b5f37fd5bbfa7f7da4f21) | [Push-triggered E2E run success](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668); no 24/7 research scheduler |
| OS-PUB-002 | [Publisher Python implementation](../../../tools/apa_publisher/publisher.py) + [6 offline tests](../../../tools/apa_publisher/tests/test_publisher.py) | GitHub readback verified; [tests in workflow success](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668) | Immutable run, generated index, REST readback, receipt; no Archicad live |
| OS-PUB-003 | [Synthetic automatic REPORT](runs/2026-10-10/APA-RUN-20261010-104437Z-publisher-integration-smoke/REPORT.md), [receipt](receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json), [generated STATE](generated/STATE.json) | DONE_PUBLISHED / GITHUB_REST_READBACK_VERIFIED; [workflow 38045964668](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38045964668) | SYNTHETIC only, claims REPORTED; idempotent no-op [workflow 38046020069](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38046020069) |


## Найденные в архивных ветках

| ID | Материал | URL | Состояние |
| --- | --- | --- | --- |
| ARC-001 | Archicad full capability audit — index | [INDEX_20260928](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/archicad-full-capability-audit-20260928/research/INDEX_20260928.md) | GITHUB_READBACK_VERIFIED; ссылки на ledger/architecture/tests; эти дочерние документы ещё не проверены |
| ARC-002 | GDL Blocker 1 forensic | [APA_TN-GDL-CREATE-01_BLOCKER1_AUDIT](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-tn-gdl-create-01-blocker1-audit-20261009/docs/research/APA_TN-GDL-CREATE-01_BLOCKER1_AUDIT_2026-10-09.md) | GITHUB_READBACK_VERIFIED; технические утверждения не воспроизведены в этом проходе |
| ARC-003 | Tapir 1.5.10 upstream contract | [tapir-1510-upstream-contract-audit](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-20261009-api-mep-batching-audit/docs/tapir-1510-upstream-contract-audit-20261009.md) | GITHUB_READBACK_VERIFIED; runtime 1.5.10 ≠ автоматически исходники 1.5.9 |
| ARC-004 | Ветка с GDL checkpoint | [research/apa-tn-gdl-create-01-checkpoint-20261009](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-tn-gdl-create-01-checkpoint-20261009) | BRANCH_FOUND; конкретные дельты не прочитаны |
| ARC-005 | Ветка с GDL native probe | [research/apa-tn-gdl-create-01-native-probe-20261009](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-tn-gdl-create-01-native-probe-20261009) | BRANCH_FOUND; дельты не прочитаны |
| ARC-006 | Архив MEP bridges | [research/apa-20261009-resource-mep-bridges-audit-v1](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-20261009-resource-mep-bridges-audit-v1) | BRANCH_FOUND; дельты не прочитаны |
| ARC-007 | Старый независимый индекс | [RESEARCH_INDEX](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-archicad29-independent-audit-20261010/RESEARCH_INDEX.md) | GITHUB_READBACK_VERIFIED; POINTER_ONLY, не полный отчёт |

## Известные пробелы и правила добавления

- Полный итог прежнего Deep Research: **NOT_FOUND_IN_CHECKED_GITHUB_ARTIFACTS**, не заявлять о восстановлении.
- Непушенные локальные файлы: **NOT_VERIFIED / LOCAL_ACCESS_REQUIRED**.
- Наличие файла в GitHub: это только GITHUB_READBACK_VERIFIED. Истинность конкретного API claim требует отдельного SOURCE_VERIFIED/BUILD_PASS/LIVE_PASS.
- Для каждого нового отчёта добавлять: ID, S-ID, прямую ссылку, commit SHA, readback, метод проверки, статус, дату, источник; не дублировать старые документы.
- Если файл существует в архиве, сначала дать ссылку и delta, не создавать копию в другой ветке.


## Восстановленные из чата результаты (2026-10-10)

Эти файлы были восстановлены из видимых отчётов ChatGPT после прежних `GITHUB_PUBLISH_BLOCKED`. **Статус содержания: `RECOVERED_FROM_CHAT / REPORTED`, не независимо перепроверенный SOURCE_VERIFIED**. Для каждого файла отдельно подтверждены GitHub `create_file` commit SHA и `fetch_file` readback.

| ID | Восстановленный отчёт | Commit SHA | GitHub readback | Содержание |
|---|---|---|---|---|
| RECOVER-TAPIR-7C3F | [Tapir: разрезы, размеры, автотекст](runs/2026-10-10/apa-recovery-20261010-132600-tapir-docs-7c3f.md) | [3b5197a](https://github.com/dvikt33-ux/safe-bim-layer/commit/3b5197adb2031b81853fd324d1a7fc93d80bbd46) | PASS, blob `efa84fd335ed1073cd3c8be5353e06d3f62990fe` | Предыдущий исходный аудит Tapir 1.5.9; installed 1.5.10 NOT_VERIFIED |
| RECOVER-HOTLINK-277E19 | [Native Hotlink и MEP Transition](runs/2026-10-10/apa-recovery-20261010-132700-hotlink-mep-277e19.md) | [5e03f46](https://github.com/dvikt33-ux/safe-bim-layer/commit/5e03f4693016977b40dd7cf197bf643cb97ef030) | PASS, blob `e6d3eebacaef09c238009e3eb86823e344d7faa6` | AC29 SDK 29.3100 claims; LIVE NOT_VERIFIED |
| RECOVER-IFCMCP-3F759 | [IfcMCP и IfcPatch MergeProjects](runs/2026-10-10/apa-recovery-20261010-132800-ifcmcp-merge-3f759.md) | [7c42418](https://github.com/dvikt33-ux/safe-bim-layer/commit/7c42418a7f64d827e45aa44b2993a67c0adb66cf) | PASS, blob `1a9cb5f5271d5ce41adc16ff61f728763bd464f7` | IfcOpenShell v0.9.0 claims; OFFLINE/BUILD/LIVE NOT_VERIFIED |

**Что осталось:** не считать восстановление файла независимой технической проверкой или завершением подшага PROJECT_PLAN. Для повышения уровня доказательств назначить отдельный source re-audit по указанным pin/version/line links, затем офлайн/изолированные испытания. Обнаруженные повторы с APA-01…APA-12 и архивом должны быть дедуплицированы по исходникам.


## Полные исходники аудитов из вложений — 2026-10-10

В отличие от нормализованных/сокращённых документов, эти две записи — **полные текстовые снимки приложенных владельцем аудитов**. GitHub readback сравнил каждый текст с исходником посимвольно. **Это проверка факта публикации, а не верификация технических выводов.** Ссылки вида `turn…` и `filecite` в оригиналах являются внутренними маркерами исходного исследовательского ответа и не гарантируют независимую открываемость из GitHub.

| ID | Полный исходник | Источник / объём | Commit и readback | Содержание |
| --- | --- | --- | --- | --- |
| IMPORT-FULL-001 | [APA Research OS — оригинал, 735 строк](runs/2026-10-10/apa-source-snapshot-research-os-full-20261010.md) | Вложение владельца `Вставленный текст.txt`, 2026-10-10; 26 160 символов | [fc8d3e7](https://github.com/dvikt33-ux/safe-bim-layer/commit/fc8d3e7a1c18090dad7f66035f8528f4081ce531); EXACT_GITHUB_READBACK_PASS; blob `6eb98cd428836c8fd73fbd2971e50ca9b24cba94` | USER_SUPPLIED_FULL_SOURCE / технические claims REPORTED; [краткая нормализованная версия](runs/2026-10-10/apa-research-os-audit-user-supplied-20261010.md) существовала ранее, это не новое независимое исследование |
| IMPORT-FULL-002 | [APA Scheduled Task без Work/Codex — оригинал, 715 строк](runs/2026-10-10/apa-source-snapshot-scheduled-task-work-limits-full-20261010.md) | Вложение владельца `Вставленный текст.txt`, 2026-10-10; 31 539 символов | [c3d6945](https://github.com/dvikt33-ux/safe-bim-layer/commit/c3d6945c7972818bb380ccae0ae057488caa1ff8); EXACT_GITHUB_READBACK_PASS; blob `9b96f1f1023ca03d4c1bd7100e8a110f64987a2f` | USER_SUPPLIED_FULL_SOURCE / технические claims REPORTED; практический вывод о write-access обычной Scheduled Task требует отдельного теста именно scheduled execution |

**Что эти записи НЕ закрывают:** все исследования из других чатов, не представленные вложениями или GitHub; полный forensic-аудит уникальных артефактов 72 веток; восстановление утраченных ответов, которых нет ни в источниках, ни в GitHub. Эти пробелы не считать DONE. Исторические отчёты не перезаписывались, `main` не менялся.


## APA-P10.A01.S01 — recovery after blocked publication (2026-10-10)

| Artifact | Task | File | Evidence | Commit | Readback |
|---|---|---|---|---|---|
| `ART-SDK-RECOVERY-20261010-6B42` | `APA-P10.A01.S01` — PARTIAL | [Native Create/Change/Get recovered report](runs/2026-10-10/apa-recovery-20261010-142600-sdk-native-6b42.md) | **REPORTED_FROM_PRIOR_CHAT**; SOURCE re-audit pending; OFFLINE/BUILD/LIVE NOT_VERIFIED | [1489a2de](https://github.com/dvikt33-ux/safe-bim-layer/commit/1489a2debc8b547632be6ff9604ee9f49d206ff9) | PASS, blob `ebfa50e7b72bc27dff84276a4baf2b834a991b33` |

Controller: task switched from `IN_PROGRESS` to `PARTIAL`, owner/claim/lease cleared and artifact registered via [commit 3789812](https://github.com/dvikt33-ux/safe-bim-layer/commit/378981212a11f9a2b9a024c0afaa1c347a490826). The earlier V1 inbox request was retired after the direct report was saved: no V2 receipt or DONE_PUBLISHED asserted. This preserves research content rather than misclassifying unverified API findings as completed.


## APA-P10.A02.S04 — MEP route/port/source matrix (2026-10-10)

| Artifact | S-ID | Immutable source report and receipt | Evidence / acceptance | Publication |
|---|---|---|---|---|
| `ART-MEP-SOURCE-20261010-PORTGRAPH` | `APA-P10.A02.S04` (`PARTIAL`) | [SOURCE matrix](runs/2026-10-10/APA-RUN-20261010-200823Z-mep-route-port-gate/REPORT.md), [V2 receipt](receipts/APA-RUN-20261010-200823Z-mep-route-port-gate.json) | **SOURCE_VERIFIED** from pinned Tapir 1.5.9 `MEPCommands.cpp` and Graphisoft DevKit 29.3100; OFFLINE/BUILD/LIVE NOT_VERIFIED, installed Tapir 1.5.10 parity NOT_VERIFIED | [V2 report/index commit 4e4fe2f](https://github.com/dvikt33-ux/safe-bim-layer/commit/4e4fe2f9320f949058f56981ac77e0f5d2d4d4b0); GitHub receipt `readback_verified=true`, `indexed=true`; [controller revision 25 update f9e9a58](https://github.com/dvikt33-ux/safe-bim-layer/commit/f9e9a58f6d14194abb06072575e39c5afde5a294), GitHub readback PASS |

Verified novel source details: distribution system membership != physical port connectivity; `GetMEPPorts` can silently skip unreadable ports; `ConnectLogically` can report deleted/split/branch route GUIDs. Existing related MEP capabilities are not reinvented. Controller task claim was released with `PARTIAL`; publication receipt status `DONE_PUBLISHED` concerns the report, **not** full technical task completion. Slack: https://w1791579305-0gy426514.slack.com/archives/C0C886E1PGR/p1791663171104129


## Native SDK writer source re-audit — 2026-10-10 20:14 UTC

| Artifact | Task | Source report | Publication | Verification |
|---|---|---|---|---|
| ART-SDK-SIGNATURE-AUDIT-20261010-201457 | APA-P10.A01.S01 / PARTIAL | [AC29 Create/GetMemo/Change/Undo source matrix](runs/2026-10-10/apa-discovery-20261010-201457-sdk-native-signatures-fallback.md) | [commit 3197659](https://github.com/dvikt33-ux/safe-bim-layer/commit/3197659f0548dee4d5c6b3e053e2715d53a16557) | Report GitHub readback PASS, blob b295ef7a0b1e963d7d9c8503d024ebc24482ab09 |

Direct source: pinned Graphisoft DevKit 29.3100 Command/Memo Doxygen and Tapir 1.5.9 call sites. Findings: batch per-item failure treatment; unchecked GetMemo error before ModifyObjects/ModifyLamps application; unchecked selected Favorites/AutoText snapshot/restore codes. **No crash or live write claimed.** Actual SDK29 header declarations and installed Tapir1.5.10 parity remain NOT_VERIFIED. Auto V2 publisher did not supply a receipt before fallback; inbox was retired only *after* this complete report had GitHub readback. Controller status written by [commit 46abf6d](https://github.com/dvikt33-ux/safe-bim-layer/commit/46abf6d6ff77f45bfb8155b7188009fc1cebec2d), revision 27, IN_PROGRESS → PARTIAL and claim cleared. If a V2 representation appears later, deduplicate by original run_id APA-RUN-20261010-201457Z-sdk-native-signatures.


## APA-P20 — сохранённый павильон, независимый API-readback 2026-10-11

| Artifact ID | Задача | Доказательство | Статус |
|---|---|---|---|
| `ART-APA-PAVILION-SAVED-READBACK-20261011` | `APA-P20.A02.S03` (controller task still BLOCKED) | [12/12 readback report](runs/2026-10-11/apa-p20-a02-s03-saved-pln-live-readback-20261010-222136.md), [commit 1e21c3a](https://github.com/dvikt33-ux/safe-bim-layer/commit/1e21c3aaa9541f03918372ad479621b0457a3018), uploaded JSON SHA-256 `593e637bfe738e5baac979d5cc897f49e1b0d23a4ae431b7f06468c0e829ecd5` | `GITHUB_READBACK_VERIFIED` for Markdown report; user-supplied `SAVED_COPY_LIVE_READBACK_PASS`, 12/12 native GUID/geometry/host checks, 0 write; operator explicitly attested **saved-copy close → reopen → read-only audit**, so **PERSISTENCE_REOPEN_PASS_REPORTED_WITH_LIVE_READBACK** (not independently witnessed/file-binary parsed); [attestation evidence commit 015a96e](https://github.com/dvikt33-ux/safe-bim-layer/commit/015a96e194930577b5b9f138077b4c04a6eb308e). Source JSON attachment not itself a GitHub blob. |



## APA-P10.A01.S02 — Native stories/attributes, Basic/Composite slab blocker (2026-10-11)

| Artifact ID | Task | Source | Verification |
|---|---|---|---|
| `ART-APA-ATTR-STORY-SLAB-20261011` | `APA-P10.A01.S02` / **PARTIAL** | [Typed AC29 story/material/composite/profile matrix](runs/2026-10-11/apa-p10-a01-s02-typed-attributes-stories-readback-slabs-20261011.md), [commit 6b82b52](https://github.com/dvikt33-ux/safe-bim-layer/commit/6b82b52cbc65a661f49cbf1f01fe3bea8846d559) and [source-audit crosslink 569c9fd](https://github.com/dvikt33-ux/safe-bim-layer/commit/569c9fd7ab37373a017819e0dbd6ce5376b45387) | `GITHUB_READBACK_VERIFIED`, installed v1.5.10 per user reports, Basic/Composite failure+repair `USER_LIVE_API_REPORT_CHECKED`; upstream [Tapir PR #785](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785) source-diff verified but OPEN/unmerged, APX parity NOT_VERIFIED |
| `ART-APA-TYPED-SLAB-PROPOSAL-20261011` | Candidate only, independent audit pending | [Proposal Basic/Composite slab capability adapter](control/proposals/APA-CAND-20261011-typed-slab-creation-adapter.md), [commit 4cd117a](https://github.com/dvikt33-ux/safe-bim-layer/commit/4cd117a91cfec38cc12eaf03d2f1bd195c67a821) | `GITHUB_READBACK_VERIFIED`, **not yet included** in `control/PROJECT_PLAN.json`, no implementation/build/live claimed |



## APA-P50.A02.S01 — Antidup source audit of existing APA infrastructure (2026-10-11)

| Artifact | Task | GitHub source + provenance | Acceptance limit |
|---|---|---|---|
| `ART-APA-REUSE-NATIVE-20261011` | `APA-P50.A02.S01` / PARTIAL | [Proof of existing intent→BIM graph→SceneWriter, older CreateSlabs→ModifySlabs Basic material route, material dependency resolver and series178 floor emitter](runs/2026-10-11/apa-p50-a02-s01-anti-dup-native-geometry-pipeline-audit.md), [commit 01ec66d](https://github.com/dvikt33-ux/safe-bim-layer/commit/01ec66d7cfbe3e1490c6add1556533731518a0d8) | `SOURCE_VERIFIED / GITHUB_READBACK_VERIFIED`; no fresh native live test; not exhaustive 72-branch dedup; **do not build duplicate adapter** |
| `ART-APA-REUSE-RESCOPE-20261011` | Candidate review warning; not admitted task | [Existing typed slab proposal with rescope warning](control/proposals/APA-CAND-20261011-typed-slab-creation-adapter.md), [commit 2289345](https://github.com/dvikt33-ux/safe-bim-layer/commit/2289345e73dae9b150bbf62f1da856dede301d23) | Needs independent auditor to approve/rescope/reject; `PROJECT_PLAN` task not created |



## APA-P00.A02.S03 / S04 — Slack historical SQLite recovery and HTTP readback (2026-10-11)

| Artifact ID | Task linkage | GitHub report | Verified gate / still pending |
|---|---|---|---|
| `ART-APA-SYNC-HISTORY-20261011` | Existing `APA-P00.A02.S03` evidence reconciliation; `APA-P00.A02.S04` publication completeness; **no controller claim or status mutation** | [LIVE Socket Mode historical backfill + independent local API readback](runs/2026-10-11/apa-sync-live-sqlite-history-recovery-20261011.md), [strict parser PR #33](https://github.com/dvikt33-ux/safe-bim-layer/pull/33), [CI 44/44 PASS](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38091580453) | **USER_LOCAL_LIVE_READBACK_PASS**: Slack history 28 scanned, 20 new SQLite accepts, 1 duplicate, 3 malformed rejects; API `EVENTS_TOTAL=21`, `ORIGINAL_SMOKE_PRESERVED=True`, 16 state keys, `EFFECTIVE_CONFLICTS=0`, cursor 21. **Restart idempotence LIVE_PASS** from owner-local 02:33 rerun: 0 accepted, 21 duplicates, 0 conflicts, 3 malformed rejects; **post-second-restart API readback LIVE_PASS**: 21 rows, cursor 21, 16 states, original smoke seq1 preserved; manual source audit of three malformed Slack messages pending; `LIVE BLOCKED` claim remains a distinct recorded status, no Archicad LIVE upgrade. |

This row indexes user-supplied logs verified for internal consistency by independent read-only HTTP calls on the owner's local machine. GitHub publication/readback of the report **does not** imply each historical technical result was independently re-audited, nor does it change the canonical `PROJECT_PLAN.json` dispatch state.

## APA-P00.A02.S03 — три отклонённых Slack-сообщения: SOURCE reconciliation (2026-10-11)

| Artifact ID | Отчёт, immutable V2, проверяемая публикация | Содержание и статус |
| --- | --- | --- |
| `ART-APA-SLACK-THREE-RECON-20261011` | [REPORT.md](runs/2026-10-10/APA-RUN-20261010-234200Z-slack-legacy-three-audit/REPORT.md), [manifest](runs/2026-10-10/APA-RUN-20261010-234200Z-slack-legacy-three-audit/manifest.json), [V2 receipt](receipts/APA-RUN-20261010-234200Z-slack-legacy-three-audit.json), [generated index](generated/INDEX.md) | **V2 GITHUB_READBACK_VERIFIED / indexed=true / receipt DONE_PUBLISHED**. Зафиксированы 3 rejected Slack формы, структурный дефект каждой, source URL, semantic superseded_by для тестового smoke, дубликат publisher digest, частично сохранённый исторический PR audit. **Техническая задача S03 остаётся PARTIAL**, 72-branch dedup ещё не завершён. |
 
**Прямой проверенный контекст:** [LIVE Slack→SQLite backfill + повторный restart + API](runs/2026-10-11/apa-sync-live-sqlite-history-recovery-20261011.md), [publisher deployment](deployments/APA_PUBLISHER_DEPLOYMENT_20261010.json), [publisher receipt](receipts/APA-RUN-20261010-104437Z-publisher-integration-smoke.json), [branch inventory](inventories/FULL_BRANCH_INVENTORY.md). 

**Link erratum for immutable V2 REPORT:** the generated report's relative link `../apa-sync-live-sqlite-history-recovery-20261011.md` is relative to its 2026-10-10 immutable run directory and is non-resolving. Correct source is the **2026-10-11** [LIVE recovery report](runs/2026-10-11/apa-sync-live-sqlite-history-recovery-20261011.md) above. Do not rewrite immutable V2 bytes after the GitHub readback receipt; this registered note is an append-only correction.

**Provenance limit:** Message TS values in immutable report originate from Slack connector rendering; owner raw Slack diagnostic independently confirmed counts/shapes, not TS-to-raw-bytes mapping. No retroactive `APA_EVENT_V1` import, no Slack/SQLite/PLN/APX mutation, no promotion of offline SOURCE claims to Archicad LIVE. Existing `APA-P00.A02.S04` governs a separate publication-audit gate.

## APA-P00.A02.S03 — 72 branch head aliases and 13 ancestry/diff checks (2026-10-11)

| Artifact ID | Task / source | Published proof and limits |
| --- | --- | --- |
| `ART-APA-BRANCH-DEDUP-20261011` | `APA-P00.A02.S03` (**PARTIAL**; owner claim to be released) | [Machine-readable 72-branch snapshot dedup matrix](inventories/BRANCH_DEDUP_MATRIX_20261011.json) (commit `df6c8c98`, GitHub readback PASS), [immutable V2 source audit](runs/2026-10-10/APA-RUN-20261010-235301Z-branch-evidence-dedup/REPORT.md), [manifest](runs/2026-10-10/APA-RUN-20261010-235301Z-branch-evidence-dedup/manifest.json), [V2 publication receipt](receipts/APA-RUN-20261010-235301Z-branch-evidence-dedup.json). GitHub receipts `DONE_PUBLISHED / readback_verified=true / indexed=true`, report content was checked against original inbox request. Exactly **72 snapshot branches, 69 unique HEAD SHA, 2 duplicate-head alias groups, 3 redundant branch-name pointers**, plus **13 direct GitHub pair comparisons**: 3 identical, 8 ahead, 2 diverged. **Snapshot only**: does not certify that current GitHub still has exactly 72 branches or that 69 trees have been fully audited. |

**Critical KEEP/DO-NOT-REIMPLEMENT:**
- Two research refs `research/apa-20261009-api-mep-batching-audit` / `research/apa-20261009-resource-mep-bridges-audit-v1` are exact alias HEADs to `feature/project-accelerator-integration-pr-20261009`. `arena/tapir159-compat-geometry-c6ab474` is an exact alias to `arena/fix-house-offline-audit-f7d38af`. Proven direct compare status `identical`; no deletion authorized.
- Stage 4 Performance remains a frozen accepted optimization benchmark; Stage 5 Hosted Window is a **descendant** with additional code, but its live W08-W10 gates remain `NOT_VERIFIED`, despite OFFLINE tests PASS. Do not relabel as live-capable.
- GDL/TN blocker1 native-probe branch **extends** checkpoint/audit and includes prepared read-only diagnostic patch plus tests. Installed APX presence and full resolution of the 92 GDL errors **not verified**.
- Two different `detail-machine ... v2.3` branches have **diverged**: KAIMAN/KERAKAM source bindings vs ROCKFACADE source corpus. They are not safe duplicates just because both say v2.3. Preserve both. KAIMAN v2.5 also adds unique WT1.3 bindings, still fail-closed.

**Source status:** direct Git SHA/commit ancestry/file list checks are `SOURCE_VERIFIED`. Historic benchmark and geometry-binding results from existing release JSON are `REPORTED` and were not rerun. The six previously claimed missing research filenames remain `NOT_VERIFIED` globally because their exact names and exhaustive tree search were not established. This item is part of `APA-P00.A02.S03` and `APA-P50.A01.S01`, with downstream reuse for `APA-P70.A01.S02`, `APA-P70.A03.S02`, `APA-P70.A04.S01`; not a new S-ID.

## APA-P00.A02.S03 — 83 branches / 80 fully read Git trees, source archive preservation index (2026-10-11)

| Artifact ID | Report and canonical indexes | Measured result and outstanding gate |
| --- | --- | --- |
| `ART-APA-BLOB-CENSUS-83-20261011` | [Published V2 REPORT](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-001922Z-eighty-head-blob-inventory/REPORT.md), [V2 manifest](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/runs/2026-10-11/APA-RUN-20261011-001922Z-eighty-head-blob-inventory/manifest.json), [V2 receipt](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/receipts/APA-RUN-20261011-001922Z-eighty-head-blob-inventory.json) | **GITHUB_READBACK_VERIFIED, receipt DONE_PUBLISHED, indexed=true.** Snapshot 83 branches, 80 distinct HEAD with complete non-truncated Git trees; **14,920** file occurrences → **1,578** different Git blob SHA, **1,594** paths and **1,748** unique path/SHA pairs. **422** blob SHA in only one head, **44** identical SHA across paths, **91** paths with multiple versions. Semantic correctness and LIVE runtime not established. |
| `ART-APA-SOURCE-71-INDEX-20261011` | [Pinned SHA/permalink index of 71 original MD/JSON reports](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/ARCHICAD29_TAPIR159_SOURCE_INDEX_20261011.json); [exact byte-overlap snapshot](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/CANONICAL_BLOB_COVERAGE_20261011.json); [TASK_PROPOSAL_V1 on future source migration](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/proposals/APA-CAND-20261011-source-archive-71.md) | **SOURCE_LINKS_VERIFIED_NOT_COPIED.** All 71 source file SHA absent from byte-exact canonical snapshot; historical research still available in `research/archicad29-tapir159-expansion`. **Bulk transfer did not take place:** attempted low-level write blocked. This index is not the actual text archive, and older Tapir 1.5.9 conclusions require 1.5.10/current-runtime review. Proposal is **PENDING_AUDIT**, not an executable S-ID. |

### Machine provenance — absolute links (correcting immutable V2 relative-link paths)

- [Current 83-branch census](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/CURRENT_BRANCH_HEADS_20261011.json)
- [Full 80-HEAD aggregate](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/CURRENT_BLOB_AGGREGATE_20261011.json)
- [422 single-HEAD blob SHA](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/CURRENT_BLOB_EXCLUSIVE_20261011.json)
- [Blob same-content / path-version collisions](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/CURRENT_BLOB_COLLISIONS_20261011.json)
- [New or changed HEAD batches 01](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/CURRENT_DELTA_BATCH_01.json) and [02](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/CURRENT_DELTA_BATCH_02.json)
- [Seven historical head batches](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/BATCH_01.json) through [BATCH_07](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/inventories/blob-scan-20261011/BATCH_07.json)

**Immutable V2 link erratum:** Some relative links in `runs/2026-10-11/APA-RUN-20261011-001922Z-eighty-head-blob-inventory/REPORT.md` begin `../inventories/blob-scan-20261011`. Relative to the immutable V2 run directory these do not resolve. The absolute GitHub links above are the canonical working links. Do **not** rewrite receipt-verified immutable REPORT.md bytes to repair links; this register section is an append-only correction.

**Task status:** `APA-P00.A02.S03` remains **PARTIAL** until content-level deduplication and preservation review. `main`, PLN, APX, Archicad, Slack Socket Mode and SQLite not modified.
