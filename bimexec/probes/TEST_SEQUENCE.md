# BIMEXEC live test sequence

This file preserves the numbering from `bimexec/docs/audits/BIMEXEC_audit_v1.md`.

Important historical note: `probe_t2_live_v13.py` was created and executed before the audit numbering was re-checked. Its completed live run is the audit **T1** scenario (one wall: create -> marker -> read-back), despite the historical filename containing `t2`.

Do not rename or rewrite its existing evidence: keeping the historical filename preserves traceability.

Canonical sequence from the audit:

- **T0** — dry-run/capability validation.
- **T1** — one wall on an empty area: create -> marker -> read-back. Completed live; historical runner: `probe_t2_live_v13.py`.
- **T2** — four-wall closed contour + T-junction + abutment. Goal: zero false geometry mismatches caused by Archicad joins; otherwise `verify_spec` is not ready (F-9).
- **T3** — dependency package; dependent opening starts only after wall package is COMPLETED and is bound to the correct wall.
- **T4** — timeout after mutation applied -> `PAUSED(OP_UNKNOWN)`, no retry, reconcile offers ADOPT.
- **T5** — process kill between dispatch and verify -> same recovery semantics as T4.
- **T6** — manual geometry drift between operations -> `PAUSED(MODEL_DRIFT)`.
- **T7** — unavailable read-back -> `PAUSED(VERIFY_UNAVAILABLE)`, never continue.

The production Router and `main` remain out of scope for these standalone live probes.
