# Restore v2.5 active machine state

`detail-machine-v2.5-systematized.tar.gz` is the compact active-state package for Archicad Detail Machine DB v2.5.

Verify it with `SYSTEMATIZED_ARCHIVE_SHA256.txt`, then extract the archive. The package contains the active detail-unit/IR/fact/variant snapshots and the semantic grammars needed to reconstruct the v2.5 machine state without the raw manufacturer source files.

Raw PDF/DXF/DWG source originals are intentionally not duplicated in normal Git. Their expected hashes and source registry remain in the release metadata; the FULL package is preserved separately.