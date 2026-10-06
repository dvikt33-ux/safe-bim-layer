# POROTHERM v2.3 source patch

This directory preserves the POROTHERM/Wienerberger low-rise source-processing delta built on packaged active release `v2.2`.

It does **not** advance `details/ACTIVE_RELEASE` by itself. Merge the delta into the next consolidated machine-state package before changing the active release pointer.

## Contents

- `porotherm-v2.3-source-patch.tar.gz.b64` — base64-encoded gzip tar containing the complete source-specific v2.3 patch.
- `registry_patch_v2.3.json` — source registry/count correction.
- `SHA256SUMS.txt` — checksums for the unpacked patch files.
- `PATCH_ARCHIVE_SHA256.txt` — checksum for the binary tar and encoded transport file.
- `unpack_porotherm_v23_patch.py` — deterministic decoder/verifier/extractor.

## Main correction

The previous generic extraction counted 69 POROTHERM records. Direct source re-indexing establishes 73 canonical technical-detail sheets. Twelve section-divider pages are navigation pages and must not be treated as buildable detail cards. The source contents says section 1 is `1.1–1.4`, but physical page 25 contains real sheet `1.5`; the title block is preserved as the canonical sheet identity.

All generated Archicad operations remain `commit_allowed=false` until sheet-specific printed dimensions and project structural parameters are bound.