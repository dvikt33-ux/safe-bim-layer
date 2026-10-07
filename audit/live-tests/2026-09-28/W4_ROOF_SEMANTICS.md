# W4 — Roof semantics (Archicad 29 + Tapir 1.5.9)

Date: 2026-09-28
Target project: `C:\Users\Admin\Downloads\Test_House_WriteSandbox.pln`
Tapir: 1.5.9

## Live results

### A — stock `CreateRoofs` multi-plane roof
- Created GUID: `3E8B5894-9FB2-4EDE-8216-86A24B749580`
- `GetElementsByType(Roof)`: GUID present
- `roofClass`: `MultiPlane`
- `structureType`: `Basic`
- thickness: `0.3 m`
- levels read back: height `0`, angle `0.523598776 rad` (~30°)
- one native Roof GUID, not a collection of SinglePlane roofs

### Per-edge semantics in stock detailed readback
The `GetDetailsOfElements` response for the created MultiPlane roof did not expose:
- `pivotPolyEdges`
- `angleType`
- `Gable`

This is a readback limitation for the tested Tapir 1.5.9 path; it does not prove that Archicad itself lacks those edge semantics.

### B — SinglePlane roof with 0° angle
The live command with `angle=0.0` was accepted and returned a created roof GUID.

Observed:
- `zero_angle.created = true`
- `zero_angle.rejected = false`

This contradicts the earlier expectation derived from a positive-angle schema constraint. Safe BIM must use live behavior as source of truth for this integration: 0° creation is possible in this tested runtime.

## Safety conclusions
1. Stock Tapir can create one native `MultiPlane` Roof element with one GUID.
2. Stock detailed readback is insufficient to verify per-edge Gable/Sloped classification.
3. A 0° SinglePlane roof must not be assumed to be rejected by Tapir 1.5.9.
4. The hard one-GUID gable-roof target still requires explicit edge-semantics support before Safe BIM can claim deterministic gable construction.

No `Modify*`, `Delete*`, or `SaveProject` command was used in W4.
