# Construction detail machine state v2.3

Focus pass: **FAVORIT «Листовые материалы», section 1, sheets 1.1–1.12 (PDF pages 4–15)**.

## What changed

- Resolved 12 high-priority section-1 catalog transcription tasks.
- Added a source-bound 36-entry component catalog and six facade-subframe system variants.
- Added 24 typed source facts from the manufacturer text/tolerance sheets.
- Added 10 dimensioned component variants without deriving dimensions from raster scale.
- Recorded 14 printed SP/GOST/TU references only as `claimed_by_source_not_independently_verified`.
- Preserved source anomalies instead of silently correcting them, including the paronite 4-size/3-designation mismatch and catalog numbering gap 24–27.

## Active counts

- 1,211 detail units / active IR bindings;
- 1179 parameter facts;
- 546 component variants;
- 598 unresolved queue records.

## Safety

No raster/pixel measurement is treated as construction geometry. Manufacturer technical statements do not become current SP/GOST requirements unless independently verified. New component/catalog records remain `commit_allowed=false`; unresolved project/structural/anchor choices remain fail-closed.