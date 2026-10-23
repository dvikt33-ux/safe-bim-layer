# APA — Slack ↔ Controller ↔ GitHub gap audit (2026-10-11)

**Type:** SOURCE_REVIEW + prior user-observed LIVE transport evidence. **Status:** PARTIAL / PROPOSAL_ONLY. Not a Scheduled task claim; no controller task state changed. No main/master/PLN/APX mutation.

## Authoritative sources checked
- [Slack-to-SQLite E2E](apa-sync-live-message-delivery-e2e-20261011.md), commit [499e1dc](https://github.com/dvikt33-ux/safe-bim-layer/commit/499e1dcbc3ae17f96247be9c5bab04264d61b610): unique INFO event `apa-sync-e2e-20261011-1517-6c7e` is in Slack and user-retrieved local SQLite as seq22/cursor22, conflict=false.
- [Socket Mode receiver](https://github.com/dvikt33-ux/safe-bim-layer/blob/3bdf572b27b27a27335f24336625777f189fec4d/scripts/apa_sync/socket_mode.py): `capture_event` validates channel/subtype, calls `store.ingest`; it does not call GitHub APIs, claim controller tasks, or publish an outgoing Slack notification.
- [SQLite coordinator](https://github.com/dvikt33-ux/safe-bim-layer/blob/3bdf572b27b27a27335f24336625777f189fec4d/scripts/apa_sync/coordinator.py): append-only, deduplicated event ledger, loopback read API `/health`, `/v1/changes`, `/v1/state`, `/v1/wait`; no authenticated write or GitHub dispatcher in checked module.
- [Local step synchronization](https://github.com/dvikt33-ux/safe-bim-layer/blob/3bdf572b27b27a27335f24336625777f189fec4d/scripts/apa_sync/step_sync.py): `before_step` reads Slack history; `after_step` posts only on explicit `--publish`; command is not an always-on GitHub reconciliation worker.
- [Project Controller](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/tools/apa_controller/controller.py): GitHub/controller file-based DAG and claim validation, no observed Slack bridge in checked source.
- [Publisher workflow](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/.github/workflows/apa-research-publisher.yml): push-triggered canonical-branch publisher, no Slack outgoing step; not an autonomous Scheduled Task initiator.
- [Canonical PROJECT_PLAN revision 49](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-verified-results-hub-20261010/docs/research/apa-results/control/PROJECT_PLAN.json): policy `trigger` allows research work initiation only by user-configured ChatGPT Scheduled Tasks. `APA-P60.A02.S03` is concurrency/claim test, `S04` proposal admission, neither expressly implements Slack evidence→GitHub notification bridge.

## Verified capability matrix
| Chain | Level | Evidence / gap |
| --- | --- | --- |
| ChatGPT send → Slack readback | LIVE PASS | direct send and separate channel readback |
| Slack Socket Mode → SQLite → local HTTP | LIVE PASS | independent owner HTTP seq22/cursor22, no conflict on event |
| Local client read Slack before work | SOURCE IMPLEMENTED, local invocation NOT VERIFIED here | explicit CLI, requires bot token |
| Local client post Slack after work | SOURCE IMPLEMENTED, local invocation NOT VERIFIED here | opt-in `--publish` CLI |
| Slack accepted event → automatic Github Controller validation/proposal | NOT IMPLEMENTED IN INSPECTED BRIDGE | receiver only ingests |
| GitHub Controller/Publisher receipt → automatic Slack notification | NOT IMPLEMENTED IN INSPECTED WORKFLOW | no outgoing Slack step |
| Slack triggers unattended research | NOT ALLOWED under current policy | only ChatGPT Scheduled trigger is allowed |
| Restart and replay | prior LIVE PASS for 21-record historical dataset | 22-record fresh restart NOT VERIFIED |
| Publisher CI source validation | CI PASS for prior test update | Actions workflow rerun 38139685031 attempt 2 SUCCESS; first attempt push race; not a Slack controller E2E |

## Gap / minimal next engineering slice
Add a **single narrow, evidence-oriented bridge** aligned with existing architecture: read accepted SQLite event envelopes from a cursor; verify a pinned allowed GitHub artifact/report/receipt and provenance; surface untrusted Slack claims as **candidate evidence**, never authoritative task status. Outgoing notifications of verified canonical commits/receipts may use an idempotent sender. Never infer `DONE_PUBLISHED` from INFO, PASS, or status fields in Slack. Do not create a second controller or enable Slack-triggered ChatGPT research; Scheduled Tasks remain the only research trigger unless owner explicitly approves changing policy.

Minimal offline gates: parser and evidence allowlist, cursor resume, source SHA check, unique event-id/dedup, repeated delivery, rejected invalid URLs, failure/retry handling, no token logging, no unauthorized controller mutation. Minimal E2E gate: accepted event linked to verified existing GitHub artifact → explicit adjudication/controlled proposal (no task status promotion) → safe outgoing ack/event → Slack readback → SQLite dedup, with independent receipts. User's Windows runner test is a separate LIVE gate, not implied by CI.

## Task de-dup / next action
Potential candidate `APA-CAND-20261011-slack-evidence-bridge` under `APA-P60.A02`. Review `APA-P00.A03.S03` (publisher/recovery), `APA-P60.A02.S03` (concurrency), `APA-P60.A02.S04` (proposal admission), `APA-P40.A01.S01–S04` (autonomy) before approval. Candidate is **NOT** a registered S-ID, not READY/IN_PROGRESS/DONE, no claim or assignment. Full hands-off bidirectional synchronization remains NOT_VERIFIED.
