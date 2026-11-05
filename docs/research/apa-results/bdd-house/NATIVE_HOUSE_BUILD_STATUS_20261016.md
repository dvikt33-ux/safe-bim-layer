# BDD house — native construction core, 2026-10-16

## Source and observed baseline

Input is 3_этап_КП_КОМФОРТ_без_замазок.pdf (24-page, 2022 Shchebanovo structural drawings). Do not mix with the 2026 Amur region project (different object).
Archicad 29.2.1 (5101), Tapir 1.5.10, local port 19727, exact source PLN C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln (space before extension).
Live inventory on 2026-10-16: 21 GUIDs (16 Object, 4 Elevation, 1 Wall), zero slabs/roofs/windows/doors.

## Verified vector geometry

All 49 pile circle centres were extracted from vector drawings on PDF page 5; diameter 300 mm, pile nominal length 2400 mm confirmed on PDF page 7. Coordinates in STRUCTURAL_DIGITIZATION_20261016.json.
KR dimension chains X 5.34+1.43+1.93+5.58 = 14.28 m, Y 1.09+8.29 = 9.38 m. General text says 14.18×9.28 m; disagreement retained, structural chains chosen for first-pass geometry with a documented discrepancy.

## Native writer and safety

Script: scripts/apa_bdd_house_native_builder.py. Explicit command allowlist and explicit Archicad port/product verification.
Source PLN is NEVER the active write target. Writes only into a copy named BDD дом - по чертежам 2022.pln in the same folder.
Before writes, checks source PLN path, version/build, Tapir, 21 native GUID baseline and presence of the preexisting isolated wall GUID. Stops if working copy or previous manifest exists.
Copies and SHA256 verifies source on disk; opens only the copy, then creates native elements in stages with GUID diff checks and local append-only JSON journal. Independent GetDetailsOfElements/Get3DBoundingBoxes readback follows before saving the copy.
Report can be uploaded to private GitHub safe-bim-bridge/results via --publish using existing gh authentication.

## First native stage (not the full house)

49 bored pile Columns, provisional-level RC grillage Beams, six exterior frame envelope Walls, 100×200 floor joists on nominal 600 mm pitch, floor layer Slab, two terrace platforms, one provisional pitched Roof.
Not yet encoded: all 23 individual wall elevations, precise internal partitions, windows and doors, individual studs around openings, exact gable/valley roof intersections and full material composite attributes.
Foundation height offsets, detailed joist ends, provisional roofing profile and material defaults have NOT been verified against live native instances. In particular do NOT call this a complete faithful construction model.

## Windows invocation

First save any unsaved original PLN changes before the script opens the new working copy. Do not re-run if a previous working file already exists.

PowerShell:

    $ErrorActionPreference = 'Stop'
    $b = gh api 'repos/dvikt33-ux/safe-bim-layer/contents/scripts/apa_bdd_house_native_builder.py?ref=feature/bdd-house-native-build-20261016' --jq .content
    if ($LASTEXITCODE -ne 0 -or -not $b) { throw 'Builder not available' }
    $p = Join-Path $env:TEMP 'apa_bdd_house_native_builder.py'
    [IO.File]::WriteAllBytes($p,[Convert]::FromBase64String(($b -replace '\s','')))
    $py = "$env:APPDATA\uv\tools\archicad-mcp-server\Scripts\python.exe"
    & $py $p --port 19727 --apply --publish
    if ($LASTEXITCODE -ne 0) { throw 'Builder failed: inspect working PLN and manifest; no blind retry' }

Expected: PREFLIGHT OK, COPY VERIFIED, BUILD progress, NATIVE CORE SAVED, NATIVE READBACK, PRIVATE GITHUB BUILD REPORT.
If native creation fails, open %TEMP%\APA_BDD_House_Construction\house_native_manifest.json and report failures before retrying. Original PLN remains on disk; partial in-memory edits can exist in the working PLN.

## Acceptance

Offline compile/geometry CI passing does NOT prove native creation. Native live verification only after real execution and full GUID/readback evidence. Do not edit main or existing research branches.