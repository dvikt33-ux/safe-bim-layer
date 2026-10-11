# APA live scratch integration — partial slab / no replay

**Status:** USER-REPORTED-LIVE-PARTIAL, NOT LIVE_PASS, NOT VERIFIED COMPLETE.
**Date:** 2026-10-11 (user console).
**Existing work:** [APA-P70.A03.S02](../../control/PROJECT_PLAN.json), [integration PR #34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34).
**Diagnostic script:** [diagnose_apa_partial_scene.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-highlevel-whole-model-20261011/scripts/diagnose_apa_partial_scene.py).

## Native scratch target

- Only user-approved disposable PLN: `C:\LocalAI\APA_Test_House_01.pln`.
- Archicad localhost API port **19726**; Tapir **1.5.10**; Archicad 29 build 5101 RUS.
- First-floor native story 0; second floor native story 1, +3m, unnamed.
- Preflight: `READY_FOR_EXPLICIT_TEST_RUN`; 20 existing project elements inventoried (16 Object, 4 Elevation), no intersects reported by native 3D-bounding-box scanner, `modelWriteAttempts=0`.
- Intent `building-shell-v1`, 25 steps; `intentHash=d0b6c99ad833ccac31c4d53036820b73c7c9f469a05532169b0c059ea30911a0`.
- Preflight approved token `e873cdbc5f6af81e4cfd23fb96ffdf49cdb0b91a8dc90ddc84bdde834dd2a4ad`.

## Run outcome

- Trial journal scene ID: `apa-house-20261011-031123-7181b47c`.
- Evidence directory in user's Windows (not fetched here): `C:\LocalAI\APA_Trial_Evidence\20261011-031123-7181b47c`.
- `status=PARTIAL_OR_UNKNOWN_OUTCOME`, `plnSaved=false`, `modelWriteAttempts=5`.
- **4 Walls created and passed native typed readback:**
  - `s1-wall-south`: `FC37570F-01DF-4B4F-A87D-94F6C2E2983E`
  - `s1-wall-east`: `36A913AF-EBE4-403C-B1B7-A2C5CDB8C4E8`
  - `s1-wall-north`: `CC3B5C2F-0F2B-42CC-A714-CD2F9C926A30`
  - `s1-wall-west`: `25D4C49F-3C47-41F9-9542-39B489E7FD0E`
- `s1-slab` native `CreateSlabs` was called and inventory increased by another GUID `bb516c6f-587b-4f51-afcc-180291542687`, but typed readback returned `ValueError: SLAB_READBACK_MISMATCH`; precise mismatch (thickness/level/polygon semantics) **not determined** yet. Do not mark slab verified based on inventory alone.
- After run: `addedGuids=5`, `removedGuids=[]`, inventory no longer unchanged. Subsequent 20 steps NOT executed.
- No claim that PLN saved or reopened. No retry/replay is permitted for this failed scene; SQLite ledger retained.

## Minimal next steps

1. On local Windows use **read-only** diagnostic script from PR #34 with `--evidence "C:\LocalAI\APA_Trial_Evidence\20261011-031123-7181b47c" --port 19726`; script first proves exact user-approved scratch target and ledger hash, reads native details for the failed slab GUID and compares slab polygon/level/thickness against original plan; no Create, Delete, Modify or Save calls.
2. Preserve current open PLN, journal and evidence directory. **Do not rerun `run_apa_test_house_01.ps1 -Execute`** and do not delete/undo any partial elements until GUID reconciliation and source correction are reviewed.
3. Fix only the demonstrated mismatch in **existing** `archicad_scene_run.py` (or source schema after proof), add regression check with real observed readback, CI, then agree a controlled continuation (not blind full replay) on same or new throwaway file.
4. Attach read-only diagnostic output and changed source SHA to existing P70 task. Keep task status incomplete until actual acceptance.

## Claim scope

This is grounded in **user-pasted terminal logs**; this assistant cannot fetch the Windows SQLite journal or native slab readback directly. The diagnostic outcome remains a blocking unknown. The four walls' `PASS` values come from the live executor results, not independent model inspection.
