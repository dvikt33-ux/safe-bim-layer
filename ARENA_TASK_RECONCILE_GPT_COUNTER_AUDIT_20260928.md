# ARENA TASK — reconcile GPT counter-audit

Date: 2026-09-28

Read first:

- `GPT_COUNTER_AUDIT_ARENA_20260928.md`
- the six Arena reports inherited on this branch from `audit/arena-full-system-audit-20260928`

## Goal

Run another adversarial targeted cycle against GPT's counter-audit. Do **not** merely agree with it and do not repeat the entire previous audit. Attack the newly disputed items with exact Tapir 1.5.9 source, official Archicad 29 API documentation, and normative GOST/SPDS source where relevant.

Required method:

`AUDIT -> targeted PASSES -> AUDIT -> targeted PASSES -> FINAL AUDIT`

Repeat if the final audit opens a new source/design question. Stop only when static/source/design questions are exhausted and every remaining unknown is an executable live test.

## Mandatory disputed points

1. **GOST dimension spacing classification**
   - GPT says Arena was wrong to label dimension placement offsets only as policy.
   - Verify GOST 2.307-2011 §5.11/5.12 and GOST R 21.101-2020 §5.4.2.
   - Decide exactly which rules are normative minima vs project/office policy.
   - Reconcile paper-space -> model-space conversion architecture.

2. **Composite in-use detection**
   - GPT says Arena's suggested `GetElementsByType` filter by `compositeId` is impossible in stock Tapir 1.5.9.
   - Verify exact `GetElementsByType` schema/source.
   - Propose the safest stock algorithm or a small dedicated wrapper.

3. **Permanent Morph delete/recreate policy**
   - GPT rejects automatic GUID replacement for permanent/user Morphs unless dependency capture/replay is complete.
   - Enumerate what Archicad relationships can be lost or re-bound on GUID replacement.
   - Decide whether temporary/operator Morphs and permanent Morphs need different policies.

4. **SEO verifier status**
   - Check whether Arena ever promoted `GetCollisions`/built-in Volume beyond what static evidence supports.
   - If semantics for associative SEO remain undocumented, keep them `UNRESOLVED_LIVE_REQUIRED` and preserve `LINK_ONLY` until LT-C1/C2.

5. **Shared asset architecture**
   - Decide whether `.mod`/Hotlink replaces or complements a linked local library.
   - Preserve the user's explicit requirement: add a reusable object/library asset once and have it available in later projects.
   - Separate GSM/library parts, native BIM modules, and Favorites/template assets if appropriate.

6. **`atomic:true` response semantics**
   - Analyze rollback response correctness: GUIDs created earlier in the loop may have been rolled back if the lambda returns an error.
   - Specify the exact response contract so Safe BIM cannot treat rolled-back GUIDs as durable.

7. **Slab bounds crash test policy**
   - Decide whether deliberately reproducing a known process crash is necessary.
   - Prefer version blacklist + positive test on a fixed build if that is sufficient.

8. **Morph topology validator**
   - Verify GPT's criticism of a universal Euler `V-E+F=2(1-g)` acceptance check for disconnected shells/components.
   - Produce a precise validator contract.

9. **Font architecture**
   - Decide whether Favorites alone are sufficient for deterministic creation but insufficient for arbitrary project audit by family name.
   - Clarify role of future `GetFonts/ResolveFontByName`.

## Required output

Create a durable report on a new Arena audit/reconciliation branch, e.g.

`ARENA_RECONCILIATION_GPT_COUNTER_AUDIT_20260928.md`

For each disputed point give:

- GPT claim
- exact evidence
- `ACCEPT / MODIFY / REJECT`
- final reconciled architecture
- remaining live test, if any

Also produce a final consolidated table of all P0/P1/P2 items showing the now-reconciled verdict and whether any live gate remains.

## Handoff

When complete, hand back to GPT through `arena-archicad-project/agent-handoff` with the next turn id, exact branch/commit/report path, and only unresolved live experiments. `requires_codex=false` unless the task explicitly needs code execution beyond static/source audit.

Do not modify `main` merely for signaling.
