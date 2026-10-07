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

The Stage 4 model summary also reuses the already-computed per-element `fullElementHash` values from the element index when constructing the whole-model hash. This removes a second full serialization/hash of every BIM element while preserving the exact historical `modelHash` contract.

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


## Measured baseline on retained S4-06 evidence

The first profiled performance-branch verification of the retained LIVE S4-06
Audit Pack remained PASS and reduced wall-clock verification from the historical
~115-118 s baseline to 71.497 s.

Profiler breakdown before timing-only snapshot deduplication:

- records: 128;
- factual snapshots: 10;
- total record bytes: 1948.1 MiB;
- snapshot bytes: 1001.1 MiB;
- extract total: 71.218 s;
- pinned JSON read/parse: 39.250 s;
- model summary/index: 29.483 s;
- changed-path analysis: 0.078 s;
- public scan: 0.259 s;
- pack compare/other: 0.019 s.

This measurement showed that manifest scanning and delta comparison were no
longer material bottlenecks. The next optimization therefore deduplicates
factual snapshots whose source bytes are identical except for the single
top-level nativeSeconds value already excluded by the historical model-hash
contract. Every source file still has to match its individually pinned raw SHA.


## Timing-only snapshot deduplication result

Retained LIVE S4-06 verification remained PASS after timing-only snapshot
deduplication. All focused regression tests passed: 55/55.

Measured profiler result:

- factual snapshots: 10;
- semantic snapshot groups: 3;
- group sizes: 5 / 3 / 2;
- snapshot bytes: 1001.1 MiB;
- extract total: 23.451 s;
- pinned JSON read/parse: 11.555 s;
- model summary/index: 8.815 s;
- changed-path analysis: 0.077 s;
- public scan: 0.258 s;
- pack compare/other: 0.023 s;
- total verifier wall-clock: 23.732 s.

Compared with the historical Stage-4 verifier baseline (~115-118 s), this is
approximately a 4.9x speedup while reproducing the existing S4-06 Audit Pack
byte-for-byte and retaining source SHA verification, semantic-delta verification,
absolute-path scanning and independent verifier extraction.


## Fast historical revalidation

The Stage 4 offline-proof no longer has to semantically re-extract Stage 1 and
Stage 3 on every performance iteration when all accepted anchors are unchanged.

The default path now:

1. requires `scripts/audit_pack.py` to be byte-identical to the VERIFIED
   `faf2fd8` milestone;
2. requires the historical Audit Pack `source.json` and
   `audit-pack-manifest.json` to be byte-identical to that milestone;
3. requires the milestone Stage 4 acceptance report to remain VERIFIED with all
   required criteria PASS;
4. re-hashes every raw source/evidence record referenced by the accepted source
   contract and compares SHA-256 + byte size;
5. re-hashes every compact derived Audit Pack file and checks the exact file set.

Only then is the already-accepted semantic PASS reused. Any mismatch automatically
falls back to the original full historical verifier. Operators can also force
the old behavior with `--full-historical`.

The offline-proof now prints and persists timings for regression tests, each
historical Stage 1/3 check, every offline fixture, and total wall-clock time.


## Final performance-pass acceptance

Status: **PASS / VERIFIED**.

Final operator validation:

- focused performance/Audit Pack regressions: **58/58 PASS**;
- fresh `hardening-offline-010`: **PASS**;
- offline regression tests: **8.343 s**;
- Stage 1 fast historical revalidation: **5.786 s**;
- Stage 3 fast historical revalidation: **5.936 s**;
- all seven Stage 4 offline fixtures: **PASS**, each under 0.6 s;
- total offline proof: **22.367 s**;
- previous full-recompute control run: **195.744 s**.

This is approximately an **8.75x** improvement for the complete Stage 4 offline
proof. The retained LIVE S4-06 Audit Pack verifier remains PASS at **23.732 s**
versus the historical ~115-118 s path, approximately **4.9x faster**.

No new BIM operation type was introduced. The frozen Stage 4 mutation/recovery
semantics remain the rollback and acceptance reference at `faf2fd8`.

Acceptance receipt:
`outputs/closed-loop-stage4/stage4-performance-acceptance.json`.
