# Stage 4 performance pass

Baseline: `faf2fd8adcfd3329ae77a137b37f739a9a462225` — verified Stage 4 milestone.

Branch: `work/stage4-performance-pass`.

## Scope

This pass changes evidence-processing performance and observability only. It must not:

- add or change BIM operation types;
- change the proven `CreateWalls` physical mutation path;
- weaken project/model identity binding;
- remove factual read-back;
- weaken stale-plan rejection;
- weaken mutation-attempt durability or the no-blind-retry rule;
- replace independent Audit Pack verification with trust in the build step.

## First optimization

The Stage 4 evidence path previously reparsed the same large factual model snapshot when:

1. generating model summary/index;
2. generating one or more delta pairs;
3. independently verifying the generated Audit Pack.

The first two happened inside the same extraction and were redundant.

The optimized Stage 4 extractor now:

- hashes the exact bytes that are parsed;
- independently rechecks source SHA/size after parsing;
- parses each factual snapshot at most once per extraction;
- retains only snapshots still required by later delta pairs;
- keeps `verify_pack()` as a separate second extraction.

The live finalizer also reuses the already source-pinned `contract.records` SHA/size values for the full-evidence manifest instead of hashing every evidence file again.

## Observability

Live finalization now prints timed phases:

- `collect`;
- `source-contract`;
- `build-pack`;
- `verify-pack`;
- `manifest-and-lfs`;
- total.

The verified Audit Pack receipt also records these timings.

## Required validation

Before this branch can replace the Stage 4 milestone runtime:

1. all Stage 2, Stage 3, Audit Pack, and Stage 4 tests must PASS;
2. a fresh source-pinned offline proof must PASS because implementation fingerprints changed;
3. historical Stage 1 and Stage 3 audit packs must still independently verify;
4. Stage 4 safety semantics must remain unchanged;
5. performance evidence must show the finalizer is faster on a representative retained Stage 4 evidence set.

The verified `faf2fd8` milestone remains the rollback/reference baseline until all five checks pass.
