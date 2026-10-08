# ChatGPT -> BIM graph -> existing Mailbox (offline adapter)

> **Current installed runtime (2026-10-09): Archicad 29.2.1 (5101) RUS FULL (x86-64).** The loaded add-on/API version must be independently confirmed after the application update. Canonical record: [ARCHICAD_RUNTIME_CURRENT.md](ARCHICAD_RUNTIME_CURRENT.md).


Status: adapter source and offline tests are published. This is a protocol
adapter; it **does not publish** jobs, execute model changes, or extend
the installed local worker by itself.

## What the adapter accepts today

- A plan passed through `archicad_bim_graph.py`, including ordering and
  dependency checks. No unknown/invalid command is silently ignored.
- An exact Archicad target object (port, instanceId, logicalProjectId,
  projectName, projectPath). The **local worker** must still recheck identity
  before every write; the sender's values alone never prove the live target.
- A stable unique `run-id`, used together with the complete canonical plan
  and step ID to derive a repeatable operationId/messageId.
- Existing complete `RESULT` objects, as published by the local bridge.
  The adapter verifies the JSON payload hash, message correlation, target
  fingerprint, operationId and factual wall read-back.

**Only `create_wall_v1` is eligible for conversion to a Mailbox JOB.**
The confirmed local writer accepted this recipe for Archicad 29 with
Tapir 1.5.10. The schema is still pinned to Tapir 1.5.8, and no other
recipe is promoted to executable status merely because it validates offline.

## Prepare a dry-run job (no publishing)

Prepare a separate `target.json` on your computer:

```json
{
  "instanceId": "archicad-19723",
  "logicalProjectId": "YOUR_CURRENT_BOUND_PROJECT_ID",
  "port": 19723,
  "projectName": "YOUR EXACT TEST PROJECT NAME",
  "projectPath": "C:\\Path\\To\\Your Test.pln"
}
```

Then:

```powershell
python scripts/archicad_mailbox_graph_adapter.py `
  --graph examples/archicad_bim_graph.offline.sample.json `
  --target target.json `
  --run-id unique-test-001 `
  --mode dry-run `
  --output "$env:TEMP\graph-preview.json"
```

The current three-element example contains a Wall, Slab and Window.
The adapter can preview the first Wall request but **refuses live execute
mode for the whole graph**, because a tested Slab/Window Mailbox recipe is
not yet deployed locally. This avoids creating half a building fragment.

For a supported example, a graph of only Walls can progress one step at
a time. The adapter emits `NEXT_JOB_PREVIEW` with the exact `JOB` envelope
and destination `safe-bim-mailbox/gpt-live/inbox/<messageId>.json`.
**No file is uploaded.** Publication remains a separate explicit
operation, controlled by GitHub permissions and local write policy.

Use the same run ID and unchanged graph for each subsequent step. Feed
published RESULT envelopes as an array with `--results results.json`.
Only matching, geometry-verified `PASS` results advance to the next step.
Non-PASS outcomes return STOP; no automatic retry.

The adapter cannot determine if a JOB has been published but has not yet
returned a RESULT. Do **not** regenerate or submit the same operation
with another ID while outcome is unknown. An altered timestamp with the
same messageId is a remote identity conflict. Preserve the initially
generated envelope.

## Why it is split

1. **Schema** validates command shapes.
2. **Graph** orders dependencies and type-checks owner links.
3. **Mailbox adapter** derives a single typed, non-submitted request and
   checks previous RESULT evidence.
4. **Local trusted executor** must perform project rebinding, replay
   protection, pre-write checks, native API calls, and geometry read-back.

This prevents generic schema validation from becoming an unsafe arbitrary
write gateway. It also means a successful offline test is not proof of a
working end-to-end Slab, Window or MEP writer.

The next implementation milestone is to bring the proven local Mailbox
write source into a reviewable feature branch and add **typed recipes**
for Slab and hosted Window, plus representative end-to-end tests in the
designated test PLN. No 600-command manual test campaign.
