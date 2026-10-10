# APA-P20.A02.S03 — saved-copy native readback of 12-element pavilion (operator-provided JSON)

**2026-10-11 evidence publication.** The operator supplied `saved-pavilion-audit-20261010T222136Z.json`. Independently parsed the attachment locally without modifying it or the Archicad project. This report is a **direct transcription and verification of the uploaded API-readback JSON**, not an independent network session on the operator's computer.

## Evidence and integrity

- Raw evidence filename: `saved-pavilion-audit-20261010T222136Z.json` (retained in the conversation upload; NOT committed as a private local-path-bearing file to this public repository).
- Raw UTF-8 JSON size **7,626 bytes**; SHA-256 **`593e637bfe738e5baac979d5cc897f49e1b0d23a4ae431b7f06468c0e829ecd5`**.
- `status=SAVED_COPY_LIVE_READBACK_PASS`, `sceneId=apa-pavilion-live-02`, `sourcePlanHash=28361d6e066364f5c6193404a0f25e395a183729ad44fb1cbe6cb07d2d6bd7dc`.
- API: Archicad 29, Tapir `1.5.10`, port `19724`. `projectName=APA_Pavilion_MVP_SUCCESS`; `projectPath` ends with `Documents\\APA_Pavilion_MVP_SUCCESS.pln`; raw absolute path preserved only in the uploaded JSON. First actual story: `floorId=1`, native `floorIndex=0`.
- `inventoryCount=57`, `verifiedElementCount=12`, `expectedElementCount=12`; the global inventory includes other native/hierarchical elements and **is not required to equal 12**.
- Local integrity check of supplied JSON: all **12 unique GUIDs**, all `PASS`, every `problems=[]`. `writesExecuted=false`, `plnSaveAttempted=false`, `projectStable=true`.
- `diskFile.exists=true`, `diskFile.bytes=15992896`, `diskFile.mtimeUTC=2026-10-10T22:18:08+00:00`. These values were reported by the audit utility, not measured from direct access to the operator's workstation.

## Per-element confirmed readback (from uploaded JSON)

| Step | Native type | GUID | Readback | Relevant measurements |
|---|---|---|---|---|
| wall-south | Wall | `6C6CB42D-8368-4749-81F9-D5FA8748AB20` | PASS | Basic, Z [0,3], bbox XY [300.1,303.9] × [300,300.2] m |
| wall-east | Wall | `BD622995-16E6-4C9B-BF42-4934AD40A931` | PASS | Basic, Z [0,3], bbox XY [303.8,304] × [300.1,302.9] m |
| wall-north | Wall | `1B95F857-025F-457F-A369-E455F33B7861` | PASS | Basic, Z [0,3], bbox XY [300.1,303.9] × [302.8,303] m |
| wall-west | Wall | `79B92DDC-9B38-44F3-9768-0F08CEC0274E` | PASS | Basic, Z [0,3], bbox XY [300,300.2] × [300.1,302.9] m |
| slab | Slab | `7539799C-D432-42F5-9F31-FED10E1047C4` | PASS | Basic, thickness **0.2 m**, level 0, bbox XYZ [300,304] × [300,303] × [-0.200000003,0] m |
| column-sw | Column | `44113E51-830B-404F-910B-3AC34B540820` | PASS | W/D 0.25/0.25, H 3, bbox XY [300.225,300.475] × [300.225,300.475] m |
| column-se | Column | `3BB1F6AD-8BFE-4EEF-9813-C84F58607AED` | PASS | W/D 0.25/0.25, H 3, bbox XY [303.525,303.775] × [300.225,300.475] m |
| column-ne | Column | `C4B4412C-1A4D-41C1-951C-1222EAC7621E` | PASS | W/D 0.25/0.25, H 3, bbox XY [303.525,303.775] × [302.525,302.775] m |
| column-nw | Column | `F3E77518-5BFA-4BBB-87EC-EBD29F428DCB` | PASS | W/D 0.25/0.25, H 3, bbox XY [300.225,300.475] × [302.525,302.775] m |
| door-south | Door | `D0A1D988-7F03-4DA1-AC40-76A3867EDD98` | PASS | W/H 0.9/2.1 m; centerOffset 1.4; sill 0; parent **wall-south** |
| window-north-1 | Window | `C54E2C77-EDF8-4175-B8FA-12BA30A0C595` | PASS | W/H 0.8/1.2; offset 0.9; sill 0.9; parent **wall-north** |
| window-north-2 | Window | `B48FEEB6-DC3D-4181-BD6C-ACDAC708FDA7` | PASS | W/H 0.8/1.2; offset 3.1; sill 0.9; parent **wall-north** |

All twelve records have native story `floorIndex=0`. The four walls, slab and columns report basic building material GUID `922C639B-9875-48DF-A3FC-E0A8AC5F2839`, which is a provisional geometric-MVP selection, **not a certified final construction material**. All geometry numbers above are from source JSON; high-level visual checks are independently recorded in [first live run and screenshots](../2026-10-10/apa-live-user-log-20261010-200512z-pavilion-slab-readback.md).

## Acceptance and boundaries

**Confirmed from the uploaded report:** `SAVED_COPY_LIVE_READBACK_PASS` for **all 12 known GUIDs**, type/floor/geometry/host relationships, and the existence of a local PLN path. The audit performed **zero mutations**. This closes the **read-only API geometry/identity verification gate for the fixed 12-element pavilion**, at evidence level `USER_SUPPLIED_LIVE_API_REPORT_CHECKED`.

**NOT yet established:** evidence that the operator **closed and reopened the saved PLN before this audit**; the audit's own `persistenceNote` explicitly requires operator attestation. Current open-model native API readback, even combined with `diskFile.exists=true`, is **not proof that the model content persisted across a close/reopen**. If the operator attests close/reopen, record as `PERSISTENCE_REOPEN_PASS_REPORTED` (still distinct from independent file-byte inspection). IFC export/structural analysis, normative design, arbitrary-model scalability, and other APA scope are also not verified by this fixed pavilion test.

## Task registry / follow-up

- Related registered task: `APA-P20.A02.S03`, currently `BLOCKED` due to dependencies in `control/PROJECT_PLAN.json` revision 27. This **evidence publication does not change the controller task state**, claim lease, or pretend that all P20 prerequisites are accepted. Controller audit should review and attach evidence using CAS/acceptance rules; avoid a false `DONE_PUBLISHED`.
- Next immediate test: operator attestation of save → full close → reopen; then record explicit persistence result. The separate read-only verifier should remain reusable for new non-mutating tests, but the v1.3/v1.4 one-shot writers **must not** be run again for this scene.
- Further MVP next scope: generalize **typed Basic slab creation** (avoid `CreateSlabs` inheriting an unexpected Composite and 0.3 m), establish attribute provenance and tests on an independently expendable project, and build safe plan-driven native writer; do not assume the fixed pavilion proves general geometry coverage.

**No PLN, APX, main/master, or tested PR branch was modified in preparing this report.**
