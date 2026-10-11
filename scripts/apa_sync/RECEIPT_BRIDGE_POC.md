# APA Slack ↔ GitHub evidence bridge — isolated prototype

## Proven, and not proven

- This prototype only **reads** existing local APA event ledger, pinned GitHub controller snapshots and immutable publisher receipts.
- It validates that a receipt is recorded as `kind=RECEIPT` in the **specific task's `evidence`** list in the pinned `PROJECT_PLAN.json`, that its `indexed/readback_verified` values are true, and that its immutable report matches the receipt's SHA256 and names the task.
- It prepares an `APA_EVENT_V1` `INFO/SOURCE` Slack notification from verified receipt data. Actual Slack sending requires explicit `notify ... --publish` and a locally configured existing bot. Before sending, it searches existing channel history for the deterministic event ID to avoid common repeated messages. A crash in the post/receipt interval remains *at least once*, not proven exactly once.
- It never changes GitHub task status, leases, claims, plan revision, executes research, starts a daemon, touches Archicad or changes the running Windows Socket Mode.
- **No Windows LIVE proof** for this proposed module; existing Slack→SQLite seq22 LIVE proof belongs to the original receiver.

## Offline tests

From the repository root on Python 3.11+:

```powershell
python -m unittest discover -s tests -p test_receipt_bridge.py -v
```

Tests use fabricated pinned plan, receipt and report in memory, with no network, Slack token, filesystem side effects or GitHub writes.

## Opt-in commands (do not execute in the existing Socket Mode shell)

Provide a real 40-hex **commit SHA** of the canonical research branch, not a floating branch name. `GITHUB_TOKEN` is optional for public repo and must be supplied as a local process environment secret if needed; never write it to GitHub or paste it into chat.

```powershell
python -m scripts.apa_sync.receipt_bridge --plan-commit <40-hex-GitHub-commit> scan --after 21
python -m scripts.apa_sync.receipt_bridge --plan-commit <40-hex-GitHub-commit> notify --task-id APA-P70.A01.S01 --receipt-path docs/research/apa-results/receipts/APA-RUN-20261011-091905Z-p70-source-integration-map.json
```

The second command is **dry-run**. The explicitly opted-in outbound send appends `--publish` to `notify`. The command fails closed if an audit receipt or its registered task/report evidence fails verification. Do not send a message for an arbitrary Slack claim.

## Controller change boundaries

Any future automation of this module must pass independent audit and authorization of deployment rights, credential isolation, rate limiting, restart and failure semantics. The actual `PROJECT_PLAN.json` status and Scheduled Task dispatch policy continue to be the sole authority. This is a bounded source-code POC in a new branch, not the admission of provisional `APA-P60.A02.S05` to READY.
