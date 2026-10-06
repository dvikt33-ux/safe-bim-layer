# Branch Inventory — 2026-10-06

This is a cleanup inventory, not an instruction to delete branches immediately.

## Active

- `work/stage4-live-hardening` — current Archicad closed-loop reliability work.

## Milestone branches already contained in Stage 4 history

GitHub comparison against the active Stage-4 branch showed these branches with
`behind_by = 0`: their commits are already ancestors of the current line.

- `work/stage1-v0-regression`
- `work/stage2-orchestrator-skeleton`
- `work/stage3-live-wall-closed-loop`
- `work/audit-pack-fix`
- `work/evidence-storage-lfs`
- `chatgpt/closed-loop-orchestrator-v1`

They remain useful named milestones/evidence anchors. After Stage 4 is frozen, they are
candidates for tags plus optional remote-branch cleanup; no information needs to be
rediscovered from them.

## Diverged branches with unique work — preserve until migrated/audited

### Archicad capabilities / modeling

- `archicad-capability-registry` — unique capability-roadmap/registry work.
- `chatgpt/minimal-archicad-inventory` — unique inventory work.
- `research/archicad-full-capability-audit-20260928` — broad capability research.
- `chatgpt/archicad-modeling-standard-v1` — modeling/QA standard and PR-line work.
- `research/archicad29-tapir159-expansion` — older Tapir/Archicad capability expansion.

### Consolidation / migration

- `chatgpt/project-revision-consolidation-20261006` — unique migration matrix/contracts;
  preserve until its useful records are moved into the canonical current docs/data.

### Bridge generations

- `feature/chat-bridge-wall-write-mvp`
- `feature/gpt-direct-bridge-20261002`
- `feature/gpt-mailbox-write-path-20261005`

These are strongly diverged and contain unique bridge/write-path history. They should not be
deleted merely because the closed-loop branch is newer. First extract any still-useful
transport/runtime ideas into an explicit migration record.

### Arena / earlier runtime generations

The Arena runtime, house primitives, T0 probes and counter-audit branches are all strongly
diverged. Examples:

- `arena/runtime-hardening-v1`
- `arena/runtime-safety-fix-ac01`
- `arena/t0-probes`
- `arena/house-primitives-offline-ebbe779`
- `arena/fix-wall-readback-z-14bc0d2`
- `arena/fix-house-offline-audit-f7d38af`
- `audit/arena-full-system-audit-20260928`
- `audit/arena-reconciliation-gpt-counter-audit-20260928`
- `audit/gpt-counter-audit-arena-20260928`
- `audit/live-r0-r4-20260928`

Treat these as historical implementation/research sources until the consolidation matrix
proves their useful capabilities have been migrated.

## Other product/design streams — separate domain, not Stage-4 clutter

Branches such as:

- `chatgpt/project-intake-stage0-v1`
- `work/planning-engine-v0`
- `work/design-engine-stage0`
- constraint/site/design-intent/normative-bundle branches
- construction-detail / detail-machine / KAIMAN branches

belong to project intake/design/normative/detail-machine work. Do not delete them as part of
Archicad closed-loop cleanup; they need their own consolidation policy.

## Likely disposable branch

- `chatgpt-write-test` — its unique tip commit is only
  `test: verify ChatGPT connector write access` and adds `chatgpt-write-test.txt`.

This is the strongest current deletion candidate, but remote branch deletion should still be
a deliberate cleanup action, not bundled into Stage-4 verification.

## Main branch observation

At this audit, `main` had advanced to `d5695f435a5841d39f0fe69a6424cccc1c8d0a4c`
with a single independent construction-detail-machine commit under
`knowledge/detail-machine/`. The Stage-4 branch did not contain that main commit.

This exposed a bad acceptance assumption: checking that the **entire main SHA never changes**
is too broad. Stage 4 now guards protected runtime/evidence paths against its historical
merge-base instead.

## Cleanup order for branches

1. Finish and freeze Stage 4.
2. Create durable tags for milestones that need permanent names.
3. Consolidate unique Archicad capability/research branches into the migration matrix.
4. Consolidate old bridge/Arena runtime knowledge.
5. Delete only branches proven redundant after migration.
6. Keep separate product/design/normative/detail-machine streams under their own policy.
