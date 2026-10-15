# APA Research OS — synthetic publisher integration smoke

Run ID: APA-RUN-20261010-104437Z-publisher-integration-smoke

This run exercises the automatic inbox-to-immutable-run-to-GitHub-REST-readback-to-receipt pipeline. It is intentionally synthetic. It does not access Archicad, PLN, APX, Tapir, live BIM geometry, or any paid research/model API.

Expected evidence after workflow: GitHub Actions run with success, immutable REPORT.md / manifest.json / evidence.json, generated index entry, publication receipt with report commit SHA and readback_verified=true. A failure must remain a failed workflow rather than a claimed success.

Claim status for this report: REPORTED; technical Archicad findings: NOT_VERIFIED.
