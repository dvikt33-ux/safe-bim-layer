# GitHub upload — Detail Machine v2.2

This directory contains the systematized active machine state for the construction-detail knowledge base.

- Compact package: `detail-machine-v2.2-systematized.tar.gz`
- Compact package SHA-256: `57edcbfef8f1bf4b9d946e212c7a2c3e0c1a0a12f285e1aa3f974c178dcdf16e`
- Release: `2.2`
- Base repository branch used for integration: `research/library-system-v3`
- Commit policy inside the machine DB remains fail-closed.

The compact package contains the active machine-readable JSON/JSONL state, including:
`details_active_v2.2.jsonl`, `parameter_facts_v2.2.jsonl`, component variants,
source registries, source semantics, assembly grammars, the KAIMAN/KERAKAM v2.2
layers, audit, summary and manifests.

The original FULL release archive is 206,050,133 bytes and exceeds GitHub's
normal 100 MiB single-file limit, so it is intentionally not committed as a
normal Git blob. Its SHA-256 remains recorded in
`archicad_detail_machine_db_v2.2_SHA256.txt`. Source binaries remain outside
this compact Git payload.
