# APA №1 BUILD-01 B1 — 22.10.2026 19Z

Four actual GitHub fetch_pr SOURCE checks. Upstream MIT, 1.7.3 open PR; not installed on local Tapir 1.5.10. Graphisoft DevKit and Archicad LIVE not verified.

- **PR #1352, G4 — Property availability.** Source: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1352 . Contract: includeAvailability=true returns isAvailable; old default false. Decision: SOURCE_ONLY, not BUILD-01 PASS. Assignment №2: №2: separate unavailable from errors.
- **PR #1353, G2 — Library pattern lookup.** Source: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1353 . Contract: SearchLibraryParts ancestorUnId + pattern, max 50, depends #1337. Decision: SOURCE_ONLY, not BUILD-01 PASS. Assignment №2: №2: compare GetAvailableLibraryParts.
- **PR #1357, G2 — Embedded GSM import.** Source: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1357 . Contract: CreateFolderInEmbeddedLibrary/CopyFilesIntoEmbeddedLibrary mutate PLN. Decision: SOURCE_ONLY, not BUILD-01 PASS. Assignment №2: №2: no writes without separate permission.
- **PR #1359, G1 — Export tolerance/Z defaults.** Source: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1359 . Contract: GetExportTolerance.arcTolerance and Get/SetLast3DDefaultLevels. Decision: SOURCE_ONLY, not BUILD-01 PASS. Assignment №2: №2: do not substitute default Z for floor bindings.
