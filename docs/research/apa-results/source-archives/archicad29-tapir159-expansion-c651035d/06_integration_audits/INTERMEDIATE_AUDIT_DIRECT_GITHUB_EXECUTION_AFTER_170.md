# INTERMEDIATE AUDIT — DIRECT GITHUB EXECUTION AFTER PASS 170

Date: 2026-09-28

## Confirmed feasible

- ChatGPT can durably publish machine-readable work to GitHub.
- Existing local dispatcher architecture already proves monotonic GitHub state polling with de-duplication and local persisted state.
- Safe BIM can treat GitHub as an asynchronous command transport without making GitHub part of the BIM write transaction.
- Conditional polling is sufficient for an initial near-real-time experience without requiring an inbound public endpoint on the user's PC.

## Main architectural correction

The user request should not map directly to arbitrary code execution.

Required chain:

```text
user request
 -> ChatGPT planning
 -> immutable Safe BIM job envelope
 -> GitHub private queue
 -> local intake
 -> local current-state reconciliation
 -> preview/checkpoint/sandbox policy
 -> Safe BIM runtime
 -> result/evidence publication
```

## Blocking safety requirements before any automatic execution

1. Private queue repository or otherwise isolated private command channel.
2. Exact project identity in each job.
3. Source snapshot/root hash binding.
4. Exact target preconditions/state hashes when applicable.
5. Monotonic job sequence + once-only local admission.
6. Existing single-flight runtime lock.
7. No automatic retry after uncertain write.
8. `RAW_CODE` cannot auto-run.
9. Credentials stored outside APX/UI.
10. Local authoritative re-check immediately before BIM mutation.

## Latency/load audit

Expected perceived latency for polling design is dominated by the poll interval, not model processing.

A single tiny queue-head conditional request every few seconds is materially lighter than exporting model state or pulling an entire repository. The GitHub REST API also has secondary content-generation limits; therefore execution status should be coalesced rather than committing every internal micro-state transition.

## Important separation

There are now two GitHub flows:

### Project context flow
`Archicad -> private state repo -> ChatGPT`

### Job flow
`ChatGPT -> private command queue -> Safe BIM`

They may live in one private repository for a prototype, but logically and permission-wise they should remain separate. For production, separate state and command permissions are preferable.

## Intermediate verdict

**FEASIBLE FOR PROTOTYPE: YES**

**SAFE FOR AUTOMATIC BIM WRITE TODAY: NO**

Reason: transport architecture is proven enough, but the command envelope, credential isolation, local admission layer, and stale-context gate have not yet been implemented/live-certified as one system.
