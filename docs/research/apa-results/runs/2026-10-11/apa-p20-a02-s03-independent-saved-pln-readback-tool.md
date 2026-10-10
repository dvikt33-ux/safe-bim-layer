# APA-P20.A02.S03 — independent saved-PLN readback gate for the first 12-element pavilion

**Date:** 2026-10-11. **Status:** `OFFLINE_TOOL_PASS / USER_LIVE_NOT_RUN`, not `DONE_PUBLISHED` for P20.A02.S03. **Source:** owner-supplied v1.4 console report `COMPLETE_UNSAVED` / `12/12` and screenshots showing `APA_Pavilion_MVP_SUCCESS`. Previous visual and native-output evidence: [prior live run](../2026-10-10/apa-live-user-log-20261010-200512z-pavilion-slab-readback.md).

## Created independently

A **standalone read-only verifier** `APA_Pavilion_Saved_PLN_ReadOnly_Audit_v1.zip` was generated as a ChatGPT downloadable artifact (the ZIP binary is **not** committed to this GitHub repository). It contains:

- `verify_saved_pavilion.py`: Python stdlib-only independent API probe;
- `START_VERIFY_SAVED.cmd`: Windows command-line launcher;
- `test_verify_saved_pavilion.py`: mocked unit tests;
- `README_RU.txt` and `TEST_RESULTS.txt`.

**ZIP:** 10,044 bytes, SHA-256 `61b2dc030fd965d7b74e820c9aaaa565176a7c4aaf63bad131d5555fe43c7742`.  
**Checker script SHA-256:** `faa16911cf4bc985e7c39d3c8f0265d2f706621562dea7efd3093396859d5d38`.  
**Offline tests:** `12/12 PASS`; ZIP CRC `PASS`. These facts do NOT establish live success on the user's Archicad.

## Safety boundaries

- Restrict native calls to **GetProjectInfo, GetAddOnVersion, GetStories, GetAllElements, GetDetailsOfElements, Get3DBoundingBoxes**, using Tapir's JSON API over loopback. **No Create/Modify/Delete/Save calls** or rollback attempts.
- Detect a *single* open `APA_Pavilion_MVP_SUCCESS.pln` on ports 19720–19740 with `Tapir 1.5.10`, `projectName=APA_Pavilion_MVP_SUCCESS`, `isUntitled=false`, `isTeamwork=false`; optionally require exact user path via `--expected-path`. Multiple matching targets block execution.
- Fetch 12 known GUIDs by direct native readback; check their presence in live native inventory without assuming an exact global element count because hierarchical elements may add subelement rows.
- Walls: four exact reference-line axes, 3m height, 0.2m thickness, Basic, Center and native story index 0.
- Slab: 4x3m exterior polygon (rotation and closed-loop tolerant), Basic, 0.2m, top level Z=0, bbox Z=-0.2..0m, and known provisional basic material GUID.
- Columns: four XY origins (0.35m from corners), 0.25x0.25m and 3m tall.
- Windows and door: widths/heights, sill/threshold, center offsets, exact owner Wall GUID. Read bbox and deny missing/malformed bbox for any queried element.
- Re-read current project binding after queries; stop as `BLOCKED_READ_ONLY` if project switched.
- Produce a local JSON report, `SAVED_COPY_LIVE_READBACK_PASS` only when all 12 GUIDs/type/geom/story/host checks pass **and** the saved-path file exists; this is **not** evidence that the human performed close-and-reopen, which must be confirmed separately.
- Never call old v1.3 `menu 5` or v1.4 `recovery menu 2` again. No PLN mutation authorized by this separate audit.

## Reproducibility and next gate

1. Operator saves a separate `APA_Pavilion_MVP_SUCCESS.pln`, closes the model and reopens that **saved copy** in Archicad 29. Do not reopen only the unsaved test `Тест MER .pln`.
2. Double-click `START_VERIFY_SAVED.cmd`; it creates a `results/saved-pavilion-audit-YYYYMMDDTHHMMSSZ.json` next to itself.
3. Attach that report; examine per-element PASS/FAIL, `inventoryCount`, exact project path and `diskFile`. A passing run is an independent API readback of the current saved-copy model.
4. Record operator attestation that close-and-reopen happened. Only then consider disk persistence gate `PASS_REPORTED_WITH_READBACK`. Machine-only proof of on-disk content would need a separate PLN parser or save/reopen control evidence.

**Controller:** canonical `control/PROJECT_PLAN.json` revision 27 currently marks `APA-P20.A02.S03` BLOCKED with unmet P20 dependencies. This documentation does **not** override its status, claim an executor lease, or dispatch a blocked task. Integrate this artifact through the project controller's evidence/task proposal process before any state promotion.

**No main/master, existing tested PR branches, live PLN, or installed APX were modified by this GitHub documentation commit.**
