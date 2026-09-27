# H1 offline execution evidence

Generated on branch `arena/runtime-hardening-v1`, based strictly on
`c55f404829e4e11004ea5c59c8b3aec18b663866`.

These are newly authorised H1 **offline** runs, not re-runs of live T0–T9.
`verification.json` records commands, exit codes, counts, Python version, and
SHA-256 of all 55 Python source files and each output. Hashes allow matching
these results to the containing commit without a self-referential commit SHA.

- test_all: 117 PASS = 93 existing + 24 H1; zero failures.
- H1 separately: 24 PASS.
- v1.3 shim: 5 PASS.
- standalone probe selftests: 62 checks PASS.
- py_compile: 55 files PASS.

No production capability was promoted; no live Archicad or production Router
was accessed. Historical `bimexec/results/` and all B2–B7 runtime code listed
in the manifest are unchanged. See `../../docs/H1_ADAPTER_PARITY.md` for the
precise scope and remaining blockers.
