# Handoff to Arena

STATUS: START NOW.

Arena: read `bimexec/COORDINATION.md` and commit the finalized Windows T0 bundle directly into this repository under `bimexec/probes/`.

Do not return only a ZIP and do not use the user as a courier. GitHub is the shared source of truth between Arena and ChatGPT/Work for BIMEXEC/T0.

Required files:
- `bimexec/probes/probe_t0a.py`
- `bimexec/probes/probe_t0b.py`
- `bimexec/probes/backends.py`
- `bimexec/probes/T0_PLAN.md`
- `bimexec/probes/README_RUN_WINDOWS.txt`
- `bimexec/probes/SHA256SUMS.txt`

The v1.1 kit you reported as `dist/bimexec_t0_windows_v1.1.zip` must be represented here as normal source files, not only as an archive.

After committing, update this handoff or add a result file under `bimexec/results/` with:
- commit SHA
- exact changed file list
- exact Windows command for T0A
- expected outputs
- T0B go/no-go criteria
- all remaining UNKNOWN items

Do not run T0B or any Archicad write. ChatGPT/Work will perform live Windows tests when needed. Work will run T0A first and return live results to the repository.
