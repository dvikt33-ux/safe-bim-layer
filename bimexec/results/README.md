# results/

Live artefacts only. Everything here is produced by a run on a real machine —
never by hand, never from memory, never from documentation.

## Split

| Folder | Holds | Written by |
|---|---|---|
| `bimexec/docs/` | specification, audits, contracts, go/no-go criteria. No live data. | Arena / review |
| `bimexec/results/` | measured output of a real run. | Work/Codex on Windows |

## Expected files

| File | Produced by | Notes |
|---|---|---|
| `WORK_LIVE_BASELINE_2026-09-26.md` | Work/Codex read-only baseline | see `bimexec/HANDOFF_WORK.md` on `main` |
| `GetDetailsOfElements_wall_sample.json` | Work/Codex baseline, and T0A | untouched Tapir response; evidence for wall endpoints |
| `capability_matrix.json` | T0A | commit **only if T0A actually ran** |
| `t0b_report_*.json`, `t0b_receipt_*.json` | T0B | only after explicit T0B authorisation |

Template: `TEMPLATE_T0A_RUN.md`.

## Rules for committing here

1. Never commit a `.pln`, `.pla`, `.bpn`, autosave, log, credential, or personal
   path that should not be public. Strip machine-specific paths to the project
   name if needed.
2. Never edit a result to make it look better. A `NO` is a result.
3. `capability_matrix.json` must validate against
   `bimexec/specs/capability_matrix.schema.json`.
4. A run that ended in `STOP` or `UNKNOWN` is still committed — with the status
   it had, and the receipt.
5. No live artefact is invented to fill a template. If a run did not happen, the
   file does not exist.
