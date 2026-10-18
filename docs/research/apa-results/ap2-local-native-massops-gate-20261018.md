# APA AP2: confirmed local source-only run, 18 October 2026

User-returned Windows terminal evidence. This is an installed APA Router run
against the real `2_этап_АП_КОМФОРТ_без_замазок.pdf`, **not** a native model write.

- Source PDF SHA256: `2cf28450e868a5c742511fe40e6d0f061c9210744cb4f43875e0d7839725c55b`
- PDF page 16, clip [125,95,685,595] points, raster 1120x1000 pixels.
- Raster SHA256: `ce664b6ac86d3094ce0a25eb192f21e08bbc0eb9a59874e6dbc16d3302337c19`.
- Read-only PyMuPDF: 1242 PDF paths on "Конструктив - Стены Несущие",
  417 dimensions, 641 axes, 192 zone paths; 19 OCG layer names found.
- APA Router OpenBIMSegments: `APA_SEMANTIC_ROUTED_SOURCE_ONLY_PASS`.
- Pixel classification: background=978395; wall=93184; window=32497; door=15924
  (total 1120000 exactly).
- Repeated mark readback: 22 placements; 9 distinct marks; 6 groups contain
  19 placements; 3 single marks.

| Mark | Source PDF labels |
|---|---:|
| ОК-3 | 6 |
| Д-1 | 4 |
| ОК-2 | 3 |
| ОК-1 | 2 |
| ОК-4 | 2 |
| Д-2 | 2 |
| ДН-1 | 1 |
| ДН-2 | 1 |
| ДШ-1 | 1 |

- Local reports: `C:\Users\Admin\AppData\Local\Temp\APA_AP2_MassOps_20261018-041639-383\plan16\`.
- `nativeCalls=0`, `modelWrites=0`, `readyForModelWrite=false`.
- Native copy count **zero**: successful source analysis is not native copy acceptance.

## Native choice correction

PR #131 / APA V2 explicitly states: independently copying hosted windows and doors
is disallowed until host and owner are source-qualified. Preferred candidates
are now `HOSTED_BATCH_CREATE_IF_QUALIFIED` for recurring marks and
`HOSTED_SINGLE_CREATE_IF_QUALIFIED` for unique ones. PDF text label positions
are **not** opening anchors. Required: verified actual Wall host GUID/story,
rotation/flip, dimensions, library-part/Favorite, host fit, overlap and native
readback in an isolated authorized AP2 PLN. Current BDD structural project
must not be contaminated with this architecturally different building.

Stage 3 mass grouping will instead exercise the already investigated
native multi-element copy/group arrays on frame columns, rafters and trusses,
separately from hosted-window creation.
